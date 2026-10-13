from webapp.tenant import games_ref


def collect_detail_records(target_name, target_id, games_docs=None):
    records = []
    annual_rbi = 0
    annual_sb = 0
    annual_h = 0
    annual_ab = 0
    annual_hr = 0

    try:
        loaded_games = games_docs if games_docs is not None else games_ref().order_by('date').get()

        def classify_result(act_str):
            if '本塁打' in act_str or 'HR' in act_str or 'ホームラン' in act_str: return 'HR'
            if '3BH' in act_str or '三塁打' in act_str or 'スリーベース' in act_str: return '3B'
            if '2BH' in act_str or '二塁打' in act_str or 'ツーベース' in act_str: return '2B'
            if '安打' in act_str or '安' in act_str or 'H' in act_str or 'ヒット' in act_str or '単打' in act_str: return '1B'
            if '三振' in act_str or 'K' in act_str.upper(): return 'K'
            if '四球' in act_str or '敬遠' in act_str or 'フォアボール' in act_str: return 'BB'
            if '死球' in act_str or 'デッドボール' in act_str: return 'HBP'
            if '犠打' in act_str or 'バント' in act_str: return 'SH'
            if '犠飛' in act_str: return 'SF'
            if '失' in act_str or 'エラー' in act_str: return 'E'
            if '野選' in act_str or 'FC' in act_str: return 'FC'
            if 'ゴロ' in act_str: return 'ゴロ'
            if 'フライ' in act_str: return 'フライ'
            if 'ライナー' in act_str: return 'ライナー'
            if '併殺' in act_str or 'ゲッツー' in act_str: return '併殺'
            return 'O'

        def extract_direction(act_str):
            if '三振' in act_str or '四球' in act_str or '死球' in act_str: return '-'
            if '投' in act_str or 'ピッチャー' in act_str: return '1'
            if '捕' in act_str or 'キャッチャー' in act_str: return '2'
            if '一' in act_str or 'ファースト' in act_str: return '3'
            if '二' in act_str or 'セカンド' in act_str: return '4'
            if '三' in act_str or 'サード' in act_str: return '5'
            if '遊' in act_str or 'ショート' in act_str: return '6'
            if '左' in act_str or 'レフト' in act_str: return '7'
            if '中' in act_str or 'センター' in act_str: return '8'
            if '右' in act_str or 'ライト' in act_str: return '9'
            return ''

        for doc in loaded_games:
            g_data = doc.to_dict()
            game_date = g_data.get('date', '不明')
            results = g_data.get('results', [])

            for p in results:
                p_name = str(p.get('name', '')).replace(" ", "").replace("　", "")
                p_id = str(p.get('player_id', p.get('id', '')))

                is_match = False
                if target_name and p_name and (target_name in p_name or p_name in target_name):
                    is_match = True
                elif target_id and p_id and (target_id == p_id):
                    is_match = True

                if is_match:
                    # 🌟 BaseMobの手動入力データと詳細結果のハイブリッド集計
                    b_stats = p.get('stats', {})
                    def get_val(*keys):
                        for k in keys:
                            val = p.get(k, b_stats.get(k))
                            if val not in [None, ""]:
                                try: return int(float(val))
                                except: pass
                        return 0

                    p_ab = get_val('AB', 'ab', 'at_bats')
                    p_h = get_val('H', 'h', 'hits', 'hit')
                    p_hr = get_val('HR', 'hr', 'homeruns', 'home_runs')
                    p_rbi = get_val('RBI', 'rbi', 'runs_batted_in', 'point', 'points')
                    p_sb = get_val('SB', 'sb', 'stolen_bases', 'steal')

                    m_ab, m_h, m_hr, m_rbi = 0, 0, 0, 0
                    actions_raw = p.get('actions', p.get('atBats', p.get('details', [])))
                    if actions_raw:
                        actions = list(actions_raw.values()) if isinstance(actions_raw, dict) else actions_raw
                        for pa in actions:
                            if isinstance(pa, str): pa = {'action': pa}
                            act = str(pa.get('action', pa.get('result', ''))).strip()

                            # ▼ 球場図・月別グラフ用のデータ保存 (ループ内に正しく統合)
                            fb_res = str(pa.get('result', pa.get('kind', ''))).strip()
                            fb_dir = str(pa.get('direction', pa.get('hit_direction', pa.get('dir', '')))).strip()
                            final_res = fb_res if fb_res else classify_result(act)
                            final_dir = fb_dir if fb_dir else extract_direction(act)

                            if final_res or act:
                                records.append({
                                    'game_date': game_date,
                                    'result': final_res,
                                    'direction': final_dir,
                                    'runner': str(pa.get('runners', '0'))
                                })

                            if not act: continue

                            try: m_rbi += int(pa.get('rbi', pa.get('point', 0)))
                            except: pass

                            is_ab = True
                            is_hit = False

                            if act in ['四球', '死球', '犠打', '犠飛'] or '四球' in act or '死球' in act or '犠打' in act or '犠飛' in act or '敬遠' in act:
                                is_ab = False

                            if '本' in act or 'HR' in act.upper():
                                m_hr += 1; is_hit = True
                            elif '3BH' in act or '三塁打' in act or '2BH' in act or '二塁打' in act or '安' in act or 'ヒット' in act or 'H' in act.upper() or '単打' in act:
                                is_hit = True

                            if is_hit: m_h += 1
                            if is_ab: m_ab += 1

                    annual_ab += max(p_ab, m_ab)
                    annual_h += max(p_h, m_h)
                    annual_hr += max(p_hr, m_hr)
                    annual_rbi += max(p_rbi, m_rbi)
                    annual_sb += p_sb

    except Exception as e:
        print(f"❌ player_detail_R1 データ取得エラー: {e}")
    return records, annual_rbi, annual_sb, annual_h, annual_ab, annual_hr
