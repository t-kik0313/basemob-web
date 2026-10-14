"""旧 misc ルートの互換入口。"""
from webapp.routes.abilities import pawapuro
from webapp.routes.players import _image_error, _clean_image_path, _save_player_image, register_player, _edit_form_player, edit_player, HANDS, IMAGE_EXTS, MAX_IMAGE_BYTES
from webapp.routes.meeting import record_summary
