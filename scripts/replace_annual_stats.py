"""運用処理。旧コマンドの入口も維持する。"""
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import os
from config.paths import IMPORT_DIR, FIREBASE_OLD_KEY

# --- 設定エリア ---
# 鍵ファイルを「メインの鍵」に変更して試してみる
KEY_FILE = str(FIREBASE_OLD_KEY)
COLLECTION_NAME = 'annual_stats'
CSV_FILE = str(IMPORT_DIR / 'annual_stats_input.csv')
# ----------------

def upload_csv_to_firebase():
    if not os.path.exists(KEY_FILE):
        print(f"❌ エラー: 鍵ファイル '{KEY_FILE}' が見つかりません。")
        return
    if not os.path.exists(CSV_FILE):
        print(f"❌ エラー: CSVファイル '{CSV_FILE}' が見つかりません。")
        return

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(KEY_FILE)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
    except Exception as e:
        print(f"❌ Firebase初期化エラー: {e}")
        return

    print(f"📖 CSVファイルを読み込んでいます: {CSV_FILE}")
    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
        df = df.fillna("") # 空セルを完全に空文字化
        records = df.to_dict(orient='records')
    except Exception as e:
        print(f"❌ CSV読み込みエラー: {e}")
        return

    # 🌟 必殺技：既存の古いデータをすべて削除して大掃除する！
    print(f"🧹 既存の '{COLLECTION_NAME}' データをリセット中...")
    try:
        docs = db.collection(COLLECTION_NAME).stream()
        delete_batch = db.batch()
        delete_count = 0
        for doc in docs:
            delete_batch.delete(doc.reference)
            delete_count += 1
            if delete_count % 500 == 0:
                delete_batch.commit()
                delete_batch = db.batch()
        delete_batch.commit()
        print(f"🧹 {delete_count} 件の古いデータを削除しました！")
    except Exception as e:
        print(f"⚠️ データ削除中にエラー: {e}")

    # 🌟 新しいデータを綺麗なIDで登録し直す
    print(f"🚀 新しいデータを {len(records)} 件書き込み中...")
    batch = db.batch()
    count = 0

    for record in records:
        pid = record.get('player_id')
        year = record.get('year')

        if pid == "" or year == "":
            continue # 空の行はスキップ

        try:
            # Pandas特有の「11.0」を「11」に直すための安全処理
            clean_pid = int(float(pid))
            clean_year = int(float(year))
            doc_id = f"{clean_pid}_{clean_year}"
        except:
            # 万が一数字にできない場合はFirebaseにおまかせ
            doc_id = db.collection(COLLECTION_NAME).document().id

        doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
        batch.set(doc_ref, record)

        count += 1
        if count % 500 == 0:
            batch.commit()
            batch = db.batch()

    batch.commit()
    print(f"✅ 完了！ {count} 件のデータを新しくアップロードし直しました。")


def main():
    upload_csv_to_firebase()

if __name__ == '__main__':
    main()
