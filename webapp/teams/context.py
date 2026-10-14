"""旧 tenant.py の処理を役割別に分割。"""
from flask import g, has_request_context, request
from werkzeug.security import check_password_hash
from webapp.firebase import db

DEFAULT_ABILITY_KINDS = ({'key': 'qual_sayonara', 'label': 'サヨナラ男'},)


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
