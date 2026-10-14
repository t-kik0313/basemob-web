"""日程処理: dates。"""
import re
import secrets
from datetime import date, datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    JST = ZoneInfo('Asia/Tokyo')
except Exception:
    JST = timezone(timedelta(hours=9))


def japan_today():
    return datetime.now(JST).date()



def window_end(today):
    month = today.month + 2
    year = today.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    return date(year, month, 1) - timedelta(days=1)



def parse_iso(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None



def in_window(value, today):
    parsed = parse_iso(value)
    return parsed is not None and today <= parsed <= window_end(today)



def event_window_end(today):
    month = today.month + 6
    year = today.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    if month == 12:
        return date(year + 1, 1, 1) - timedelta(days=1)
    return date(year, month + 1, 1) - timedelta(days=1)



def in_event_window(value, today):
    parsed = parse_iso(value)
    return parsed is not None and today <= parsed <= event_window_end(today)



def parse_by(value):
    parsed = parse_iso(value)
    if parsed is None or parsed.year < 2000 or parsed.year > 2100:
        return None
    return parsed.isoformat()



def plain_name(name):
    return str(name or '').replace(' ', '').replace('　', '')



def clip(value, limit):
    text = str(value or '').replace('\x00', '').replace('\r\n', '\n').replace('\r', '\n')
    return text[:limit]



def time_or_blank(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{2}:\d{2}', value):
        return ''
    hour, minute = int(value[:2]), int(value[3:])
    if hour > 23 or minute > 59:
        return ''
    return f'{hour:02d}:{minute:02d}'
