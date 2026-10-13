import os

from flask import render_template, request, redirect, url_for
import traceback
from webapp import app
from webapp.config import BASE_DIR
from webapp.firebase import db, db_old
from webapp.tenant import games_ref, next_player_id, players_ref, current_slug
from webapp.data import get_cleaned_df, load_players_df, load_merged_data
from webapp.stats.json_cache import get_players_data_json, update_json_from_csv

HANDS = ('右', '左', '両')
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
MAX_IMAGE_BYTES = 8 * 1024 * 1024


@app.route('/pawapuro')
def pawapuro():
    from webapp.routes.current_year_records import collect_season
    from webapp.routes.qualitative_abilities import flag_on
    from webapp.stats.ability_ranks import apply_meeting_run_rank, apply_plate_abilities, apply_steal_rank

    players_data = get_players_data_json()
    meeting = load_merged_data()
    meeting_rows = [] if meeting.empty else meeting.to_dict(orient='records')
    qualitative = {}
    try:
        for doc in players_ref().stream():
            qualitative[str(doc.id)] = flag_on((doc.to_dict() or {}).get('qual_sayonara'))
    except Exception as error:
        print(f"⚠️ 定性特殊能力の読み込みエラー: {error}")
    for player in players_data:
        name = str(player.get('name', '')).replace(" ", "").replace("　", "")
        plate_records, stolen_bases = collect_season(name, player.get('player_id'))
        apply_plate_abilities(player, plate_records)
        apply_steal_rank(player, stolen_bases)
        apply_meeting_run_rank(player, meeting_rows)
        player['t_sayonara'] = qualitative.get(str(player.get('player_id')), False)
    return render_template('pawapuro.html', players_data=players_data)

def _image_error(image):
    if image is None or not image.filename:
        return None
    ext = os.path.splitext(image.filename)[1].lower()
    image.seek(0, os.SEEK_END)
    size = image.tell()
    image.seek(0)
    if ext not in IMAGE_EXTS or size <= 0 or size > MAX_IMAGE_BYTES:
        return '画像は jpg、png、webp、gif（8MBまで）を選んでください。'
    return None


def _save_player_image(player_id, image):
    if image is None or not image.filename:
        return 'default.png'
    ext = os.path.splitext(image.filename)[1].lower()
    if ext == '.jpeg':
        ext = '.jpg'
    slug = current_slug() or 'team'
    folder = os.path.join(BASE_DIR, 'static', 'player_images', slug)
    os.makedirs(folder, exist_ok=True)
    filename = f'{player_id}{ext}'
    image.save(os.path.join(folder, filename))
    return f'player_images/{slug}/{filename}'


@app.route('/register_player', methods=['GET', 'POST'])
def register_player():
    form = {'throw_hand': '右', 'bat_hand': '右'}
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        number = (request.form.get('number') or '').strip()
        pos = (request.form.get('position') or '').strip()
        throw_hand = request.form.get('throw_hand') or ''
        bat_hand = request.form.get('bat_hand') or ''
        form = {
            'name': name,
            'number': number,
            'position': pos,
            'throw_hand': throw_hand,
            'bat_hand': bat_hand,
        }
        if not name or not number:
            return render_template('register.html', error='選手名と背番号を入力してください。', form=form)
        if throw_hand not in HANDS or bat_hand not in HANDS:
            return render_template('register.html', error='投と打は右・左・両から選んでください。', form=form)

        image = request.files.get('image')
        image_error = _image_error(image)
        if image_error:
            return render_template('register.html', error=image_error, form=form)

        new_id = next_player_id()
        image_path = _save_player_image(new_id, image)
        new_player = {
            'player_id': new_id,
            'name': name,
            'number': number,
            'no': number,
            'pos1': pos,
            'pitch_bat': f'{throw_hand}投{bat_hand}打',
            'image_path': image_path,
        }

        if db is not None:
            players_ref().document(str(new_id)).set(new_player, merge=True)

        return redirect(url_for('players'))
    return render_template('register.html', form=form)

@app.route('/edit_player/<int:player_id>', methods=['GET', 'POST'])
def edit_player(player_id):
    if request.method == 'POST':
        update_data = {}
        for f in ['name','number','pos1','pos2','pos3','pitch_bat','image_path','birth_date']:
            if request.form.get(f) is not None: 
                update_data[f] = request.form.get(f)
                
        if db is not None:
            players_ref().document(str(player_id)).set(update_data, merge=True)

        return redirect(url_for('player_detail_R1', player_id=player_id))

    df = get_cleaned_df('players') 
    
    player = {}
    if not df.empty and player_id in df['player_id'].values:
        row = df[df['player_id'] == player_id].iloc[0]
        player = {
            'id': int(row['player_id']), 'player_id': int(row['player_id']),
            'name': row.get('name', ''), 
            'number': row.get('number', ''), 
            'pos1': row.get('pos1', ''),
            'pos2': row.get('pos2', ''),
            'pos3': row.get('pos3', ''),
            'pitch_bat': row.get('pitch_bat', ''), 
            'image_path': row.get('image_path', '')
        }
    return render_template('edit_player.html', player=player)

@app.route('/record_summary')
def record_summary():
    merged = load_merged_data()
    records = merged.to_dict(orient='records') if not merged.empty else []
    return render_template('record_summary.html', records=records)

