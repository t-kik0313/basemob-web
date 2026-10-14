import os
import pandas as pd
from webapp.config import BASE_DIR
from webapp.firebase import db, db_old


OLD_DB_COLLECTIONS = [
    'basic_info', 'players', 'game_records', 'annual_stats',
    'annual_stats_detail', 'record_meeting',
]


def get_cleaned_df(collection_name):
    try:
        records = _load_from_firestore(collection_name)
        if not records:
            print(f"⚠️ 警告: '{collection_name}' のデータは0件でした（空っぽです）")
            return pd.DataFrame()
        return _normalize_dataframe(records)
    except Exception as e:
        from webapp import app
        app.logger.error(f"データ取得エラー ({collection_name}): {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def _load_from_firestore(collection_name):
    records = []
    if collection_name in OLD_DB_COLLECTIONS:
        if db_old is None:
            return records
        print(f"🔄 旧DB(baseball-site)から '{collection_name}' を取得します")
        docs = db_old.collection(collection_name).stream()
    else:
        if db is None:
            return records
        print(f"🔥 新DB(BaseMob)から '{collection_name}' を取得します")
        docs = db.collection(collection_name).stream()
    for doc in docs:
        data = doc.to_dict()
        data['doc_id'] = doc.id
        records.append(data)
    return records


def _normalize_dataframe(records):
    df = pd.DataFrame(records)
    df.columns = df.columns.str.strip()
    col_map = {c: 'player_id' for c in df.columns if str(c).lower() in ['player_id', '選手id', 'id']}
    df.rename(columns=col_map, inplace=True)
    df = df.loc[:, ~df.columns.duplicated()]
    df = df.astype(str).replace(r'\.0$', '', regex=True).replace('nan', '')
    if 'player_id' in df.columns:
        df['player_id'] = pd.to_numeric(df['player_id'], errors='coerce').fillna(0).astype(int)
    return df


def load_players_df():
    df = get_cleaned_df('players')
    if df.empty:
        return df
    df.rename(columns={
        'position_main': 'pos1', 'position_sub1': 'pos2',
        'position_sub2': 'pos3', 'number': 'no',
    }, inplace=True)
    df = df.loc[:, ~df.columns.duplicated()]
    plus_cols = ['plus_meet', 'plus_power', 'plus_speed', 'plus_arm', 'plus_defense', 'plus_catching']
    for col in plus_cols:
        df[col] = pd.to_numeric(df.get(col, 0), errors='coerce').fillna(0).astype(int)
    for col in ['pos1', 'pos2', 'pos3', 'dan', 'injury', 'throw', 'catcher']:
        if col not in df.columns:
            df[col] = "2" if col == "dan" else ("D" if col in ['injury', 'throw', 'catcher'] else "")
    df['pos1'] = df['pos1'].fillna("").astype(str)
    if 'no' not in df.columns:
        df['no'] = df.get('player_id', 0)
    df['number'] = df['no']
    return df


def load_merged_data():
    basic_info = get_cleaned_df('basic_info')
    record_data = get_cleaned_df('record_meeting')
    if not basic_info.empty and not record_data.empty:
        if 'player_id' in basic_info.columns and 'player_id' in record_data.columns:
            return pd.merge(basic_info[['player_id', 'name']], record_data, on='player_id', how='left')
    return pd.DataFrame()
