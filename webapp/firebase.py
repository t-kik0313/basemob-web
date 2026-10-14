import os
import firebase_admin
from firebase_admin import credentials, firestore
from webapp.config import BASE_DIR

db = None
db_old = None

try:
    cred_basemob = credentials.Certificate(os.path.join(BASE_DIR, 'firebase_key.json'))
    firebase_admin.initialize_app(cred_basemob)
    db = firestore.client()

    cred_baseball = credentials.Certificate(os.path.join(BASE_DIR, 'firebase_key_notuse.json'))
    app_baseball = firebase_admin.initialize_app(cred_baseball, name='baseball_site')
    db_old = firestore.client(app=app_baseball)
    print("🔥 Firebase二刀流モード（BaseMob & 旧DB）で起動しました！")
except Exception as e:
    print(f"⚠️ Firebase接続エラー: {e}")
    db = None
    db_old = None


def team_games():
    from webapp.repositories.references import games_ref
    return games_ref()
