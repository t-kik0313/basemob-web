"""サイト所有者だけが実行する。既存チームの文書は変更しない。"""
import sys

from werkzeug.security import generate_password_hash

from webapp.firebase import db


def create_team(team_id, name, login_id, password):
    team_id = str(team_id or '').strip()
    name = str(name or '').strip()
    login_id = str(login_id or '').strip()
    password = str(password or '')
    if not team_id or not name or not login_id or not password:
        raise SystemExit('チームID、表示名、ログインID、パスワードをすべて指定してください。')
    if db is None:
        raise SystemExit('Firebase に接続できないため、中止しました。')

    existing = {doc.id: (doc.to_dict() or {}).get('login_id') for doc in db.collection('teams').stream()}
    if team_id in existing:
        raise SystemExit(f'{team_id} は既にあるため、作成しませんでした。')
    if login_id in {value for value in existing.values() if value}:
        raise SystemExit('そのログインIDは別のチームが使っているため、作成しませんでした。')

    db.collection('teams').document(team_id).set({
        'name': name,
        'slug': team_id.lower(),
        'login_id': login_id,
        'password_hash': generate_password_hash(password),
        'paPerGame': 1.8,
        'reqGames': 1,
        'reqAb': 2,
        'ability_kinds': [{'key': 'qual_sayonara', 'label': 'サヨナラ男'}],
    })
    print(f'{team_id} を作成しました。開くアドレスは /t/{team_id.lower()}/players です。')


if __name__ == '__main__':
    if len(sys.argv) != 5:
        raise SystemExit('使い方: py -m webapp.create_team チームID 表示名 ログインID パスワード')
    create_team(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
