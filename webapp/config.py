import logging
from config.paths import ROOT_DIR, CACHE_DIR, LOG_DIR

BASE_DIR = str(ROOT_DIR)
JSON_PLAYERS = str(CACHE_DIR / 'players_data.json')
LOG_FILE = str(LOG_DIR / 'debug_log.txt')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

REGULATION_PA_COEF = 1.8
USER_ID = "ryunen"
PASSWORD = "baseball"
SECRET_KEY = "ryunen-busters-login"
LOGIN_DAYS = 30
TEAM_ID = "RYUNEN"

REQ_GAMES = 1
REQ_AB = 2

logging.basicConfig(
    level=logging.DEBUG,
    filename=LOG_FILE,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
)
