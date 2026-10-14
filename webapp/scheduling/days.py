"""日程処理: days。"""
import re
import secrets
from webapp.scheduling.common import PollError
from webapp.scheduling.dates import in_window


def apply_add(poll, iso, routine, today):
    if not in_window(iso, today):
        raise PollError('足せるのは今日から来月末までです。')
    if routine:
        if iso not in poll['removed']:
            raise PollError('その日はもう並んでいます。')
        poll['removed'] = [item for item in poll['removed'] if item != iso]
        return
    if iso in poll['added']:
        raise PollError('その日はもう並んでいます。')
    if len(poll['added']) >= 62:
        raise PollError('これ以上は足せません。')
    poll['removed'] = [item for item in poll['removed'] if item != iso]
    poll['added'].append(iso)
    poll['added'].sort()



def apply_remove(poll, iso, today):
    if not in_window(iso, today):
        raise PollError('外せるのは今日から来月末までです。')
    poll['added'] = [item for item in poll['added'] if item != iso]
    if iso not in poll['removed']:
        poll['removed'].append(iso)
        poll['removed'].sort()
    poll['answers'].pop(iso, None)
    poll['games'].pop(iso, None)
