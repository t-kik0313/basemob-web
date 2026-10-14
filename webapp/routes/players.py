import os
from flask import render_template, request, redirect, url_for
from webapp import app
from webapp.config import BASE_DIR
from webapp.firebase import db
from webapp.teams.context import current_slug, current_team_id
from webapp.services.player_view import load_player_shell
from webapp.repositories.players import next_player_id
from webapp.repositories.references import players_ref
from webapp.data import load_merged_data
from webapp.stats.json_cache import get_players_data_json

HANDS = ('右', '左', '両')
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
MAX_IMAGE_BYTES = 8 * 1024 * 1024

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



def _clean_image_path(value):
    path = (value or '').strip().replace('\\', '/')
    if not path:
        return 'default.png'
    if path.startswith('/') or ':' in path or '\x00' in path:
        return None
    parts = []
    for part in path.split('/'):
        if part in ('', '.'):
            continue
        if part == '..':
            return None
        parts.append(part)
    cleaned = '/'.join(parts)
    if not cleaned or len(cleaned) > 240:
        return None
    return cleaned



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



def _edit_form_player(player_id, source):
    def value(key, default=''):
        got = source.get(key, default)
        if got is None:
            return default
        text = str(got).strip()
        if text.lower() == 'nan':
            return default
        return got

    return {
        'id': player_id,
        'player_id': player_id,
        'name': value('name'),
        'number': value('number'),
        'pos1': value('pos1'),
        'pos2': value('pos2'),
        'pos3': value('pos3'),
        'pitch_bat': value('pitch_bat'),
        'birth_date': value('birth_date'),
        'image_path': value('image_path'),
    }



@app.route('/edit_player/<int:player_id>', methods=['GET', 'POST'])
def edit_player(player_id):
    if request.method == 'POST':
        update_data = {}
        for field in ['name', 'number', 'pos1', 'pos2', 'pos3', 'pitch_bat', 'birth_date']:
            if request.form.get(field) is not None:
                update_data[field] = request.form.get(field)

        image = request.files.get('image')
        image_error = _image_error(image)
        image_path = _clean_image_path(request.form.get('image_path'))
        if image_error or image_path is None:
            player = _edit_form_player(player_id, request.form)
            message = image_error or '画像パスは static フォルダ内の相対パスにしてください。'
            return render_template('edit_player.html', player=player, error=message)

        if image is not None and image.filename:
            update_data['image_path'] = _save_player_image(player_id, image)
        else:
            update_data['image_path'] = image_path

        if db is not None:
            players_ref().document(str(player_id)).set(update_data, merge=True)

        return redirect(url_for('player_detail_R1', player_id=player_id))

    source = dict(load_player_shell(player_id) or {})
    stored = {}
    if db is not None and current_team_id():
        doc = players_ref().document(str(player_id)).get()
        if doc.exists:
            stored = doc.to_dict() or {}
    for field in ('name', 'number', 'pos1', 'pos2', 'pos3', 'pitch_bat', 'birth_date', 'image_path'):
        if field in stored:
            source[field] = stored.get(field) or ''
    if not source.get('number'):
        source['number'] = stored.get('no') or source.get('no') or ''
    player = _edit_form_player(player_id, source)
    return render_template('edit_player.html', player=player)
