import math
import pandas as pd
from webapp.utils import calc_t_score, safe_float, safe_int


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

    dist = safe_float(r_data.get('batting_distance'))
    if p_games_count > 5:
        meet_base = 174.0 * avg + 14.5
        meet_correction = (math.sqrt(pa) / math.sqrt(regulation_pa)) if regulation_pa > 0 and pa > 0 else 0.5
        calc_meet = int(max(30, min(100, round(meet_base * min(1.0, meet_correction))))) 
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
            if 'avg' in l_row.columns:
                l_avg = safe_float(l_row.iloc[0].get('avg'))
                calc_meet = int(max(30, min(100, round(174.0 * l_avg + 14.5)))) if l_avg > 0 else 30
            else: calc_meet = 30

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
            meet_base = 174.0 * avg + 14.5
            meet_correction = (math.sqrt(pa) / math.sqrt(regulation_pa)) if regulation_pa > 0 and pa > 0 else 0.5
            calc_meet = int(max(30, min(100, round(meet_base * min(1.0, meet_correction))))) 
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
