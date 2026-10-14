import math
import pandas as pd
from webapp.utils import calc_t_score, safe_float, safe_int

NON_AB = {'四球', '死球', '犠打', '犠飛', 'BB', 'HBP', 'SH', 'SF', 'B'}
HITS = {'H', '1B', '2B', '3B', 'HR', '単打', '2BH', '3BH', '2塁打', '3塁打', '本塁打'}


def calc_meet_score(avg, pa, regulation_pa, scale_by_pa):
    score = 174.0 * avg + 14.5
    if scale_by_pa:
        if regulation_pa > 0 and pa > 0:
            score *= min(1.0, math.sqrt(pa) / math.sqrt(regulation_pa))
        else:
            score *= 0.5
    return int(max(30, min(100, round(score))))


def season_batting_line(records):
    games = set()
    ab = hits = 0
    for record in records or []:
        games.add((str(record.get('game_date') or ''), str(record.get('game_id') or '')))
        result = str(record.get('result') or '').strip()
        if result in NON_AB:
            continue
        ab += 1
        if result in HITS:
            hits += 1
    return {
        'games': len(games),
        'pa': len(records or []),
        'ab': ab,
        'hits': hits,
        'avg': (hits / ab) if ab else 0.0,
    }


def apply_season_meet(player, records, regulation_pa):
    """6試合以上なら今年度の打率でミートを出す。それ未満は呼び出し元の値（2025年）を残す。"""
    line = season_batting_line(records)
    if line['games'] <= 5:
        return
    plus = safe_int(player.get('plus_meet', 0))
    player['meet_val'] = calc_meet_score(line['avg'], line['pa'], regulation_pa, True) + plus


def current_season_regulation_pa():
    _lines, regulation_pa = load_current_season()
    return regulation_pa


def _plain_name(value):
    return str(value or '').replace(' ', '').replace('　', '')


def _roster_ids(players):
    names = {}
    for row in players or []:
        try:
            pid = int(row.get('player_id'))
        except (TypeError, ValueError):
            continue
        plain = _plain_name(row.get('name'))
        if plain:
            names.setdefault(plain, set()).add(pid)
    return names


def _resolve_player_id(player, roster_names):
    raw_id = player.get('player_id', player.get('id'))
    try:
        return int(float(raw_id))
    except (TypeError, ValueError):
        pass
    plain = _plain_name(player.get('name'))
    if not plain:
        return None
    if plain in roster_names and len(roster_names[plain]) == 1:
        return next(iter(roster_names[plain]))
    found = set()
    for roster_name, ids in roster_names.items():
        if plain in roster_name or roster_name in plain:
            found.update(ids)
    if len(found) == 1:
        return next(iter(found))
    return None


def load_current_season(players=None):
    """今年度の試合ごとの打席から、選手ごとの試合数・打席・打率を集める。"""
    from webapp.teams.context import pa_per_game
    from webapp.services.season_records import PLATE_RESULT_MAP, extend_plate_records, iter_numbered_games

    roster_names = _roster_ids(players)
    buckets = {}
    team_games = 0
    try:
        for number, _doc, g_data in iter_numbered_games():
            if not g_data.get('results'):
                continue
            team_games += 1
            for player in g_data.get('results') or []:
                pid = _resolve_player_id(player, roster_names)
                if pid is None:
                    continue
                extend_plate_records(
                    buckets.setdefault(pid, []),
                    player,
                    g_data,
                    g_data.get('date', ''),
                    number,
                    PLATE_RESULT_MAP,
                )
    except Exception:
        return {}, 0
    lines = {pid: season_batting_line(rows) for pid, rows in buckets.items()}
    regulation_pa = math.ceil(round(team_games * float(pa_per_game()), 6)) if team_games else 0
    return lines, regulation_pa


def ability_power(p_data, box, frames):
    pid = box["pid"]
    avg = box["avg"]
    pa = box["pa"]
    hrs = box["hrs"]
    errors = box["errors"]
    p_games_count = box["p_games_count"]
    record_df = frames["record_df"]
    has_records = frames["has_records"]
    annual_df = frames["annual_df"]
    has_annual = frames["has_annual"]
    regulation_pa = frames["regulation_pa"]
    slg_mean = frames["slg_mean"]
    slg_std = frames["slg_std"]
    run_mean_short = frames["run_mean_short"]
    run_std_short = frames["run_std_short"]
    run_mean_long = frames["run_mean_long"]
    r_row = record_df[record_df['player_id'] == pid] if has_records else pd.DataFrame()
    r_data = r_row.iloc[0].to_dict() if not r_row.empty else {}

    l_row = pd.DataFrame()
    if has_annual and 'player_id' in annual_df.columns:
        player_history = annual_df[annual_df['player_id'] == pid]
        if not player_history.empty:
            if 'year' in player_history.columns:
                l_row = player_history[player_history['year'].astype(str) == '2025']
            if l_row.empty: l_row = player_history.tail(1)

    season = (frames.get('season_by_player') or {}).get(pid) or {}
    if int(season.get('games') or 0) > 5:
        calc_meet = calc_meet_score(season.get('avg') or 0, season.get('pa') or 0, frames.get('season_regulation_pa') or 0, True)
    elif not l_row.empty and 'avg' in l_row.columns:
        l_avg = safe_float(l_row.iloc[0].get('avg'))
        calc_meet = int(max(30, min(100, round(174.0 * l_avg + 14.5)))) if l_avg > 0 else 30
    else:
        calc_meet = calc_meet_score(avg, pa, regulation_pa, True)

    dist = safe_float(r_data.get('batting_distance'))
    if p_games_count > 5:
        if dist > 0: calc_power = int(max(0, min(100, round((min(100, dist) - 20) + (hrs * 2)))))
        else:
            calc_power = 50
            if not l_row.empty and 'slg' in l_row.columns:
                l_slg = safe_float(l_row.iloc[0].get('slg'))
                if slg_std > 0 and l_slg > 0:
                    slg_t_score = calc_t_score(l_slg, slg_mean, slg_std)
                    calc_power = int(max(0, min(100, round(slg_t_score))))
    else:
        if not l_row.empty:
            if dist > 0 and 'hr' in l_row.columns:
                l_hr = safe_int(l_row.iloc[0].get('hr'))
                calc_power = int(max(0, min(100, round((min(100, dist) - 20) + (l_hr * 2)))))
            else:
                calc_power = 50
                if 'slg' in l_row.columns:
                    l_slg = safe_float(l_row.iloc[0].get('slg'))
                    if slg_std > 0 and l_slg > 0:
                        slg_t_score = calc_t_score(l_slg, slg_mean, slg_std)
                        calc_power = int(max(0, min(100, round(slg_t_score))))
        else:
            if dist > 0: calc_power = int(max(0, min(100, round((min(100, dist) - 20) + (hrs * 2)))))
            else: calc_power = 50

    p_data['meet_val'] = calc_meet + p_data['plus_meet']
    p_data['power_val'] = calc_power + p_data['plus_power']

    r_run_short = safe_float(r_data.get('run_short'))
    if r_run_short > 0 and run_std_short > 0:
        t_score = calc_t_score(r_run_short, run_mean_short, run_std_short, invert=True)
        base_speed = int(max(0, min(100, round(t_score + 10 + (t_score - 50) * 0.5))))
    else: base_speed = 50
    p_data['speed_val'] = base_speed + p_data['plus_speed']

    throw_dist = safe_float(r_data.get('throw_distance'))
    base_arm = int(max(0, min(100, math.ceil(throw_dist) - 10))) if throw_dist > 0 else 50
    p_data['arm_val'] = base_arm + p_data['plus_arm']
    p_data['defense_val'] = 50 + p_data['plus_defense']

    pos1 = str(p_data.get('pos1', ''))
    err_mult = 3 if '外野手' in pos1 else 1
    # 年齢ボーナスを外し、純粋に 50 - (エラー数 × 倍率) に変更
    base_catch = int(max(0, min(100, 50 - (errors * err_mult))))
    p_data['catch_val'] = base_catch + p_data['plus_catching']
    box["r_data"] = r_data
    box["r_run_short"] = r_run_short
