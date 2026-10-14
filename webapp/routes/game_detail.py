import os
import re

from flask import render_template, request, redirect, url_for
from webapp import app
from webapp.config import BASE_DIR
from webapp.firebase import db, db_old
from webapp.teams.context import current_slug
from webapp.repositories.references import games_ref
from webapp.data import get_cleaned_df, load_players_df, load_merged_data
from webapp.stats.json_cache import get_players_data_json, update_json_from_csv
from webapp.stats.game_batters import build_batters

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
MAX_IMAGE_BYTES = 8 * 1024 * 1024
YOUTUBE_ID_RE = re.compile(
    r'(?:youtu\.be/|youtube\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/))([A-Za-z0-9_-]{11})'
)


def _game_ref(game_id):
    return games_ref().document(game_id)


def _image_dir():
    slug = current_slug() or 'team'
    folder = os.path.join(BASE_DIR, 'static', 'scoreboard_images', slug)
    os.makedirs(folder, exist_ok=True)
    return folder


def _image_filename(game_id, ext):
    stem = ''.join('_' if c in '<>:"/\\|?*' else c for c in game_id).strip()
    if stem in ('', '.', '..'):
        stem = 'game'
    return stem + ext


def _youtube_id(url):
    if not url:
        return ''
    match = YOUTUBE_ID_RE.search(str(url))
    return match.group(1) if match else ''


def _remove_stored_image(rel):
    rel = str(rel or '').replace('\\', '/')
    if not rel.startswith('scoreboard_images/'):
        return
    folder = os.path.realpath(os.path.join(BASE_DIR, 'static', 'scoreboard_images'))
    path = os.path.realpath(os.path.join(BASE_DIR, 'static', rel))
    if os.path.commonpath([folder, path]) != folder or not os.path.isfile(path):
        return
    os.remove(path)


@app.route('/game/<game_id>')
def game_detail(game_id):
    try:
        # DBから試合データを取得
        game_ref = games_ref().document(game_id)
        doc_snap = game_ref.get()

        if not doc_snap.exists:
            return "試合が見つかりません", 404

        game_data = doc_snap.to_dict()
        game_data['id'] = doc_snap.id

        # ▼▼▼ 投手データの取得 ▼▼▼
        pitchers_docs = game_ref.collection('pitchers').stream()
        pitchers_data = [doc.to_dict() for doc in pitchers_docs]
        pitchers = pitchers_data if pitchers_data else game_data.get('pitchers', [])

        for p in pitchers:
            total_outs = int(p.get('outs', p.get('out', 0)))
            full_innings = total_outs // 3
            leftover_outs = total_outs % 3
            p['display_innings'] = f"{full_innings}.{leftover_outs}"

        game_data['youtube_id'] = _youtube_id(game_data.get('youtube_url'))
        batters = build_batters(game_data)
        return render_template('game_detail.html', game=game_data, batters=batters, pitchers=pitchers)

    except Exception as e:
        import traceback
        print(f"❌ 試合詳細データの取得エラー:")
        traceback.print_exc()
        return "エラーが発生しました", 500


@app.route('/game/<game_id>/scoreboard_image', methods=['POST'])
def upload_scoreboard_image(game_id):
    game_ref = _game_ref(game_id)
    if not game_ref.get().exists:
        return "試合が見つかりません", 404

    image = request.files.get('scoreboard_image')
    if not image or not image.filename:
        return redirect(url_for('game_detail', game_id=game_id))

    ext = os.path.splitext(image.filename)[1].lower()
    image.seek(0, os.SEEK_END)
    size = image.tell()
    image.seek(0)
    if ext not in IMAGE_EXTS or size <= 0 or size > MAX_IMAGE_BYTES:
        return redirect(url_for('game_detail', game_id=game_id))

    existing = (game_ref.get().to_dict() or {}).get('scoreboard_image')
    _remove_stored_image(existing)
    folder = _image_dir()
    filename = _image_filename(game_id, ext)
    slug = current_slug() or 'team'
    image.save(os.path.join(folder, filename))
    game_ref.update({'scoreboard_image': f"scoreboard_images/{slug}/{filename}"})
    return redirect(url_for('game_detail', game_id=game_id))


@app.route('/game/<game_id>/youtube', methods=['POST'])
def save_youtube_link(game_id):
    game_ref = _game_ref(game_id)
    if not game_ref.get().exists:
        return "試合が見つかりません", 404

    url = request.form.get('youtube_url', '').strip()
    if not url.startswith(('http://', 'https://')) or len(url) > 500:
        return redirect(url_for('game_detail', game_id=game_id))

    game_ref.update({'youtube_url': url})
    return redirect(url_for('game_detail', game_id=game_id))

