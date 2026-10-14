from flask import render_template, request, redirect, url_for
import traceback
from webapp import app
from webapp.repositories.players import roster_rows


@app.route('/')
def index(): return redirect(url_for('players'))

# トップページ（選手一覧）
@app.route('/players')
def players():
    try:
        players_list = roster_rows()
        print(f"--- 🎉 処理完了！ {len(players_list)} 人の選手データをHTMLに渡します ---")
        return render_template('players.html', players=players_list)

    except Exception as e:
        import traceback
        print("❌❌❌ 選手一覧の取得エラー ❌❌❌")
        traceback.print_exc()
        return render_template('players.html', players=[])


