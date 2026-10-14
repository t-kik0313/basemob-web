from webapp.presentation import page_route, screen_response
from flask import redirect, request, url_for

from webapp import app
from webapp.firebase import db
from webapp.teams.context import current_team, pa_per_game


def parse_pa_coef(raw):
    text = str(raw or '').strip().replace('，', '.').replace(',', '.')
    try:
        value = float(text)
    except ValueError:
        return None
    if value <= 0 or value > 20:
        return None
    return round(value, 2)


@page_route('/admin/regulation', methods=['GET', 'POST'])
def regulation_settings():
    team = current_team()
    error = None
    saved = request.args.get('saved') == '1'
    coef = pa_per_game()
    if request.method == 'POST':
        coef = parse_pa_coef(request.form.get('pa_coef'))
        if coef is None:
            error = '0より大きく20以下の数を入力してください。'
            coef = pa_per_game()
        elif team and db is not None:
            db.collection('teams').document(team['id']).set({'paPerGame': coef}, merge=True)
            return redirect(url_for('regulation_settings', saved=1))
        else:
            error = 'チームを確認できないため、保存できませんでした。'
    return screen_response(
        'regulation.html',
        pa_coef=coef,
        error=error,
        saved=saved and not error,
    )
