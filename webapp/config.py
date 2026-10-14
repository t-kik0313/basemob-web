import os
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PLAYERS = os.path.join(BASE_DIR, 'players_data.json')
LOG_FILE = os.path.join(BASE_DIR, 'debug_log.txt')

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
