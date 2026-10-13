import traceback

from flask import g, jsonify, render_template, request

from webapp import app
from webapp.schedule_poll import (
    PollError,
    apply_event_answer,
    apply_event_confirm,
    apply_event_delete,
    apply_event_member_answer,
    apply_event_people,
    apply_event_put,
    event_people_view,
    japan_today,
)
from webapp.tenant import plain_name, read_poll, roster_rows, update_poll


def _roster_ids(rows):
    return {int(row['player_id']) for row in rows}


def _names(rows):
    by_name = {}
    for row in rows:
        key = plain_name(row.get('name'))
        if key and key not in by_name:
            by_name[key] = row.get('player_id')
    return by_name


def _member_required():
    if getattr(g, 'public_view', False):
        raise PollError('ログインが必要です。')


def _events_payload(poll, rows):
    people, custom = event_people_view(poll, rows)
    return {
        'events': poll.get('events') or {},
        'people': people,
        'peopleCustom': custom,
    }


@app.route('/api/events', methods=['GET'])
def api_events():
    try:
        poll = read_poll()
        rows = roster_rows()
    except Exception:
        traceback.print_exc()
        return jsonify({'error': '読み込めませんでした。'}), 500
    return jsonify(_events_payload(poll, rows))


@app.route('/api/events', methods=['POST'])
def api_events_post():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': '形式が違います。'}), 400
    action = data.get('action')
    today = japan_today()
    try:
        rows = roster_rows()

        def mutate(poll):
            if action == 'answer':
                person_id = data.get('person_id')
                if person_id not in (None, ''):
                    apply_event_member_answer(
                        poll,
                        data.get('id'),
                        person_id,
                        data.get('answers'),
                        _roster_ids(rows),
                    )
                else:
                    raw_id = data.get('player_id')
                    if raw_id in (None, ''):
                        player_id = None
                    else:
                        try:
                            player_id = int(raw_id)
                        except (TypeError, ValueError):
                            raise PollError('選手が見つかりません。')
                    apply_event_answer(
                        poll,
                        data.get('id'),
                        player_id,
                        data.get('name'),
                        data.get('answers'),
                        _roster_ids(rows),
                        _names(rows),
                    )
            elif action == 'create':
                _member_required()
                apply_event_put(poll, '', data.get('event'), today)
            elif action == 'update':
                _member_required()
                apply_event_put(poll, data.get('id'), data.get('event'), today)
            elif action == 'confirm':
                _member_required()
                apply_event_confirm(poll, data.get('id'))
            elif action == 'delete':
                _member_required()
                apply_event_delete(poll, data.get('id'))
            elif action == 'people':
                _member_required()
                apply_event_people(poll, data.get('people'), rows)
            else:
                raise PollError('形式が違います。')

        poll = update_poll(mutate)
    except PollError as exc:
        code = 401 if str(exc) == 'ログインが必要です。' else 400
        return jsonify({'error': str(exc)}), code
    except Exception:
        traceback.print_exc()
        return jsonify({'error': '保存に失敗しました。'}), 500
    return jsonify(_events_payload(poll, rows))


@app.route('/events')
def events():
    public = bool(getattr(g, 'public_view', False))
    rows = roster_rows()
    roster = [
        {'player_id': row['player_id'], 'name': row['name']}
        for row in rows
        if row.get('name')
    ]
    return render_template('events.html', logged_in=not public, roster=roster)
