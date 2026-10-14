from webapp.presentation import page_route, screen_response
from flask import request, redirect, url_for
import traceback
from webapp import app
from webapp.firebase import db, db_old
from webapp.repositories.references import games_ref as team_games
from webapp.data import get_cleaned_df, load_players_df, load_merged_data
from webapp.stats.json_cache import get_players_data_json, update_json_from_csv


@page_route('/pitchers')
def pitchers():
    try:
        print("--- ⚾ 投手成績データの取得を開始します ---")
        games_ref = team_games()
        docs = games_ref.stream()

        pitcher_stats = {}
        game_count = 0

        for doc in docs:
            game_count += 1
            game_data = doc.to_dict()
            print(f"✅ 試合データ取得成功: ドキュメントID [{doc.id}]")

            pitchers_in_game = game_data.get('pitchers', [])
            if not pitchers_in_game:
                print(f"  ⚠️ この試合には 'pitchers' (投手) データがありません")
                continue

            for p in pitchers_in_game:
                name = p.get('name', '不明')
                print(f"  ▶ 投手データを処理中: {name}")

                if name not in pitcher_stats:
                    pitcher_stats[name] = {
                        'name': name, 'games': 0, 'wins': 0, 'losses': 0, 'saves': 0,
                        'outs': 0, 'hits': 0, 'hr': 0, 'bb': 0, 'hbp': 0,
                        'so': 0, 'runs': 0, 'er': 0, 'cg': 0, 'sho': 0
                    }

                stats = pitcher_stats[name]
                stats['games'] += 1
                stats['outs'] += int(p.get('outs', 0))
                stats['hits'] += int(p.get('hits', 0))
                stats['hr'] += int(p.get('hr', 0))
                stats['bb'] += int(p.get('bb', 0))
                stats['hbp'] += int(p.get('hbp', 0))
                stats['er'] += int(p.get('er', 0))

                # エラーが起きやすい箇所の保護
                stats['runs'] += int(p.get('runs', p.get('er', 0)))
                stats['so'] += int(p.get('so', p.get('k', 0))) # soかkか両方対応

                if p.get('cg') == True:
                    stats['cg'] += 1

        print(f"--- 🔄 全 {game_count} 試合の集計が完了。計算フェーズに入ります ---")

        pitchers_list = []
        for name, stats in pitcher_stats.items():
            total_outs = stats['outs']
            full_innings = total_outs // 3
            leftover_outs = total_outs % 3
            stats['display_innings'] = f"{full_innings}.{leftover_outs}"

            math_innings = total_outs / 3
            total_walks = stats['bb'] + stats['hbp']

            if math_innings > 0:
                stats['calc_whip'] = round((stats['hits'] + total_walks) / math_innings, 2)
                stats['calc_era'] = round((stats['er'] * 7) / math_innings, 2)
            else:
                stats['calc_whip'] = 0.00
                stats['calc_era'] = 0.00

            if total_walks > 0:
                stats['calc_k_bb'] = round(stats['so'] / total_walks, 2)
            else:
                stats['calc_k_bb'] = 0.00

            pitchers_list.append(stats)

        print(f"--- 🎉 処理完了！ {len(pitchers_list)} 人の投手データをHTMLに渡します ---")
        return screen_response('pitchers.html', pitchers=pitchers_list)

    except Exception as e:
        import traceback
        print("❌❌❌ 投手成績の取得・計算中に重大なエラーが発生しました ❌❌❌")
        print(f"エラー内容: {e}")
        traceback.print_exc() # エラーの詳しい原因を表示
        return screen_response('pitchers.html', pitchers=[])

