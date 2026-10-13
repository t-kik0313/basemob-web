from datetime import datetime
from webapp.utils import safe_int


def player_shell(p_row):
    pid = int(p_row['player_id'])
    p_data = p_row.to_dict()
    p_data['player_id'] = pid
    p_data['id'] = pid

    p_data['plus_meet'] = safe_int(p_row.get('plus_meet', 0))
    p_data['plus_power'] = safe_int(p_row.get('plus_power', 0))
    p_data['plus_speed'] = safe_int(p_row.get('plus_speed', 0))
    p_data['plus_arm'] = safe_int(p_row.get('plus_arm', 0))
    p_data['plus_defense'] = safe_int(p_row.get('plus_defense', 0))
    p_data['plus_catching'] = safe_int(p_row.get('plus_catching', 0))

    dan_val = safe_int(p_row.get('dan', 2), 2)
    p_data['dan'] = dan_val if dan_val > 0 else 2

    p_data['injury'] = str(p_row.get('injury', 'D')) if str(p_row.get('injury', '')).strip() != "" else 'D'
    p_data['throw'] = str(p_row.get('throw', 'D')) if str(p_row.get('throw', '')).strip() != "" else 'D'
    p_data['catcher'] = str(p_row.get('catcher', 'D')) if str(p_row.get('catcher', '')).strip() != "" else 'D'

    age = 25 
    birth_str = str(p_data.get('birth_date', '')).strip()
    if birth_str:
        for fmt in ('%Y-%m-%d', '%Y/%m/%d'):
            try:
                b_date = datetime.strptime(birth_str, fmt)
                today = datetime.today() 
                age = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
                break
            except ValueError: continue
    p_data['age'] = int(age)
    p_data['holding_points'] = max(0, (40 - int(age)) * 1)

    p_data.setdefault('image_path', 'default.png')
    p_data.setdefault('character', 'ふつう')
    p_data.setdefault('pitch_bat', '右投右打')
    return pid, p_data
