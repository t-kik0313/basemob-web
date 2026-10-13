import os
import re

from flask import g, has_request_context, request, url_for
from werkzeug.security import check_password_hash

from firebase_admin import firestore

from webapp.firebase import db
from webapp.schedule_poll import normalize_poll

IDENTITY_FIELDS = (
    'name', 'number', 'no', 'pos1', 'pos2', 'pos3',
    'pitch_bat', 'image_path', 'birth_date', 'player_id',
)
DEFAULT_ABILITY_KINDS = ({'key': 'qual_sayonara', 'label': 'サヨナラ男'},)


class TeamPrefix:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '') or '/'
        parts = path.split('/')
        if len(parts) >= 3 and parts[1] == 't' and parts[2]:
            environ['basemob.team_slug'] = parts[2]
            rest = '/' + '/'.join(parts[3:])
            environ['PATH_INFO'] = rest if rest != '/' else '/'
        return self.app(environ, start_response)


def plain_name(name):
    return str(name or '').replace(' ', '').replace('　', '')


def _load_teams():
    teams = []
    if db is None:
        return teams
    for doc in db.collection('teams').stream():
        data = doc.to_dict() or {}
        kinds = data.get('ability_kinds') or list(DEFAULT_ABILITY_KINDS)
        teams.append({
            'id': doc.id,
            'slug': str(data.get('slug') or doc.id).strip().lower(),
            'name': data.get('name') or doc.id,
            'login_id': str(data.get('login_id') or ''),
            'password_hash': str(data.get('password_hash') or ''),
            'pa_per_game': data.get('paPerGame', 1.8),
            'req_games': data.get('reqGames', 1),
            'req_ab': data.get('reqAb', 2),
            'ability_kinds': [(item.get('key'), item.get('label')) for item in kinds if item.get('key')],
        })
    return teams


def all_teams():
    if has_request_context():
        cached = getattr(g, '_all_teams', None)
        if cached is None:
            cached = _load_teams()
            g._all_teams = cached
        return cached
    return _load_teams()


def team_by_slug(slug):
    key = str(slug or '').strip().lower()
    if not key:
        return None
    for team in all_teams():
        if team['slug'] == key or team['id'].lower() == key:
            return team
    return None


def team_by_id(team_id):
    for team in all_teams():
        if team['id'] == team_id:
            return team
    return None


def current_slug():
    if not has_request_context():
        return None
    return getattr(g, 'team_slug', None) or request.environ.get('basemob.team_slug')


def current_team():
    return team_by_slug(current_slug())


def current_team_id():
    team = current_team()
    return team['id'] if team else None


def _team_document(team_id=None):
    team_id = team_id or current_team_id()
    return db.collection('teams').document(team_id)


def players_ref(team_id=None):
    return _team_document(team_id).collection('players')


def games_ref(team_id=None):
    return _team_document(team_id).collection('games')


def schedule_ref(team_id=None):
    return _team_document(team_id).collection('schedule').document('board')


def password_matches(team, username, password):
    if not team or not team.get('login_id') or not team.get('password_hash'):
        return False
    if username != team['login_id'] or not password:
        return False
    return check_password_hash(team['password_hash'], password)


def pa_per_game():
    team = current_team()
    if not team:
        from webapp.config import REGULATION_PA_COEF
        return REGULATION_PA_COEF
    try:
        return float(team['pa_per_game'])
    except (TypeError, ValueError):
        from webapp.config import REGULATION_PA_COEF
        return REGULATION_PA_COEF


def roster_rows(team_id=None):
    rows = []
    for doc in players_ref(team_id).stream():
        data = doc.to_dict() or {}
        try:
            player_id = int(data.get('player_id') or doc.id)
        except (TypeError, ValueError):
            continue
        number = data.get('number')
        if number is None or str(number).strip() == '':
            number = data.get('no', '')
        rows.append({
            'player_id': player_id,
            'name': data.get('name') or '',
            'no': number,
            'number': number,
            'image_path': data.get('image_path') or 'default.png',
            'pos1': data.get('pos1') or '',
            'pitch_bat': data.get('pitch_bat') or '',
        })
    rows.sort(key=lambda row: _jersey_sort(row['no']))
    return rows


def _jersey_sort(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 999


def next_player_id(team_id=None):
    numbers = [row['player_id'] for row in roster_rows(team_id)]
    return max(numbers) + 1 if numbers else 1


def bind_schedule_people(items, roster):
    by_name = {}
    for player in roster:
        key = plain_name(player.get('name'))
        if key and key not in by_name:
            by_name[key] = player.get('player_id')

    def with_id(name, extra=None):
        record = {'n': name}
        if extra:
            record.update(extra)
        player_id = by_name.get(plain_name(name))
        if player_id:
            record['player_id'] = player_id
        else:
            record.pop('player_id', None)
        return record

    bound = []
    for event in items:
        if not isinstance(event, dict):
            continue
        copied = dict(event)
        lineup = []
        for slot in copied.get('lineup') or []:
            if isinstance(slot, dict):
                row = with_id(slot.get('n') or '', {k: v for k, v in slot.items() if k not in ('n', 'player_id')})
            else:
                row = with_id(str(slot or ''))
            lineup.append(row)
        copied['lineup'] = lineup
        for key in ('attendees', 'absentees'):
            people = []
            for person in copied.get(key) or []:
                name = person.get('n') if isinstance(person, dict) else person
                people.append(with_id(name or ''))
            copied[key] = people
        pendings = []
        for person in copied.get('pendings') or []:
            if isinstance(person, dict):
                pendings.append(with_id(person.get('n') or '', {'d': person.get('d') or ''}))
            else:
                pendings.append(with_id(str(person or ''), {'d': ''}))
        copied['pendings'] = pendings
        bound.append(copied)
    return bound


def public_event(event):
    return {
        'opponent': (event or {}).get('opponent') or '',
        'date': (event or {}).get('date') or '',
        'time': (event or {}).get('timePB') or '',
    }


def read_schedule(team_id=None):
    if db is None:
        return []
    doc = schedule_ref(team_id).get()
    if doc.exists:
        items = (doc.to_dict() or {}).get('items')
        if isinstance(items, list):
            return items
    from webapp.config import BASE_DIR
    path = os.path.join(BASE_DIR, 'schedule_data.csv')
    if not os.path.exists(path):
        return []
    import json
    with open(path, encoding='utf-8') as handle:
        text = handle.read().strip()
    if not text:
        return []
    data = json.loads(text)
    return data if isinstance(data, list) else []


def write_schedule(items, team_id=None):
    schedule_ref(team_id).set({'items': items})


def read_poll(team_id=None):
    if db is None:
        return normalize_poll(None)
    doc = schedule_ref(team_id).get()
    raw = (doc.to_dict() or {}).get('poll') if doc.exists else None
    return normalize_poll(raw)


def update_poll(mutator, team_id=None):
    if db is None:
        raise RuntimeError('schedule store is unavailable')
    ref = schedule_ref(team_id)
    transaction = db.transaction()
    result = {}

    @firestore.transactional
    def _run(transaction):
        snap = ref.get(transaction=transaction)
        raw = snap.to_dict() if snap.exists else {}
        poll = normalize_poll((raw or {}).get('poll'))
        mutator(poll)
        poll = normalize_poll(poll)
        result['poll'] = poll
        transaction.set(ref, {'poll': poll}, merge=True)

    _run(transaction)
    return result['poll']


def load_player_shell(player_id):
    from webapp.stats.json_cache import get_players_data_json

    player = next((row for row in get_players_data_json() if row.get('player_id') == player_id), None)
    stored = {}
    if db is not None and current_team_id():
        doc = players_ref().document(str(player_id)).get()
        if doc.exists:
            stored = doc.to_dict() or {}
    if player is None and not stored:
        return None
    if player is None:
        player = {'player_id': player_id}
    for key in IDENTITY_FIELDS:
        value = stored.get(key)
        if value not in (None, ''):
            player[key] = value
    for key, value in stored.items():
        if key.startswith('plus_') or key.startswith('qual_'):
            player[key] = value
    player['player_id'] = player_id
    player['id'] = player_id
    return player


def install_team_urls(app):
    app.wsgi_app = TeamPrefix(app.wsgi_app)

    def team_url_for(endpoint, **values):
        external = values.get('_external') or values.get('_scheme')
        url = url_for(endpoint, **values)
        if external or endpoint == 'static' or not url.startswith('/') or url.startswith('/static') or url.startswith('/t/'):
            return url
        slug = current_slug()
        if not slug:
            return url
        return f'/t/{slug}{url}'

    app.jinja_env.globals['url_for'] = team_url_for

    @app.context_processor
    def inject_team():
        team = current_team()
        if not team:
            return {
                'team_name': '',
                'team_id': '',
                'schedule_api': '/api/schedule',
                'abilities_api': '/api/update_abilities',
                'score_entry_url': 'https://basemob-207a2.web.app/app.html',
            }
        slug = team['slug']
        return {
            'team_name': team['name'],
            'team_id': team['id'],
            'schedule_api': f'/t/{slug}/api/schedule',
            'abilities_api': f'/t/{slug}/api/update_abilities',
            'score_entry_url': f"https://basemob-207a2.web.app/app.html?team={team['id']}",
        }


def safe_realm(slug):
    cleaned = re.sub(r'[^A-Za-z0-9_-]', '', slug or '')
    return f'team-{cleaned}' if cleaned else 'team'
