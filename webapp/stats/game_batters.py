def build_batters(game_data):
    # === 🌟 打者成績の計算処理（新表記統一・完全同期版） ===
    # 【新ルール】BaseMobの入力を、baseball-site側の表示名に変換する辞書
    RESULT_MAP = {
        "単打": "H", "2塁打": "2BH", "3塁打": "3BH", "本塁打": "HR",
        "ゴロ": "ゴロ", "フライ": "フライ", "ライナー": "ライナー",
        "三振": "三振", "四球": "四球", "死球": "死球",
        "犠打": "犠打", "犠飛": "犠飛",
        "失策出塁": "敵失", "野手選択": "野選"
    }

    batters = []
    player_list = game_data.get('results', game_data.get('batters', []))

    # === 🌟 修正: 代打などの文字が来てもエラーにならない安全な並び替え ===
    def safe_order(player_data):
        val = player_data.get('order', 99)
        if val == "" or val is None:  # 空っぽの場合
            return 99
        try:
            return int(float(val))    # 数字ならそのまま整数に
        except (ValueError, TypeError):
            return 99                 # 「代打」などの文字なら一番下(99)に

    player_list = sorted(player_list, key=safe_order)
    # ==========================================================

    for i, p in enumerate(player_list):
        # 🌟 新発見！ BaseMobの「stats」という隠し箱を開ける
        b_stats = p.get('stats', {})

        def get_val(*keys):
            for k in keys:
                # pの直下と、隠し箱（b_stats）の両方を探す！
                val = p.get(k, b_stats.get(k))
                if val not in [None, ""]:
                    try: return int(float(val))
                    except: pass
            return 0

        # 1. BaseMobの集計データを確実に取得
        stats = {
            'order': p.get('order', i + 1),
            'name': p.get('name', '不明'),
            'position': p.get('position', ''),
            'PA': get_val('PA', 'pa', 'plate_apperances', 'tpa'),
            'AB': get_val('AB', 'ab', 'at_bats'),
            'H': get_val('H', 'h', 'hits', 'hit'),
            'HR': get_val('HR', 'hr', 'homeruns', 'home_runs'),
            'RBI': get_val('RBI', 'rbi', 'runs_batted_in', 'point', 'points'),
            'RUNS': get_val('RUNS', 'runs', 'scores', 'score'),
            'SB': get_val('SB', 'sb', 'stolen_bases', 'steal'),
            'BH2': get_val('BH2', 'bh2', 'doubles', 'double'),
            'BH3': get_val('BH3', 'bh3', 'triples', 'triple'),
            'RISP_AB': get_val('RISP_AB', 'risp_ab'),
            'RISP_H': get_val('RISP_H', 'risp_h', 'risp_hits'),
            'K': get_val('K', 'k', 'so', 'strike_outs', 'strikeout'),
            'BB': get_val('BB', 'bb', 'walks', 'four_balls'),
            'HBP': get_val('HBP', 'hbp', 'dead_balls'),
            'SAC': get_val('SAC', 'sac', 'sacrifice_bants', 'bunts'),
            'SF': get_val('SF', 'sf', 'sacrifice_flies'),
            'DP': get_val('DP', 'dp', 'double_plays'),
            'ERR': get_val('ERR', 'err', 'errors'),
            'defensive_errors': get_val('defensive_errors')
        }

        # 2. 打席ごとの詳細データ（アクション）の計算
        actions_raw = p.get('actions', p.get('atBats', p.get('details', p.get('results', []))))

        if actions_raw:
            actions = list(actions_raw.values()) if isinstance(actions_raw, dict) else actions_raw

            m_stats = {k: 0 for k in stats.keys() if k not in ['order', 'name', 'position']}
            m_stats['PA'] = len(actions)

            for pa in actions:
                if isinstance(pa, str):
                    pa = {'action': pa}

                act_raw = ""
                for k_test in ['action', 'result', 'name', 'text', 'b_result']:
                    if pa.get(k_test):
                        act_raw = str(pa.get(k_test)).strip()
                        break

                norm_act = ""
                for key, display_name in RESULT_MAP.items():
                    if key in act_raw:
                        norm_act = display_name
                        break

                if not norm_act:
                    if '本' in act_raw or 'HR' in act_raw.upper(): norm_act = "HR"
                    elif '3' in act_raw or '三塁打' in act_raw: norm_act = "3BH"
                    elif '2' in act_raw or '二塁打' in act_raw: norm_act = "2BH"
                    # 🌟 新発見対応！ 「センターH」のように文字列の中にHが含まれていればヒット！
                    elif '安' in act_raw or 'ヒット' in act_raw or 'H' in act_raw.upper(): norm_act = "H"
                    elif '三振' in act_raw or act_raw.upper() == 'K': norm_act = "三振"
                    elif '四球' in act_raw or '敬遠' in act_raw or act_raw.upper() == 'BB': norm_act = "四球"
                    elif '死球' in act_raw or act_raw.upper() == 'HBP': norm_act = "死球"
                    elif '犠打' in act_raw or 'バント' in act_raw: norm_act = "犠打"
                    elif '犠飛' in act_raw: norm_act = "犠飛"
                    elif '失' in act_raw or 'エラー' in act_raw or '野選' in act_raw: norm_act = "敵失"
                    else: norm_act = act_raw

                is_hit = norm_act in ["H", "2BH", "3BH", "HR"]
                is_ab = norm_act not in ["四球", "死球", "犠打", "犠飛"]

                if norm_act == "HR": m_stats['HR'] += 1
                elif norm_act == "3BH": m_stats['BH3'] += 1
                elif norm_act == "2BH": m_stats['BH2'] += 1
                elif norm_act == "三振": m_stats['K'] += 1
                elif norm_act == "四球": m_stats['BB'] += 1
                elif norm_act == "死球": m_stats['HBP'] += 1
                elif norm_act == "犠打": m_stats['SAC'] += 1
                elif norm_act == "犠飛": m_stats['SF'] += 1
                elif norm_act == "敵失": m_stats['ERR'] += 1
                elif '併殺' in act_raw or act_raw.upper() == 'DP': m_stats['DP'] += 1

                if is_hit: m_stats['H'] += 1
                if is_ab: m_stats['AB'] += 1

                try: m_stats['RBI'] += int(pa.get('rbi', pa.get('point', pa.get('points', 0))))
                except: pass
                if pa.get('run') or pa.get('score'): m_stats['RUNS'] += 1

                case_info = str(pa.get('case', pa.get('runners', pa.get('base', pa.get('situation', '')))))
                is_risp = any(x in case_info for x in ['2', '3', '二', '三', '満'])
                if is_risp:
                    if is_ab: m_stats['RISP_AB'] += 1
                    if is_hit: m_stats['RISP_H'] += 1

            # 3. 集計データと手動計算の「いいとこ取り」をする
            if m_stats['PA'] > 0:
                for k in ['PA', 'AB', 'H', 'HR', 'BH2', 'BH3', 'K', 'BB', 'HBP', 'SAC', 'SF', 'DP', 'ERR', 'RISP_AB', 'RISP_H', 'RBI', 'RUNS', 'SB', 'defensive_errors']:
                    stats[k] = max(stats[k], m_stats.get(k, 0))

        batters.append(stats)
    return batters
