from flask import render_template, request, redirect, url_for
import traceback
from webapp import app
from webapp.firebase import db, db_old
from webapp.repositories.references import games_ref
from webapp.data import get_cleaned_df, load_players_df, load_merged_data
from webapp.stats.json_cache import get_players_data_json, update_json_from_csv


@app.route('/games')
def games():
    try:
        # DBから全試合データを取得（正しい住所）
        docs = games_ref().stream()
        games_list = []
        selected_year = request.args.get('year', '').strip()

        for doc in docs:
            g_data = doc.to_dict()
            g_data['id'] = doc.id
            if selected_year and str(g_data.get('date', ''))[:4] != selected_year:
                continue

            # === 🌟 この試合の打者成績を計算する ===
            batter_stats = []
            if 'results' in g_data:
                for i, p in enumerate(g_data['results']):
                    # 1人分の成績を入れる箱
                    stats = {
                        'order': i + 1,
                        'name': p.get('name', '不明'),
                        'PA': 0, 'AB': 0, 'H': 0, 'HR': 0, 'RBI': 0, 'RUNS': 0, 'SB': int(p.get('sb', 0) or 0),
                        'BH2': 0, 'BH3': 0, 'RISP_AB': 0, 'RISP_H': 0,
                        'K': 0, 'BB': 0, 'HBP': 0, 'SAC': 0, 'SF': 0, 'DP': 0, 'ERR': 0
                    }

                    actions_raw = p.get('actions', [])

                    # 🛡️ 安全装置1
                    if isinstance(actions_raw, dict):
                        actions = list(actions_raw.values())
                    elif isinstance(actions_raw, str):
                        actions = [{'action': actions_raw}]
                    else:
                        actions = actions_raw

                    stats['PA'] = len(actions) # 打席数

                    for pa in actions:
                        # 🛡️ 安全装置2
                        if isinstance(pa, str):
                            pa = {'action': pa}

                        act = str(pa.get('action', ''))

                        try:
                            stats['RBI'] += int(pa.get('rbi', 0))
                        except (ValueError, TypeError):
                            pass

                        if pa.get('run'):
                            stats['RUNS'] += 1

                        runners = str(pa.get('runners', ''))
                        is_risp = ('2' in runners or '3' in runners)
                        is_ab = True
                        is_hit = False

                        if act.endswith('本塁打') or act.endswith('HR'):
                            stats['HR'] += 1; is_hit = True
                        elif act.endswith('3BH'):
                            stats['BH3'] += 1; is_hit = True
                        elif act.endswith('2BH'):
                            stats['BH2'] += 1; is_hit = True
                        elif act.endswith('H') or act.endswith('安打') or act.endswith('安'):
                            is_hit = True
                        elif '三振' in act:
                            stats['K'] += 1
                        elif '四球' in act or '敬遠' in act:
                            stats['BB'] += 1; is_ab = False
                        elif '死球' in act:
                            stats['HBP'] += 1; is_ab = False
                        elif '犠打' in act or 'バント' in act:
                            stats['SAC'] += 1; is_ab = False
                        elif '犠飛' in act:
                            stats['SF'] += 1; is_ab = False
                        elif '併殺' in act or 'ゲッツー' in act:
                            stats['DP'] += 1
                        elif '失' in act or 'エラー' in act:
                            stats['ERR'] += 1

                        if is_hit:
                            stats['H'] += 1
                            if is_risp:
                                stats['RISP_H'] += 1
                        if is_ab:
                            stats['AB'] += 1
                            if is_risp:
                                stats['RISP_AB'] += 1

                    batter_stats.append(stats)

            # 計算した「打者成績表」を埋め込む
            g_data['batter_stats'] = batter_stats
            games_list.append(g_data)

        # 日付が新しい順（降順）に並び替え
        games_list = sorted(games_list, key=lambda x: x.get('date', '0000-00-00'), reverse=True)

        return render_template('games.html', games=games_list, selected_year=selected_year)

    except Exception as e:
        import traceback
        print("❌ エラー発生:")
        traceback.print_exc()
        return "エラーが発生しました", 500


