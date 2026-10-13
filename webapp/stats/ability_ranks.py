def ability_ranks(p_data, box, frames):
    ab = box["ab"]
    avg = box["avg"]
    sb = box["sb"]
    sh = box["sh"]
    hits = box["hits"]
    pa = box["pa"]
    hrs = box["hrs"]
    bb = box["bb"]
    so = box["so"]
    slg = box["slg"]
    obp = box["obp"]
    runs = box["runs"]
    rbi = box["rbi"]
    errors = box["errors"]
    gidp = box["gidp"]
    sf = box["sf"]
    p_games_count = box["p_games_count"]
    risp_avg = box["risp_avg"]
    left_ab = box["left_ab"]
    left_avg = box["left_avg"]
    pull_avg = box["pull_avg"]
    push_avg = box["push_avg"]
    zeroStrikeAvg = box["zeroStrikeAvg"]
    twoStrikeAvg = box["twoStrikeAvg"]
    officialAvg = box["officialAvg"]
    bat4_avg = box["bat4_avg"]
    infield_hits = box["infield_hits"]
    sayonara_hits = box["sayonara_hits"]
    games_with_hits = box["games_with_hits"]
    games_with_multi_hits = box["games_with_multi_hits"]
    r_data = box["r_data"]
    r_run_short = box["r_run_short"]
    run_mean_long = frames["run_mean_long"]
    def eval_rank(diff):
        if diff >= 0.250: return 'A'
        if diff >= 0.150: return 'B'
        if diff >= 0.050: return 'C'
        if diff >= -0.050: return 'D'
        if diff >= -0.150: return 'E'
        if diff >= -0.250: return 'F'
        return 'G'

    if ab < 15:
        p_data['chance_rank'] = p_data['left_rank'] = 'D'
    else:
        p_data['chance_rank'] = eval_rank(risp_avg - avg)
        left_diff = left_avg - avg
        if left_ab < 10: left_diff = left_diff * (left_ab / 10.0)
        p_data['left_rank'] = eval_rank(left_diff)

    if sb >= 8: p_data['steal_rank'] = 'A'
    elif sb >= 5: p_data['steal_rank'] = 'B'
    elif sb >= 2: p_data['steal_rank'] = 'C'
    else: p_data['steal_rank'] = 'D'

    r_run_long = safe_float(r_data.get('run_long'))
    if r_run_long > 0 and r_run_short > 0 and run_mean_long > 0:
        run_val = (run_mean_long - r_run_long) * ((r_run_short * 4) - r_run_long)
        if run_val >= 0.55: p_data['run_rank'] = 'A'
        elif run_val >= 0.35: p_data['run_rank'] = 'B'
        elif run_val >= 0.10: p_data['run_rank'] = 'C'
        elif run_val >= 0.00: p_data['run_rank'] = 'D'
        elif run_val >= -0.40: p_data['run_rank'] = 'E'
        else: p_data['run_rank'] = 'F'
    else: p_data['run_rank'] = 'D'

    if ab >= 15:
        p_data['t_koukaku'] = (pull_avg >= 0.300 and push_avg >= 0.300)
        p_data['t_pull'] = (pull_avg >= 0.350 and push_avg < 0.250)
        p_data['t_chancemaker'] = (p_data.get('runner_0_avg', 0) >= 0.300)
        p_data['t_nagashi'] = (push_avg >= 0.350)
        p_data['t_firststrike'] = (zeroStrikeAvg >= 0.400)
        p_data['t_vsace'] = (officialAvg >= 0.350)
        p_data['t_bat4'] = (bat4_avg >= 0.300)
        p_data['t_infield'] = ((infield_hits / hits) >= 0.400) if hits > 0 else False
        p_data['t_nebari'] = (twoStrikeAvg >= 0.300)
        p_data['t_katame'] = ((games_with_multi_hits / games_with_hits) >= 0.250) if games_with_hits > 0 else False
        p_data['t_manrui'] = (p_data.get('runner_F_ab', 0) >= 2 and p_data.get('runner_F_avg', 0) >= 0.300)
        p_data['t_bunt'] = (sh >= 5)
        p_data['t_sayonara'] = (sayonara_hits >= 1)
    else:
        p_data['t_koukaku'] = p_data['t_pull'] = p_data['t_chancemaker'] = p_data['t_nagashi'] = False
        p_data['t_firststrike'] = p_data['t_vsace'] = p_data['t_bat4'] = p_data['t_infield'] = False
        p_data['t_nebari'] = p_data['t_katame'] = p_data['t_manrui'] = p_data['t_bunt'] = p_data['t_sayonara'] = False

    p_data.update({
        'games': int(p_games_count), 'pa': int(pa), 'ab': int(ab), 'hits': int(hits), 'hr': int(hrs), 
        'bb': int(bb), 'so': int(so), 'avg': float(avg), 'slg': float(slg), 'obp': float(obp), 
        'ops': float(obp + slg), 'sb': int(sb), 'runs': int(runs), 'rbi': int(rbi), 'errors': int(errors), 
        'gidp': int(gidp), 'sh': int(sh), 'sf': int(sf)
    })


SPECIAL_ABILITY_ORDER = (
    ('t_pull', 'プルヒッター'),
    ('t_chancemaker', 'チャンスメーカー'),
    ('t_nagashi', '流し打ち'),
    ('t_koukaku', '広角打法'),
    ('t_firststrike', '初球○'),
    ('t_vsace', '対エース○'),
    ('t_nebari', '粘り打ち'),
    ('t_bat4', '4番○'),
    ('t_katame', '固め打ち'),
    ('t_infield', '内野安打○'),
    ('t_manrui', '満塁男'),
    ('t_bunt', 'バント○'),
    ('t_sayonara', 'サヨナラ男'),
)


def flag_on(value):
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true', 'yes', 'on')
    return value is True


def lit_special_abilities(player):
    """Return special abilities that are on, in display order. Every lit ability is blue."""
    player = player or {}
    lit = [(label, 'blue') for key, label in SPECIAL_ABILITY_ORDER if player.get(key)]
    if player.get('left_rank') in ('A', 'B'):
        lit.append(('対左投手○', 'blue'))
    return lit


HIT_RESULTS = {'H', '1B', '2B', '3B', 'HR', '単打', '2BH', '3BH', '本塁打'}
AB_RESULTS = {
    'H', '1B', '2B', '3B', 'HR', 'O', 'E', 'FC', 'K', '単打', '2BH', '3BH', '本塁打',
    'ゴロ', 'フライ', 'ライナー', '三振', '失策出塁', '敵失', '野手選択', '併殺打',
}
BUNT_RESULTS = {'犠打', 'SH', 'バント'}
RIGHT_PULL = {'5', '6', '7', '三', '遊', '左'}
RIGHT_PUSH = {'3', '4', '9', '一', '二', '右'}
INFIELD_DIRS = {'1', '2', '3', '4', '5', '6', '投', '捕', '一', '二', '三', '遊'}
NO_RUNNER = {'なし', '0', '0.0'}
LOADED_RUNNER = {'満塁', 'F'}
RISP_RUNNERS = {'2塁', '3塁', '1,2塁', '1,3塁', '2,3塁', '満塁', '2', '3', '1.2', '1.3', '2.3', 'F'}
QUANTITATIVE_FLAGS = (
    't_pull', 't_chancemaker', 't_nagashi', 't_koukaku', 't_firststrike', 't_vsace',
    't_nebari', 't_bat4', 't_katame', 't_infield', 't_manrui', 't_bunt',
)


def _clean_token(value):
    text = str(value or '').strip().replace('.0', '')
    if text in ('nan', 'None'):
        return ''
    return text


def _rank_from_diff(diff):
    if diff >= 0.250: return 'A'
    if diff >= 0.150: return 'B'
    if diff >= 0.050: return 'C'
    if diff >= -0.050: return 'D'
    if diff >= -0.150: return 'E'
    if diff >= -0.250: return 'F'
    return 'G'


def _avg(hits, ab):
    return hits / ab if ab else 0.0


def apply_plate_abilities(player, records):
    """Set quantitative blue-ability flags from 今年度個人成績 plate rows."""
    player = player or {}
    is_left = '左打' in str(player.get('pitch_bat', ''))
    pull_dirs = RIGHT_PUSH if is_left else RIGHT_PULL
    push_dirs = RIGHT_PULL if is_left else RIGHT_PUSH

    pull_ab = pull_h = push_ab = push_h = 0
    none_ab = none_h = loaded_ab = loaded_h = risp_ab = risp_h = 0
    s0_ab = s0_h = s2_ab = s2_h = 0
    off_ab = off_h = left_ab = left_h = 0
    bat4_ab = bat4_h = 0
    all_ab = all_h = infield_h = bunts = 0
    hit_games = {}

    for record in records or []:
        result = _clean_token(record.get('result'))
        if result in BUNT_RESULTS:
            bunts += 1
        if result not in AB_RESULTS:
            continue
        all_ab += 1
        is_hit = result in HIT_RESULTS
        if is_hit:
            all_h += 1
            game_key = f"{record.get('game_date')}_{record.get('game_id')}"
            hit_games[game_key] = hit_games.get(game_key, 0) + 1
        direction = _clean_token(record.get('direction'))
        if direction in ('なし',):
            direction = ''
        runner = _clean_token(record.get('runner'))
        strikes = _clean_token(record.get('strikes'))

        if direction in pull_dirs:
            pull_ab += 1
            if is_hit:
                pull_h += 1
        if direction in push_dirs:
            push_ab += 1
            if is_hit:
                push_h += 1
        if runner in NO_RUNNER:
            none_ab += 1
            if is_hit:
                none_h += 1
        if runner in LOADED_RUNNER:
            loaded_ab += 1
            if is_hit:
                loaded_h += 1
        if runner in RISP_RUNNERS:
            risp_ab += 1
            if is_hit:
                risp_h += 1
        if strikes in ('0',):
            s0_ab += 1
            if is_hit:
                s0_h += 1
        if strikes in ('2',):
            s2_ab += 1
            if is_hit:
                s2_h += 1
        if str(record.get('is_official')) == '1' or record.get('game_type') in ('official', '公式戦'):
            off_ab += 1
            if is_hit:
                off_h += 1
        if str(record.get('vs_left')) == '1':
            left_ab += 1
            if is_hit:
                left_h += 1
        if str(record.get('is_4th_bat')) == '1' or _clean_token(record.get('batting_order')) == '4':
            bat4_ab += 1
            if is_hit:
                bat4_h += 1
        if is_hit and direction in INFIELD_DIRS:
            infield_h += 1

    games_with_hits = len(hit_games)
    multi_hit_games = sum(1 for count in hit_games.values() if count >= 2)
    for key in QUANTITATIVE_FLAGS:
        player[key] = False
    if all_ab < 15:
        player['left_rank'] = 'D'
        player['chance_rank'] = 'D'
        return player

    pull_avg = _avg(pull_h, pull_ab)
    push_avg = _avg(push_h, push_ab)
    player['t_pull'] = pull_avg >= 0.350 and push_avg < 0.250
    player['t_chancemaker'] = _avg(none_h, none_ab) >= 0.300
    player['t_nagashi'] = push_avg >= 0.350
    player['t_koukaku'] = pull_avg >= 0.300 and push_avg >= 0.300
    player['t_firststrike'] = _avg(s0_h, s0_ab) >= 0.400
    player['t_vsace'] = _avg(off_h, off_ab) >= 0.350
    player['t_nebari'] = _avg(s2_h, s2_ab) >= 0.300
    player['t_bat4'] = _avg(bat4_h, bat4_ab) >= 0.300
    player['t_katame'] = (multi_hit_games / games_with_hits) >= 0.250 if games_with_hits else False
    player['t_infield'] = (infield_h / all_h) >= 0.400 if all_h else False
    player['t_manrui'] = loaded_ab >= 2 and _avg(loaded_h, loaded_ab) >= 0.300
    player['t_bunt'] = bunts >= 5

    left_diff = _avg(left_h, left_ab) - _avg(all_h, all_ab)
    if left_ab < 10:
        left_diff *= left_ab / 10.0
    player['left_rank'] = _rank_from_diff(left_diff)
    player['chance_rank'] = _rank_from_diff(_avg(risp_h, risp_ab) - _avg(all_h, all_ab))
    return player


def apply_steal_rank(player, stolen_bases):
    stolen = int(stolen_bases or 0)
    if stolen >= 8:
        player['steal_rank'] = 'A'
    elif stolen >= 5:
        player['steal_rank'] = 'B'
    elif stolen >= 2:
        player['steal_rank'] = 'C'
    else:
        player['steal_rank'] = 'D'
    return player


def apply_meeting_run_rank(player, meeting_rows):
    pid = player.get('player_id')
    longs = []
    short = long = 0
    for row in meeting_rows or []:
        try:
            run_long = float(row.get('run_long') or 0)
        except (TypeError, ValueError):
            run_long = 0
        if run_long > 0:
            longs.append(run_long)
        try:
            row_id = int(float(row.get('player_id')))
        except (TypeError, ValueError):
            continue
        if pid is not None and row_id == int(pid):
            try:
                short = float(row.get('run_short') or 0)
            except (TypeError, ValueError):
                short = 0
            long = run_long
    mean_long = sum(longs) / len(longs) if longs else 0
    return apply_run_rank(player, short, long, mean_long)


def apply_run_rank(player, run_short, run_long, run_mean_long):
    try:
        short = float(run_short or 0)
        long = float(run_long or 0)
        mean_long = float(run_mean_long or 0)
    except (TypeError, ValueError):
        short = long = mean_long = 0
    if long > 0 and short > 0 and mean_long > 0:
        run_val = (mean_long - long) * ((short * 4) - long)
        if run_val >= 0.55:
            player['run_rank'] = 'A'
        elif run_val >= 0.35:
            player['run_rank'] = 'B'
        elif run_val >= 0.10:
            player['run_rank'] = 'C'
        elif run_val >= 0.00:
            player['run_rank'] = 'D'
        elif run_val >= -0.40:
            player['run_rank'] = 'E'
        else:
            player['run_rank'] = 'F'
    else:
        player['run_rank'] = 'D'
    return player
