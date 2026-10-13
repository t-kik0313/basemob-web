import pandas as pd
from webapp.tenant import pa_per_game
from webapp.data import get_cleaned_df, load_players_df


def prepare_frames():
    players_df = load_players_df()
    if players_df.empty: return None

    game_df = get_cleaned_df('game_records')

    if not game_df.empty:
        if 'game_date' in game_df.columns:
            game_date = game_df['game_date'].astype(str)
            keep = game_date.str.strip() != ''
            game_df = game_df[keep]
            game_date = game_date[keep]
            game_df = game_df[~game_date.str.lower().isin(['nan', 'none', 'nat'])]
        if 'result' in game_df.columns:
            game_df = game_df[game_df['result'].astype(str).str.strip() != '']

        ensure_cols = [
            'game_type', 'batting_order', 'fielding_position', 'direction', 'runner', 
            'strikes', 'is_official', 'is_4th_bat', 'vs_left', 'sayonara', 'result',
            'sb', 'runs', 'rbi', 'errors', 'gidp', 'bases', 'is_hr', 'advancing_runner', 'multi_hit'
        ]
        for c in ensure_cols:
            if c not in game_df.columns: game_df[c] = ''

    record_df = get_cleaned_df('record_meeting')
    annual_df = get_cleaned_df('annual_stats')

    if not annual_df.empty:
        col_map = {}
        for c in annual_df.columns:
            cl = str(c).strip().lower()
            if cl in ['player_id', '選手id', 'id']: col_map[c] = 'player_id'
            elif cl in ['year', '年度', '年']: col_map[c] = 'year'
            elif cl in ['batting_average', 'avg', '打率']: col_map[c] = 'avg'
            elif cl in ['homeruns', 'hr', '本塁打']: col_map[c] = 'hr'
            elif cl in ['slg', '長打率']: col_map[c] = 'slg'
        annual_df.rename(columns=col_map, inplace=True)
        if 'player_id' in annual_df.columns:
            annual_df['player_id'] = pd.to_numeric(annual_df['player_id'], errors='coerce').fillna(-1).astype(int)

    has_records = not record_df.empty
    run_mean_short = run_std_short = run_mean_long = 0
    if has_records:
        record_df['run_short'] = pd.to_numeric(record_df.get('run_short'), errors='coerce')
        valid_run_short = record_df['run_short'].dropna()
        if len(valid_run_short) >= 3:
            run_mean_short, run_std_short = valid_run_short.mean(), valid_run_short.std()

        record_df['run_long'] = pd.to_numeric(record_df.get('run_long'), errors='coerce')
        valid_run_long = record_df['run_long'].dropna()
        if len(valid_run_long) > 0: run_mean_long = valid_run_long.mean()

    has_annual = not annual_df.empty
    slg_mean = slg_std = 0
    if has_annual and 'slg' in annual_df.columns:
        slg_target_df = annual_df[annual_df['year'].astype(str).str.contains('2025', na=False)].copy() if 'year' in annual_df.columns else annual_df.copy()
        slg_target_df['slg'] = pd.to_numeric(slg_target_df['slg'], errors='coerce')
        valid_slg = slg_target_df['slg'].dropna()
        if len(valid_slg) >= 3: slg_mean, slg_std = valid_slg.mean(), valid_slg.std()
        elif len(valid_slg) > 0: slg_mean = valid_slg.mean()

    team_games = game_df['game_id'].nunique() if not game_df.empty and 'game_id' in game_df.columns else 0
    regulation_pa = team_games * pa_per_game() if team_games > 0 else 0
    from webapp.stats.ability_power import load_current_season
    roster = players_df.to_dict(orient='records') if players_df is not None and not players_df.empty else []
    season_by_player, season_regulation_pa = load_current_season(roster)
    return {
        "players_df": players_df,
        "game_df": game_df,
        "record_df": record_df,
        "annual_df": annual_df,
        "has_records": has_records,
        "run_mean_short": run_mean_short,
        "run_std_short": run_std_short,
        "run_mean_long": run_mean_long,
        "has_annual": has_annual,
        "slg_mean": slg_mean,
        "slg_std": slg_std,
        "regulation_pa": regulation_pa,
        "season_by_player": season_by_player,
        "season_regulation_pa": season_regulation_pa,
    }
