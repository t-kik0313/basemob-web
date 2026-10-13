import pandas as pd
from webapp.utils import safe_div


def batting_splits(p_data, box):
    pdf = box["pdf"]
    ab_results = box["ab_results"]

    def calc_split_stats(mask):
        if mask is None or not mask.any():
            return 0, 0, 0.0
        t_ab = int((mask & is_ab).sum())
        t_hits = int((mask & is_hit).sum())
        return t_ab, t_hits, safe_div(t_hits, t_ab)

    if pdf.empty:
        direction = runner = order = position = None
        is_ab = is_hit = None
    else:
        direction = pdf['direction'].astype(str)
        runner = pdf['runner'].astype(str)
        order = pdf['batting_order'].astype(str)
        position = pdf['fielding_position'].astype(str)
        is_ab = pdf['result'].isin(ab_results)
        is_hit = pdf['calc_bases'] > 0

    def subset(series_mask):
        return None if pdf.empty else series_mask

    left_dirs = ['5', '6', '7']
    center_dirs = ['1', '2', '8']
    right_dirs = ['3', '4', '9']

    l_ab, l_hits, l_avg = calc_split_stats(subset(direction.isin(left_dirs) if direction is not None else None))
    c_ab, c_hits, c_avg = calc_split_stats(subset(direction.isin(center_dirs) if direction is not None else None))
    r_ab, r_hits, r_avg = calc_split_stats(subset(direction.isin(right_dirs) if direction is not None else None))

    p_data.update({
        'dir_left_ab': int(l_ab), 'dir_left_hits': int(l_hits), 'dir_left_avg': float(l_avg),
        'dir_center_ab': int(c_ab), 'dir_center_hits': int(c_hits), 'dir_center_avg': float(c_avg),
        'dir_right_ab': int(r_ab), 'dir_right_hits': int(r_hits), 'dir_right_avg': float(r_avg),
    })

    runner_cases = ['0', '1', '2', '3', '1.2', '1.3', '2.3', 'F']
    for r_case in runner_cases:
        c_ab, c_hits, c_avg = calc_split_stats(subset(runner == r_case if runner is not None else None))
        safe_key = r_case.replace('.', '_')
        p_data[f'runner_{safe_key}_ab'] = int(c_ab)
        p_data[f'runner_{safe_key}_hits'] = int(c_hits)
        p_data[f'runner_{safe_key}_avg'] = float(c_avg)

    order_stats = {}
    for batting_order in ['1','2','3','4','5','6','7','8','9','sub']:
        o_ab, o_hits, o_avg = calc_split_stats(subset(order == batting_order if order is not None else None))
        if o_ab > 0: order_stats[batting_order] = {'ab': int(o_ab), 'hits': int(o_hits), 'avg': float(o_avg)}
    p_data['order_stats'] = order_stats

    pos_stats = {}
    for pos in ['1','2','3','4','5','6','7','8','9','DH','PH','PR']:
        p_ab, p_hits, p_avg = calc_split_stats(subset(position == pos if position is not None else None))
        if p_ab > 0: pos_stats[pos] = {'ab': int(p_ab), 'hits': int(p_hits), 'avg': float(p_avg)}
    p_data['pos_stats'] = pos_stats

    is_left_batter = '左打' in str(p_data['pitch_bat'])
    pull_avg = r_avg if is_left_batter else l_avg
    push_avg = l_avg if is_left_batter else r_avg

    _, _, zeroStrikeAvg = calc_split_stats(subset(pdf['strikes'] == '0') if not pdf.empty else None)
    _, _, twoStrikeAvg = calc_split_stats(subset(pdf['strikes'] == '2') if not pdf.empty else None)

    if pdf.empty:
        off_mask = None
    else:
        off_mask = (pdf['game_type'] == 'official') | (pdf['is_official'].astype(str) == '1')
    _, _, officialAvg = calc_split_stats(off_mask)

    risp_runners = ['2', '3', '1.2', '1.3', '2.3', 'F']
    risp_ab, risp_hits, risp_avg = calc_split_stats(subset(runner.isin(risp_runners) if runner is not None else None))

    left_ab, left_hits, left_avg = calc_split_stats(subset(pdf['vs_left'].astype(str) == '1') if not pdf.empty else None)
    if pdf.empty:
        bat4_mask = None
    else:
        bat4_mask = (pdf['is_4th_bat'].astype(str) == '1') | (order == '4')
    bat4_ab, bat4_hits, bat4_avg = calc_split_stats(bat4_mask)

    infield_dirs = ['1', '2', '3', '4', '5', '6']
    _, infield_hits, _ = calc_split_stats(subset(direction.isin(infield_dirs) if direction is not None else None))
    sayonara_hits = int((is_hit & (pdf['sayonara'].astype(str) == '1')).sum()) if not pdf.empty else 0

    hit_df = pdf[pdf['calc_bases'] > 0] if not pdf.empty else pd.DataFrame()
    if not hit_df.empty and 'game_date' in hit_df.columns and 'game_id' in hit_df.columns:
        hit_counts = hit_df.groupby(['game_date', 'game_id']).size()
        games_with_hits = len(hit_counts)
        games_with_multi_hits = len(hit_counts[hit_counts >= 2])
    else: games_with_hits = games_with_multi_hits = 0
    box["pull_avg"] = pull_avg
    box["push_avg"] = push_avg
    box["zeroStrikeAvg"] = zeroStrikeAvg
    box["twoStrikeAvg"] = twoStrikeAvg
    box["officialAvg"] = officialAvg
    box["risp_avg"] = risp_avg
    box["left_ab"] = left_ab
    box["left_avg"] = left_avg
    box["bat4_avg"] = bat4_avg
    box["infield_hits"] = infield_hits
    box["sayonara_hits"] = sayonara_hits
    box["games_with_hits"] = games_with_hits
    box["games_with_multi_hits"] = games_with_multi_hits
