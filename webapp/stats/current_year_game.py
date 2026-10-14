def absorb_game(p, g_data, game_date, RESULT_MAP, annual_totals, current_year_games):
    b_stats = p.get('stats') or {}
    if not isinstance(b_stats, dict):
        b_stats = {}

    def get_val(*keys):
        for k in keys:
            val = p.get(k, b_stats.get(k))
            if val not in [None, ""]:
                try: return int(float(val))
                except: pass
        return 0

    game_stats = {
        'date': game_date,
        'opponent': g_data.get('opponent', '不明'),
        'result': g_data.get('result', ''),
        'pa': get_val('PA', 'pa', 'plate_apperances', 'tpa'),
        'ab': get_val('AB', 'ab', 'at_bats'),
        'hits': get_val('H', 'h', 'hits', 'hit'),
        'hr': get_val('HR', 'hr', 'homeruns', 'home_runs'),
        'rbi': get_val('RBI', 'rbi', 'runs_batted_in', 'point', 'points'),
        'runs': get_val('RUNS', 'runs', 'scores', 'score'),
        'sb': get_val('SB', 'sb', 'stolen_bases', 'steal'),
        'doubles': get_val('BH2', 'bh2', 'doubles', 'double'),
        'triples': get_val('BH3', 'bh3', 'triples', 'triple'),
        'risp_ab': get_val('RISP_AB', 'risp_ab'),
        'risp_h': get_val('RISP_H', 'risp_h', 'risp_hits'),
        'so': get_val('K', 'k', 'so', 'strike_outs', 'strikeout'),
        'bb': get_val('BB', 'bb', 'walks', 'four_balls'),
        'hbp': get_val('HBP', 'hbp', 'dead_balls'),
        'sh': get_val('SAC', 'sac', 'sacrifice_bants', 'bunts'),
        'sf': get_val('SF', 'sf', 'sacrifice_flies'),
        'gidp': get_val('DP', 'dp', 'double_plays'),
        'errors': get_val('ERR', 'err', 'errors'),
        'actions_text': []
    }

    actions_raw = p.get('actions', p.get('atBats', p.get('details', [])))
    if actions_raw:
        actions = list(actions_raw.values()) if isinstance(actions_raw, dict) else actions_raw
        m_stats = {k: 0 for k in ['pa', 'ab', 'hits', 'hr', 'rbi', 'runs', 'doubles', 'triples', 'so', 'bb', 'hbp', 'sh', 'sf', 'gidp', 'errors', 'risp_ab', 'risp_h']}
        m_stats['pa'] = len(actions)

        for pa in actions:
            if isinstance(pa, str): pa = {'action': pa}
            act_raw = ""
            for k_test in ['action', 'result', 'name', 'text', 'b_result']:
                if pa.get(k_test):
                    act_raw = str(pa.get(k_test)).strip()
                    break

            norm_act = ""
            for key, display_name in RESULT_MAP.items():
                if key in act_raw: norm_act = display_name; break

            if not norm_act:
                if '本' in act_raw or 'HR' in act_raw.upper(): norm_act = "HR"
                elif '3' in act_raw or '三塁打' in act_raw: norm_act = "3BH"
                elif '2' in act_raw or '二塁打' in act_raw: norm_act = "2BH"
                elif '安' in act_raw or 'ヒット' in act_raw or 'H' in act_raw.upper(): norm_act = "H"
                elif '三振' in act_raw or act_raw.upper() == 'K': norm_act = "三振"
                elif '四球' in act_raw or '敬遠' in act_raw or act_raw.upper() == 'BB': norm_act = "四球"
                elif '死球' in act_raw or act_raw.upper() == 'HBP': norm_act = "死球"
                elif '犠打' in act_raw or 'バント' in act_raw: norm_act = "犠打"
                elif '犠飛' in act_raw: norm_act = "犠飛"
                elif '失' in act_raw or 'エラー' in act_raw or '野選' in act_raw: norm_act = "敵失"
                else: norm_act = act_raw

            game_stats['actions_text'].append(act_raw)

            is_hit = norm_act in ["H", "2BH", "3BH", "HR"]
            is_ab = norm_act not in ["四球", "死球", "犠打", "犠飛"]

            if norm_act == "HR": m_stats['hr'] += 1
            elif norm_act == "3BH": m_stats['triples'] += 1
            elif norm_act == "2BH": m_stats['doubles'] += 1
            elif norm_act == "三振": m_stats['so'] += 1
            elif norm_act == "四球": m_stats['bb'] += 1
            elif norm_act == "死球": m_stats['hbp'] += 1
            elif norm_act == "犠打": m_stats['sh'] += 1
            elif norm_act == "犠飛": m_stats['sf'] += 1
            elif norm_act == "敵失": m_stats['errors'] += 1
            elif '併殺' in act_raw or act_raw.upper() == 'DP': m_stats['gidp'] += 1

            if is_hit: m_stats['hits'] += 1
            if is_ab: m_stats['ab'] += 1

            try: m_stats['rbi'] += int(pa.get('rbi', pa.get('point', pa.get('points', 0))))
            except: pass
            if pa.get('run') or pa.get('score'): m_stats['runs'] += 1

            case_info = str(pa.get('case', pa.get('runners', pa.get('base', pa.get('situation', '')))))
            is_risp = any(x in case_info for x in ['2', '3', '二', '三', '満'])
            if is_risp:
                if is_ab: m_stats['risp_ab'] += 1
                if is_hit: m_stats['risp_h'] += 1

        if m_stats['pa'] > 0:
            for k in m_stats:
                game_stats[k] = max(game_stats[k], m_stats[k])

    game_stats['avg'] = game_stats['hits'] / game_stats['ab'] if game_stats['ab'] > 0 else 0.0
    current_year_games.append(game_stats)

    for k in annual_totals:
        annual_totals[k] += game_stats[k]
