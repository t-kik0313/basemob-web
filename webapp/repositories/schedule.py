"""旧 tenant.py の処理を役割別に分割。"""
import os
from config.paths import SCHEDULE_FILE
from firebase_admin import firestore
from webapp.firebase import db
from webapp.repositories.references import schedule_ref
from webapp.scheduling.normalization import normalize_poll


def read_schedule(team_id=None):
    if db is None:
        return []
    doc = schedule_ref(team_id).get()
    if doc.exists:
        items = (doc.to_dict() or {}).get('items')
        if isinstance(items, list):
            return items
    path = str(SCHEDULE_FILE)
    if not os.path.exists(path):
        return []
    import json
    with open(path, encoding='utf-8') as handle:
        text = handle.read().strip()
    if not text:
        return []
    data = json.loads(text)
    return data if isinstance(data, list) else []



def write_schedule(items, team_id=None):
    schedule_ref(team_id).set({'items': items})



def read_poll(team_id=None):
    if db is None:
        return normalize_poll(None)
    doc = schedule_ref(team_id).get()
    raw = (doc.to_dict() or {}).get('poll') if doc.exists else None
    return normalize_poll(raw)



def update_poll(mutator, team_id=None):
    if db is None:
        raise RuntimeError('schedule store is unavailable')
    ref = schedule_ref(team_id)
    transaction = db.transaction()
    result = {}

    @firestore.transactional
    def _run(transaction):
        snap = ref.get(transaction=transaction)
        raw = snap.to_dict() if snap.exists else {}
        poll = normalize_poll((raw or {}).get('poll'))
        mutator(poll)
        poll = normalize_poll(poll)
        result['poll'] = poll
        # merge=True は中のキーを葉ごとに足すだけで、消した予定は Firestore に残る。
        # poll フィールドごと置き換えると、削除が保存される。
        transaction.set(ref, {'poll': poll}, merge=['poll'])

    _run(transaction)
    return result['poll']
