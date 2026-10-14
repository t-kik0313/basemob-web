from webapp.repositories.references import games_ref as team_games


def append_current_season(player, player_id, f_year, f_type, history_stats):
    try:
        games_ref = team_games().stream()
        cy = {k: 0 for k in ['games', 'plate_apperances', 'at_bats', 'hits', 'homeruns', 'runs_batted_in', 'scores', 'stolen_bases', 'doubles', 'triples', 'strike_outs', 'bb', 'hbp', 'sacrifice_bants', 'sacrifice_flies', 'double_plays', 'errors', 'risp_ab', 'risp_h']}
        cy['year'] = '2026'
        has_current_data = False
        clean_name = str(player.get('name', '')).replace(" ", "").replace("　", "")
        RESULT_MAP = {"単打":"H","2塁打":"2BH","3塁打":"3BH","本塁打":"HR","ゴロ":"ゴロ","フライ":"フライ","ライナー":"ライナー","三振":"三振","四球":"四球","死球":"死球","犠打":"犠打","犠飛":"犠飛","失策出塁":"敵失","野手選択":"野選"}

        for doc in games_ref:
            g = doc.to_dict()
            g_year = g.get('date', '2026')[:4] if g.get('date') else '2026'
            if f_year and g_year != f_year: continue
            if f_type and g.get('gameType', g.get('tournament', '')) != f_type and f_type not in g.get('gameType', g.get('tournament', '')): continue

            if 'results' in g:
                for p in g['results']:
                    p_name = str(p.get('name', '')).replace(" ", "").replace("　", "")
                    if str(p.get('player_id', p.get('id', 9999))) == str(player_id) or p_name == clean_name or (clean_name in p_name):
                        has_current_data = True
                        cy['games'] += 1
                        b_stats = p.get('stats', {})
                        def get_val(*keys):
                            for k in keys:
                                val = p.get(k, b_stats.get(k))
                                if val not in [None, ""]:
                                    try: return int(float(val))
                                    except: pass
                            return 0

                        pa = get_val('PA', 'pa', 'plate_apperances'); ab = get_val('AB', 'ab', 'at_bats')
                        h = get_val('H', 'h', 'hits'); hr = get_val('HR', 'hr', 'homeruns')
                        rbi = get_val('RBI', 'rbi', 'runs_batted_in', 'point'); runs = get_val('RUNS', 'runs', 'scores')
                        sb = get_val('SB', 'sb', 'stolen_bases'); doubles = get_val('BH2', 'bh2', 'doubles')
                        triples = get_val('BH3', 'bh3', 'triples'); so = get_val('K', 'k', 'so', 'strike_outs')
                        bb = get_val('BB', 'bb', 'walks'); hbp = get_val('HBP', 'hbp', 'dead_balls')
                        sh = get_val('SAC', 'sac', 'sacrifice_bants'); sf = get_val('SF', 'sf', 'sacrifice_flies')
                        dp = get_val('DP', 'dp', 'double_plays'); err = get_val('ERR', 'err', 'errors')
                        risp_ab = get_val('RISP_AB', 'risp_ab'); risp_h = get_val('RISP_H', 'risp_h')

                        m_pa, m_ab, m_h, m_hr, m_rbi, m_runs, m_2b, m_3b, m_so, m_bb, m_hbp, m_sh, m_sf, m_dp, m_err, m_rab, m_rh = [0]*17
                        actions_raw = p.get('actions', p.get('atBats', p.get('details', [])))
                        if actions_raw:
                            actions = list(actions_raw.values()) if isinstance(actions_raw, dict) else actions_raw
                            m_pa = len(actions)
                            for pa_act in actions:
                                if isinstance(pa_act, str): pa_act = {'action': pa_act}
                                act_raw = ""
                                for k_test in ['action', 'result', 'name', 'text']:
                                    if pa_act.get(k_test): act_raw = str(pa_act.get(k_test)).strip(); break
                                norm_act = ""
                                for k, v in RESULT_MAP.items():
                                    if k in act_raw: norm_act = v; break
                                if not norm_act:
                                    if '本' in act_raw or 'HR' in act_raw.upper(): norm_act = "HR"
                                    elif '3' in act_raw or '三塁打' in act_raw: norm_act = "3BH"
                                    elif '2' in act_raw or '二塁打' in act_raw: norm_act = "2BH"
                                    elif '安' in act_raw or 'ヒット' in act_raw or 'H' in act_raw.upper(): norm_act = "H"
                                    elif '三振' in act_raw or act_raw.upper() == 'K': norm_act = "三振"
                                    elif '四球' in act_raw or '敬遠' in act_raw: norm_act = "四球"
                                    elif '死球' in act_raw or act_raw.upper() == 'HBP': norm_act = "死球"
                                    elif '犠打' in act_raw or 'バント' in act_raw: norm_act = "犠打"
                                    elif '犠飛' in act_raw: norm_act = "犠飛"
                                    elif '失' in act_raw or 'エラー' in act_raw: norm_act = "敵失"

                                is_hit = norm_act in ["H", "2BH", "3BH", "HR"]
                                is_ab = norm_act not in ["四球", "死球", "犠打", "犠飛"]
                                if norm_act == "HR": m_hr += 1
                                elif norm_act == "3BH": m_3b += 1
                                elif norm_act == "2BH": m_2b += 1
                                elif norm_act == "三振": m_so += 1
                                elif norm_act == "四球": m_bb += 1
                                elif norm_act == "死球": m_hbp += 1
                                elif norm_act == "犠打": m_sh += 1
                                elif norm_act == "犠飛": m_sf += 1
                                elif norm_act == "敵失": m_err += 1
                                elif '併殺' in act_raw or act_raw.upper() == 'DP': m_dp += 1
                                if is_hit: m_h += 1
                                if is_ab: m_ab += 1
                                try: m_rbi += int(pa_act.get('rbi', pa_act.get('point', 0)))
                                except: pass
                                if pa_act.get('run') or pa_act.get('score'): m_runs += 1
                                case_info = str(pa_act.get('case', pa_act.get('runners', '')))
                                if any(x in case_info for x in ['2', '3', '二', '三', '満']):
                                    if is_ab: m_rab += 1
                                    if is_hit: m_rh += 1

                        cy['plate_apperances'] += max(pa, m_pa); cy['at_bats'] += max(ab, m_ab)
                        cy['hits'] += max(h, m_h); cy['homeruns'] += max(hr, m_hr)
                        cy['runs_batted_in'] += max(rbi, m_rbi); cy['scores'] += max(runs, m_runs)
                        cy['stolen_bases'] += sb; cy['doubles'] += max(doubles, m_2b)
                        cy['triples'] += max(triples, m_3b); cy['strike_outs'] += max(so, m_so)
                        cy['bb'] += max(bb, m_bb); cy['hbp'] += max(hbp, m_hbp)
                        cy['sacrifice_bants'] += max(sh, m_sh); cy['sacrifice_flies'] += max(sf, m_sf)
                        cy['double_plays'] += max(dp, m_dp); cy['errors'] += max(err, m_err)
                        cy['risp_ab'] += max(risp_ab, m_rab); cy['risp_h'] += max(risp_h, m_rh)

        if has_current_data:
            cy['batting_average'] = cy['hits'] / cy['at_bats'] if cy['at_bats'] > 0 else 0.0
            den = cy['at_bats'] + cy['bb'] + cy['hbp'] + cy['sacrifice_flies']
            cy['obp'] = (cy['hits'] + cy['bb'] + cy['hbp']) / den if den > 0 else 0.0
            tb = (cy['hits'] - cy['doubles'] - cy['triples'] - cy['homeruns']) + (cy['doubles'] * 2) + (cy['triples'] * 3) + (cy['homeruns'] * 4)
            cy['slg'] = tb / cy['at_bats'] if cy['at_bats'] > 0 else 0.0
            cy['OPS'] = cy['obp'] + cy['slg']
            cy['risp_avg'] = cy['risp_h'] / cy['risp_ab'] if cy['risp_ab'] > 0 else 0.0
            history_stats.append(cy)
    except Exception as e:
        import traceback; traceback.print_exc()
