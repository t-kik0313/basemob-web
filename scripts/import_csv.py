"""運用処理。旧コマンドの入口も維持する。"""
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import os
import math
from config.paths import IMPORT_DIR, FIREBASE_KEY

# Firebase接続
try:
    cred = credentials.Certificate(str(FIREBASE_KEY))
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Firebase接続エラー: {e}")
    exit()

def upload_csv_to_firestore(csv_filename, collection_name, id_col=None):
    csv_path = str(IMPORT_DIR / csv_filename)
    if not os.path.exists(csv_path):
        print(f"⏭️ スキップ: {csv_filename} が見つかりません。")
        return

    df = pd.read_csv(csv_path, encoding='utf-8')
    df = df.fillna("") # 空白データを処理
    records = df.to_dict(orient='records')

    batch = db.batch()
    col_ref = db.collection(collection_name)

    count = 0
    for record in records:
        clean_record = {}
        for k, v in record.items():
            if isinstance(v, float) and math.isnan(v):
                clean_record[k] = ""
            else:
                clean_record[k] = v

        # IDの指定があればそれを使い、なければ自動IDを割り当て
        if id_col and id_col in clean_record and str(clean_record[id_col]) != "":
            doc_ref = col_ref.document(str(clean_record[id_col]))
        else:
            doc_ref = col_ref.document()

        batch.set(doc_ref, clean_record)
        count += 1

        # 500件ごとの制限対策
        if count % 400 == 0:
            batch.commit()
            batch = db.batch()

    if count % 400 != 0:
        batch.commit()
    print(f"✅ {csv_filename} のデータを '{collection_name}' にアップロードしました！({count}件)")

print("🚀 データのお引越しを開始します...")

# 各CSVデータをそれぞれ別のコレクション（フォルダ）へ
upload_csv_to_firestore('basic_info_input.csv', 'basic_info', 'player_id')
upload_csv_to_firestore('game_records.csv', 'game_records')
upload_csv_to_firestore('annual_stats_input.csv', 'annual_stats')
upload_csv_to_firestore('record_meeting_data.csv', 'record_meeting', 'player_id')

print("🎉 すべてのお引越しが完了しました！")
