"""旧 tenant.py の処理を役割別に分割。"""
from webapp.firebase import db
from webapp.teams.context import current_team_id


def _team_document(team_id=None):
    team_id = team_id or current_team_id()
    return db.collection('teams').document(team_id)



def players_ref(team_id=None):
    return _team_document(team_id).collection('players')



def games_ref(team_id=None):
    return _team_document(team_id).collection('games')



def schedule_ref(team_id=None):
    return _team_document(team_id).collection('schedule').document('board')
