import logging
import os
from flask import Flask
from webapp.config import BASE_DIR

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'),
)
app.logger.setLevel(logging.DEBUG)

from webapp.auth import register_auth
register_auth(app)

from webapp.routes import (  # noqa: E402,F401
    index_players,
    current_year,
    player_detail,
    records,
    misc,
    games,
    teamstats,
    history,
    pitchers,
    game_detail,
    annual,
    schedule,
    events,
    qualitative_abilities,
    regulation,
    csv_data,
)

from webapp.tenant import install_team_urls  # noqa: E402
install_team_urls(app)
