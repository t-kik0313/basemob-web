from webapp.presentation import page_route, screen_response
from webapp import app
from webapp.repositories.references import players_ref
from webapp.data import load_merged_data
from webapp.stats.json_cache import get_players_data_json

@page_route('/pawapuro')
def pawapuro():
    from webapp.services.season_records import collect_season
    from webapp.routes.qualitative_abilities import flag_on
    from webapp.stats.ability_ranks import apply_meeting_run_rank, apply_plate_abilities, apply_steal_rank

    from webapp.stats.ability_power import apply_season_meet, current_season_regulation_pa
    players_data = get_players_data_json()
    regulation_pa = current_season_regulation_pa()
    meeting = load_merged_data()
    meeting_rows = [] if meeting.empty else meeting.to_dict(orient='records')
    qualitative = {}
    try:
        for doc in players_ref().stream():
            qualitative[str(doc.id)] = flag_on((doc.to_dict() or {}).get('qual_sayonara'))
    except Exception as error:
        print(f"⚠️ 定性特殊能力の読み込みエラー: {error}")
    for player in players_data:
        name = str(player.get('name', '')).replace(" ", "").replace("　", "")
        plate_records, stolen_bases = collect_season(name, player.get('player_id'))
        apply_season_meet(player, plate_records, regulation_pa)
        apply_plate_abilities(player, plate_records)
        apply_steal_rank(player, stolen_bases)
        apply_meeting_run_rank(player, meeting_rows)
        player['t_sayonara'] = qualitative.get(str(player.get('player_id')), False)
    return screen_response('pawapuro.html', players_data=players_data)
