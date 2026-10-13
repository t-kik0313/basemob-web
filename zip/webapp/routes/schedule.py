import traceback

from flask import g, jsonify, render_template, request

from webapp import app
from webapp.routes.player_detail_form import build_form_summary
from webapp.routes.player_detail_records import collect_detail_records
from webapp.schedule_poll import (
    PollError,
    apply_add,
    apply_answer,
    apply_game,
    apply_remove,
    japan_today,
)
from webapp.tenant import plain_name, read_poll, roster_rows, update_poll

CONDITION_LABELS = ('絶好調', '好調', '普通', '不調', '絶不調')


def _roster_conditions(players):
    from webapp.tenant import games_ref

    conditions = {}
    try:
        games = list(games_ref().order_by('date').get())
    except Exception:
        traceback.print_exc()
        return conditions
    for player in players:
        name = player.get('name', '')
        records, *_rest = collect_detail_records(plain_name(name), str(player.get('player_id', '')), games)
        text = build_form_summary(records, 0, 0).get('condition_text')
        conditions[name] = text if text in CONDITION_LABELS else '普通'
    return conditions


def _roster_ids(rows):
    return {int(row['player_id']) for row in rows}


def _names(rows):
    by_name = {}
    for row in rows:
        key = plain_name(row.get('name'))
        if key and key not in by_name:
            by_name[key] = row.get('player_id')
    return by_name


@app.route('/api/schedule', methods=['GET'])
def api_schedule():
    try:
        poll = read_poll()
    except Exception:
        traceback.print_exc()
        return jsonify({'error': '読み込めませんでした。'}), 500
    return jsonify(poll)


@app.route('/api/schedule/poll', methods=['POST'])
def api_schedule_poll():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': '形式が違います。'}), 400
    action = data.get('action')
    today = japan_today()
    try:
        rows = roster_rows()

        def mutate(poll):
            if action == 'answer':
                try:
                    player_id = int(data.get('player_id'))
                except (TypeError, ValueError):
                    raise PollError('選手が見つかりません。')
                apply_answer(poll, _roster_ids(rows), player_id, data.get('answers'), today)
            elif action == 'add':
                apply_add(poll, data.get('iso'), bool(data.get('routine')), today)
            elif action == 'remove':
                apply_remove(poll, data.get('iso'), today)
            elif action == 'game':
                apply_game(poll, data.get('iso'), data.get('game'), _names(rows), today)
            else:
                raise PollError('形式が違います。')

        poll = update_poll(mutate)
    except PollError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception:
        traceback.print_exc()
        return jsonify({'error': '保存に失敗しました。'}), 500
    return jsonify(poll)


@app.route('/schedule')
def schedule():
    public = bool(getattr(g, 'public_view', False))
    rows = roster_rows()
    roster = [
        {'player_id': row['player_id'], 'name': row['name']}
        for row in rows
        if row.get('name')
    ]
    conditions = _roster_conditions(rows)
    return render_template(
        'schedule.html',
        logged_in=not public,
        roster=roster,
        conditions=conditions,
    )
