from flask import render_template, request, redirect, url_for
import traceback
from webapp import app
from webapp.firebase import db, db_old
from webapp.repositories.references import games_ref as team_games
from webapp.data import get_cleaned_df, load_players_df, load_merged_data
from webapp.stats.json_cache import get_players_data_json, update_json_from_csv


@app.route('/teamstats')
def teamstats():
    from flask import request
    try:
        print("\n--- 📊 チーム成績の集計を開始します ---")
        f_year = request.args.get('year', '')
        f_type = request.args.get('game_type', '')

        # --- A. 2020年〜2025年の確定データ（手入力） ---
        historical_data = [
            {'year': '2025', 'games': 31, 'wins': 20, 'losses': 9, 'draws': 2, 'runs': 191, 'runs_allowed': 148, 'hits': 0, 'ab': 0, 'hr': 26, 'sb': 70, 'er': 0, 'outs': 0},
            {'year': '2024', 'games': 22, 'wins': 16, 'losses': 4, 'draws': 2, 'runs': 147, 'runs_allowed': 71, 'hits': 0, 'ab': 0, 'hr': 16, 'sb': 25, 'er': 0, 'outs': 0},
            {'year': '2023', 'games': 24, 'wins': 17, 'losses': 5, 'draws': 2, 'runs': 139, 'runs_allowed': 60, 'hits': 0, 'ab': 0, 'hr': 16, 'sb': 29, 'er': 0, 'outs': 0},
            {'year': '2022', 'games': 23, 'wins': 12, 'losses': 11, 'draws': 0, 'runs': 129, 'runs_allowed': 95, 'hits': 0, 'ab': 0, 'hr': 13, 'sb': 34, 'er': 0, 'outs': 0},
            {'year': '2021', 'games': 32, 'wins': 16, 'losses': 13, 'draws': 3, 'runs': 143, 'runs_allowed': 122, 'hits': 0, 'ab': 0, 'hr': 13, 'sb': 80, 'er': 0, 'outs': 0},
            {'year': '2020', 'games': 18, 'wins': 10, 'losses': 7, 'draws': 1, 'runs': 77, 'runs_allowed': 72, 'hits': 0, 'ab': 0, 'hr': 5, 'sb': 13, 'er': 0, 'outs': 0},
        ]

        yearly_stats = {}
        for hd in historical_data:
            if f_year and hd['year'] != f_year: continue
            if f_type: continue
            yearly_stats[hd['year']] = hd.copy()

        # --- B. 2026年以降のデータをFirestoreから集計 ---
        # 🌟 注意: ここが 'RYUNEN' になっています。アプリのTEAM IDと一致しているか確認！
        games_ref = team_games().stream()

        fetch_count = 0
        newest_game_year = None
        for doc in games_ref:
            g = doc.to_dict()
            fetch_count += 1

            g_date = g.get('date', '2026-01-01')
            g_year = str(g_date)[:4]
            if g_year.isdigit() and int(g_year) >= 2026:
                if newest_game_year is None or g_year > newest_game_year:
                    newest_game_year = g_year

            print(f"  ⚾ 取得した試合: {g_date} vs {g.get('opponent', '不明')} (属性: {g.get('gameType', '')})")

            if int(g_year) < 2026: continue
            if f_year and g_year != f_year: continue

            g_type_val = str(g.get('gameType', g.get('tournament', '')))
            if f_type and f_type not in g_type_val: continue

            if g_year not in yearly_stats:
                yearly_stats[g_year] = {
                    'year': g_year, 'games': 0, 'wins': 0, 'losses': 0, 'draws': 0,
                    'runs': 0, 'runs_allowed': 0, 'hits': 0, 'ab': 0, 'hr': 0, 'sb': 0, 'er': 0, 'outs': 0
                }

            ys = yearly_stats[g_year]
            ys['games'] += 1

            res = g.get('result', 'D')
            if res == 'W': ys['wins'] += 1
            elif res == 'L': ys['losses'] += 1
            else: ys['draws'] += 1

            # 🌟 どんな値（空欄・文字）が入っていても絶対にエラーを起こさない魔法
            def safe_int(v):
                if v in [None, ""]: return 0
                try: return int(float(v))
                except: return 0

            ys['runs'] += safe_int(g.get('scoreMy'))
            ys['runs_allowed'] += safe_int(g.get('scoreOpp'))

            if 'results' in g:
                for p in g['results']:
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
                    p_sb = get_val('SB', 'sb', 'stolen_bases', 'steal')

                    m_ab, m_h, m_hr = 0, 0, 0
                    actions_raw = p.get('actions', p.get('atBats', p.get('details', [])))
                    if actions_raw:
                        actions = list(actions_raw.values()) if isinstance(actions_raw, dict) else actions_raw
                        for pa in actions:
                            if isinstance(pa, str): pa = {'action': pa}
                            act_raw = str(pa.get('action', pa.get('result', ''))).strip()
                            if act_raw and act_raw not in ['四球', '死球', '犠打', '犠飛']: m_ab += 1
                            if '本' in act_raw or 'HR' in act_raw.upper(): m_hr += 1; m_h += 1
                            elif '安' in act_raw or 'ヒット' in act_raw or 'H' in act_raw.upper(): m_h += 1

                    ys['ab'] += max(p_ab, m_ab)
                    ys['hits'] += max(p_h, m_h)
                    ys['hr'] += max(p_hr, m_hr)
                    ys['sb'] += p_sb

            if 'pitchers' in g:
                for pit in g['pitchers']:
                    ys['er'] += safe_int(pit.get('er'))
                    ys['outs'] += safe_int(pit.get('outs'))

        print(f"✅ 合計 {fetch_count} 件の試合をFirestoreから読み込みました")

        team_stats_list = []
        for y in sorted(yearly_stats.keys(), reverse=True):
            ys = yearly_stats[y]
            decisions = ys['wins'] + ys['losses']
            ys['win_pct'] = ys['wins'] / decisions if decisions > 0 else 0.0
            ys['avg'] = ys['hits'] / ys['ab'] if ys['ab'] > 0 else 0.0
            ys['era'] = (ys['er'] * 21) / ys['outs'] if ys['outs'] > 0 else 0.0
            team_stats_list.append(ys)

        return render_template('teamstats.html', stats=team_stats_list, request=request, newest_game_year=newest_game_year)
    except Exception as e:
        import traceback; traceback.print_exc()
        return "エラーが発生しました", 500

