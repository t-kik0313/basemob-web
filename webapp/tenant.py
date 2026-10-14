"""旧 import パスの互換入口。実装は teams / repositories / services に配置。"""
from webapp.teams.context import plain_name, _load_teams, all_teams, team_by_slug, team_by_id, current_slug, current_team, current_team_id, password_matches, pa_per_game, DEFAULT_ABILITY_KINDS
from webapp.teams.urls import TeamPrefix, install_team_urls, safe_realm
from webapp.repositories.references import _team_document, players_ref, games_ref, schedule_ref
from webapp.repositories.players import roster_rows, _jersey_sort, next_player_id
from webapp.repositories.schedule import read_schedule, write_schedule, read_poll, update_poll
from webapp.services.player_view import load_player_shell, IDENTITY_FIELDS
from webapp.services.schedule_view import bind_schedule_people, public_event
