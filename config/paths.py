"""アプリと運用スクリプトが共有する、作業ディレクトリに依存しないパス。"""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
IMPORT_DIR = ROOT_DIR / 'data' / 'imports'
REFERENCE_DIR = ROOT_DIR / 'data' / 'reference'
CACHE_DIR = ROOT_DIR / 'var' / 'cache'
LOG_DIR = ROOT_DIR / 'var' / 'log'
CREDENTIALS_DIR = ROOT_DIR / 'config' / 'credentials'
FIREBASE_KEY = CREDENTIALS_DIR / 'firebase_key.json'
FIREBASE_OLD_KEY = CREDENTIALS_DIR / 'firebase_key_notuse.json'
SCHEDULE_FILE = REFERENCE_DIR / 'schedule_data.csv'
