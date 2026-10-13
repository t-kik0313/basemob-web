def _plain_name(value):
    return str(value or '').replace(" ", "").replace("　", "").strip()


def _match_player_id(name, players):
    clean = _plain_name(name)
    if not clean or not players:
        return None
    exact = [p for p in players if _plain_name(p.get('name')) == clean]
    if len(exact) == 1:
        return int(exact[0].get('player_id'))
    partial = [
        p for p in players
        if _plain_name(p.get('name')) and (
            _plain_name(p.get('name')) in clean or clean in _plain_name(p.get('name'))
        )
    ]
    if len(partial) == 1:
        return int(partial[0].get('player_id'))
    return None


def tally_games(games_ref, player_stats, players, RESULT_MAP):
    for doc in games_ref:
        g_data = doc.to_dict()
        if 'results' in g_data:
            for p in g_data['results']:
                name = p.get('name', '不明')

                if name not in player_stats:
                    p_id = p.get('player_id', p.get('id'))
                    if not p_id or str(p_id) == '9999':
                        p_id = _match_player_id(name, players)

                    player_stats[name] = {
                        'name': name,
                        'id': p_id,
                        'games': 0, 'pa': 0, 'ab': 0, 'hits': 0, 'hr': 0, 'rbi': 0, 'runs': 0, 'sb': 0,
                        'doubles': 0, 'triples': 0,
                        'so': 0, 'bb': 0, 'hbp': 0, 'sh': 0, 'sf': 0, 'gidp': 0, 'errors': 0, 'fielding_errors': 0,
                        'risp_ab': 0, 'risp_h': 0  # 🌟 得点圏の箱を追加
                    }

                stats = player_stats[name]
                stats['games'] += 1

                # 🌟 BaseMobの隠しデータ＆手動入力データを取得
                b_stats = p.get('stats', {})
                def get_val(*keys):
                    for k in keys:
                        val = p.get(k, b_stats.get(k))
                        if val not in [None, ""]:
                            try: return int(float(val))
                            except: pass
                    return 0

                g_pa = get_val('PA', 'pa', 'plate_apperances', 'tpa')
                g_ab = get_val('AB', 'ab', 'at_bats')
                g_hits = get_val('H', 'h', 'hits', 'hit')
                g_hr = get_val('HR', 'hr', 'homeruns', 'home_runs')
                g_rbi = get_val('RBI', 'rbi', 'runs_batted_in', 'point', 'points')
                g_runs = get_val('RUNS', 'runs', 'scores', 'score')
                g_sb = get_val('SB', 'sb', 'stolen_bases', 'steal')
                g_doubles = get_val('BH2', 'bh2', 'doubles', 'double')
                g_triples = get_val('BH3', 'bh3', 'triples', 'triple')
                g_risp_ab = get_val('RISP_AB', 'risp_ab')
                g_risp_h = get_val('RISP_H', 'risp_h', 'risp_hits')
                g_so = get_val('K', 'k', 'so', 'strike_outs', 'strikeout')
                g_bb = get_val('BB', 'bb', 'walks', 'four_balls')
                g_hbp = get_val('HBP', 'hbp', 'dead_balls')
                g_sh = get_val('SAC', 'sac', 'sacrifice_bants', 'bunts')
                g_sf = get_val('SF', 'sf', 'sacrifice_flies')
                g_gidp = get_val('DP', 'dp', 'double_plays')
                g_errors = get_val('ERR', 'err', 'errors')
                g_fielding_errors = get_val('defensive_errors', 'fielding_errors')

                # 🌟 詳細データ（actions）の計算
                actions_raw = p.get('actions', p.get('atBats', p.get('details', p.get('results', []))))
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
                        g_pa = max(g_pa, m_stats['pa'])
                        g_ab = max(g_ab, m_stats['ab'])
                        g_hits = max(g_hits, m_stats['hits'])
                        g_hr = max(g_hr, m_stats['hr'])
                        g_rbi = max(g_rbi, m_stats['rbi'])
                        g_runs = max(g_runs, m_stats['runs'])
                        g_doubles = max(g_doubles, m_stats['doubles'])
                        g_triples = max(g_triples, m_stats['triples'])
                        g_so = max(g_so, m_stats['so'])
                        g_bb = max(g_bb, m_stats['bb'])
                        g_hbp = max(g_hbp, m_stats['hbp'])
                        g_sh = max(g_sh, m_stats['sh'])
                        g_sf = max(g_sf, m_stats['sf'])
                        g_gidp = max(g_gidp, m_stats['gidp'])
                        g_errors = max(g_errors, m_stats['errors'])
                        g_risp_ab = max(g_risp_ab, m_stats['risp_ab'])
                        g_risp_h = max(g_risp_h, m_stats['risp_h'])

                # 🌟 算出した1試合分のデータを個人の年間成績に加算
                stats['pa'] += g_pa; stats['ab'] += g_ab; stats['hits'] += g_hits
                stats['hr'] += g_hr; stats['rbi'] += g_rbi; stats['runs'] += g_runs
                stats['sb'] += g_sb; stats['doubles'] += g_doubles; stats['triples'] += g_triples
                stats['so'] += g_so; stats['bb'] += g_bb; stats['hbp'] += g_hbp
                stats['sh'] += g_sh; stats['sf'] += g_sf; stats['gidp'] += g_gidp
                stats['errors'] += g_errors; stats['fielding_errors'] += g_fielding_errors
                stats['risp_ab'] += g_risp_ab; stats['risp_h'] += g_risp_h
