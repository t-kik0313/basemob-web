"""運用処理。旧コマンドの入口も維持する。"""
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""Copy 留年 roster fields onto teams/RYUNEN/players and store the schedule.

Does not modify games. Does not import CSV game records.
Takes a local copy first and puts the previous documents back if the check fails.
"""
import json
import os
import pickle
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from webapp.config import BASE_DIR
from webapp.firebase import db, db_old
from webapp.services.player_view import IDENTITY_FIELDS
from webapp.services.schedule_view import bind_schedule_people
from webapp.teams.context import plain_name

TEAM_ID = 'RYUNEN'
LOGIN_ID = 'ryunen'
LOGIN_PASSWORD = 'baseball'


def _present(value):
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == '':
        return False
    return True


def _ability_view(data):
    return {
        key: data.get(key)
        for key in sorted(data)
        if key.startswith('plus_') or key.startswith('qual_')
    }


def _dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def migrate_ryunen():
    if db is None or db_old is None:
        raise SystemExit('Firebase に接続できないため、中止しました。')

    team_ref = db.collection('teams').document(TEAM_ID)
    players = team_ref.collection('players')
    games = team_ref.collection('games')
    schedule = team_ref.collection('schedule').document('board')

    old_docs = list(db_old.collection('players').stream())
    team_docs = list(players.stream())
    game_docs = list(games.stream())
    if len(old_docs) != 16 or len(team_docs) != 16 or len(game_docs) != 10:
        raise SystemExit(
            f'件数が想定と違うため中止しました。旧名簿 {len(old_docs)} / チーム名簿 {len(team_docs)} / 試合 {len(game_docs)}'
        )

    old_by_id = {doc.id: doc.to_dict() or {} for doc in old_docs}
    team_by_id = {doc.id: doc.to_dict() or {} for doc in team_docs}
    game_by_id = {doc.id: doc.to_dict() or {} for doc in game_docs}
    if set(old_by_id) != set(team_by_id):
        raise SystemExit('名簿のIDが一致しないため、中止しました。')

    team_doc = team_ref.get()
    original_team = team_doc.to_dict() or {}
    schedule_doc = schedule.get()
    original_schedule = schedule_doc.to_dict() if schedule_doc.exists else None
    schedule_existed = schedule_doc.exists

    backup_dir = os.path.join(BASE_DIR, 'backups', 'ryunen-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    os.makedirs(backup_dir, exist_ok=True)
    with open(os.path.join(backup_dir, 'before.pkl'), 'wb') as handle:
        pickle.dump({
            'team': original_team,
            'players': team_by_id,
            'games': game_by_id,
            'schedule': original_schedule,
        }, handle)
    print('複製:', backup_dir)

    abilities_before = {doc_id: _ability_view(data) for doc_id, data in team_by_id.items()}
    games_before = {doc_id: _dump(data) for doc_id, data in game_by_id.items()}

    try:
        for doc_id, source in old_by_id.items():
            payload = {}
            for key in IDENTITY_FIELDS:
                if key in source and _present(source.get(key)):
                    payload[key] = source.get(key)
            payload['player_id'] = int(source.get('player_id') or doc_id)
            players.document(doc_id).set(payload, merge=True)

        roster = []
        for doc_id, source in old_by_id.items():
            roster.append({
                'player_id': int(source.get('player_id') or doc_id),
                'name': source.get('name') or '',
            })
        csv_path = os.path.join(BASE_DIR, 'schedule_data.csv')
        if schedule_existed and isinstance((original_schedule or {}).get('items'), list):
            raw_items = original_schedule['items']
        else:
            with open(csv_path, encoding='utf-8') as handle:
                raw_items = json.loads(handle.read() or '[]')
        bound = bind_schedule_people(raw_items, roster)
        schedule.set({'items': bound})

        updates = {'slug': 'ryunen', 'login_id': LOGIN_ID, 'reqGames': 1, 'reqAb': 2}
        if not original_team.get('ability_kinds'):
            updates['ability_kinds'] = [{'key': 'qual_sayonara', 'label': 'サヨナラ男'}]
        if not original_team.get('password_hash'):
            updates['password_hash'] = generate_password_hash(LOGIN_PASSWORD)
        team_ref.set(updates, merge=True)

        after_players = {doc.id: doc.to_dict() or {} for doc in players.stream()}
        after_games = {doc.id: doc.to_dict() or {} for doc in games.stream()}
        after_team = team_ref.get().to_dict() or {}
        problems = []
        if set(after_players) != set(team_by_id):
            problems.append('名簿のIDが変わりました')
        if set(after_games) != set(game_by_id) or len(after_games) != 10:
            problems.append('試合の件数が変わりました')
        for doc_id, before in games_before.items():
            if _dump(after_games.get(doc_id)) != before:
                problems.append(f'試合 {doc_id} の中身が変わりました')
                break
        for doc_id, before in abilities_before.items():
            if _ability_view(after_players.get(doc_id, {})) != before:
                problems.append(f'選手 {doc_id} の能力値が変わりました')
                break
            if not (after_players.get(doc_id) or {}).get('name'):
                problems.append(f'選手 {doc_id} の名前がありません')
                break
        if after_team.get('name') != original_team.get('name'):
            problems.append('チーム名が変わりました')
        if after_team.get('paPerGame') != original_team.get('paPerGame'):
            problems.append('規定打席の係数が変わりました')
        if not check_password_hash(after_team.get('password_hash') or '', LOGIN_PASSWORD):
            problems.append('パスワードを確認できません')
        mapped = 0
        unmatched = []
        for event in bound:
            for slot in event.get('lineup') or []:
                if slot.get('player_id'):
                    mapped += 1
                elif plain_name(slot.get('n')):
                    unmatched.append(slot.get('n'))
        if problems:
            raise RuntimeError(' / '.join(problems))
    except Exception as error:
        print('失敗したので、書き込む前の状態に戻します:', error)
        for doc_id, data in team_by_id.items():
            players.document(doc_id).set(data)
        team_ref.set(original_team)
        if schedule_existed:
            schedule.set(original_schedule)
        else:
            schedule.delete()
        for doc_id, data in game_by_id.items():
            games.document(doc_id).set(data)
        raise SystemExit('元に戻しました。Firestore の試合と名簿は作業前の状態です。')

    print(f'名簿 16人に表示項目を足しました。試合は 10件のままです。')
    print(f'スタメンへ選手IDを付けた枠: {mapped}')
    if unmatched:
        print('名簿と一致しなかった名前:', '、'.join(unmatched))
    print('ログインはチームID ryunen、これまでのパスワードです。')



def main():
    migrate_ryunen()

if __name__ == '__main__':
    main()
