RESULT_MAP = {
    "単打": "H", "2塁打": "2BH", "3塁打": "3BH", "本塁打": "HR",
    "ゴロ": "ゴロ", "フライ": "フライ", "ライナー": "ライナー",
    "三振": "三振", "四球": "四球", "死球": "死球",
    "犠打": "犠打", "犠飛": "犠飛", "失策出塁": "敵失", "野手選択": "野選",
}


def list_actions(player):
    raw = player.get('actions', player.get('atBats', player.get('details', player.get('results', []))))
    if not raw:
        return []
    if isinstance(raw, dict):
        return list(raw.values())
    if isinstance(raw, str):
        return [{'action': raw}]
    return raw


def action_text(pa):
    if isinstance(pa, str):
        pa = {'action': pa}
    for key in ['action', 'result', 'name', 'text', 'b_result']:
        if pa.get(key):
            return str(pa.get(key)).strip()
    return ""


def normalize_result(act_raw):
    for key, display_name in RESULT_MAP.items():
        if key in act_raw:
            return display_name
    upper = act_raw.upper()
    if '本' in act_raw or 'HR' in upper:
        return "HR"
    if '3' in act_raw or '三塁打' in act_raw:
        return "3BH"
    if '2' in act_raw or '二塁打' in act_raw:
        return "2BH"
    if '安' in act_raw or 'ヒット' in act_raw or 'H' in upper:
        return "H"
    if '三振' in act_raw or upper == 'K':
        return "三振"
    if '四球' in act_raw or '敬遠' in act_raw or upper == 'BB':
        return "四球"
    if '死球' in act_raw or upper == 'HBP':
        return "死球"
    if '犠打' in act_raw or 'バント' in act_raw:
        return "犠打"
    if '犠飛' in act_raw:
        return "犠飛"
    if '失' in act_raw or 'エラー' in act_raw or '野選' in act_raw:
        return "敵失"
    return act_raw


def is_hit_result(norm_act):
    return norm_act in ["H", "2BH", "3BH", "HR"]


def is_ab_result(norm_act):
    return norm_act not in ["四球", "死球", "犠打", "犠飛"]


def is_risp_case(case_info):
    return any(x in str(case_info) for x in ['2', '3', '二', '三', '満'])


def calc_bases(row):
    result = str(row.get('result', ''))
    if result == '1B':
        return 1
    if result == '2B':
        return 2
    if result == '3B':
        return 3
    if result == 'HR':
        return 4
    if result == 'H':
        if str(row.get('is_hr', '0')) == '1':
            return 4
        bases = str(row.get('bases', '1'))
        return int(bases) if bases.isdigit() else 1
    return 0
