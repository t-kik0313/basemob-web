PLATE_RESULT_MAP = {
    "単打": "H", "2塁打": "2BH", "3塁打": "3BH", "本塁打": "HR",
    "ゴロ": "ゴロ", "フライ": "フライ", "ライナー": "ライナー",
    "三振": "三振", "四球": "四球", "死球": "死球",
    "犠打": "犠打", "犠飛": "犠飛", "失策出塁": "敵失", "野手選択": "野選"
}


def iter_numbered_games():
    """Yield (game number, document, data) in date order. Same-day games stay unique."""
    from webapp.tenant import games_ref

    docs = list(games_ref().stream())
    docs.sort(key=lambda doc: (str((doc.to_dict() or {}).get('date') or ''), doc.id))
    for number, doc in enumerate(docs, start=1):
        yield number, doc, doc.to_dict() or {}


def _stolen_bases(player_row):
    stats = player_row.get('stats') or {}
    if not isinstance(stats, dict):
        stats = {}
    for key in ('SB', 'sb', 'stolen_bases', 'steal'):
        value = player_row.get(key, stats.get(key))
        if value in (None, ''):
            continue
        try:
            return int(float(value))
        except (TypeError, ValueError):
            continue
    return 0


def collect_season(target_name, target_id):
    """Plate rows and stolen bases for one player, from the same games as 今年度個人成績."""
    records = []
    stolen = 0
    target_name = str(target_name or '').replace(" ", "").replace("　", "")
    target_id = str(target_id or '')
    try:
        for number, _doc, g_data in iter_numbered_games():
            game_date = g_data.get('date', '不明')
            for p in g_data.get('results') or []:
                p_name = str(p.get('name', '')).replace(" ", "").replace("　", "")
                p_id = str(p.get('player_id', p.get('id', '')))
                name_match = target_name and p_name and (target_name in p_name or p_name in target_name)
                id_match = target_id and p_id and target_id == p_id
                if name_match or id_match:
                    extend_plate_records(records, p, g_data, game_date, number, PLATE_RESULT_MAP)
                    stolen += _stolen_bases(p)
    except Exception as e:
        print(f"❌ 打席データ取得エラー: {e}")
    return records, stolen


def collect_plate_records(target_name, target_id):
    records, _stolen = collect_season(target_name, target_id)
    return records


def extend_plate_records(records, p, g_data, game_date, game_id, RESULT_MAP):
    # template側の records に合わせるための処理を追加
    b_stats = p.get('stats', {})
    actions_raw = p.get('actions', p.get('atBats', p.get('details', [])))
    if actions_raw:
        actions = list(actions_raw.values()) if isinstance(actions_raw, dict) else actions_raw
        for pa in actions:
            if isinstance(pa, str): pa = {'action': pa}
            act_raw = ""
            for k_test in ['action', 'result', 'name', 'text']:
                if pa.get(k_test):
                    act_raw = str(pa.get(k_test)).strip()
                    break

            norm_act = ""
            for key, display_name in RESULT_MAP.items():
                if key in act_raw: norm_act = display_name; break

            if not norm_act:
                if '本' in act_raw or 'HR' in act_raw.upper(): norm_act = "HR"
                elif '3' in act_raw or '三塁打' in act_raw: norm_act = "3BH"
                elif '2' in act_raw or '二塁打' in act_raw: norm_act = "2BH"
                elif '安' in act_raw or 'ヒット' in act_raw or 'H' in act_raw.upper(): norm_act = "H"
                elif '三振' in act_raw or act_raw.upper() == 'K': norm_act = "三振"
                elif '四球' in act_raw or '敬遠' in act_raw or act_raw.upper() == 'BB': norm_act = "四球"
                elif '死球' in act_raw or act_raw.upper() == 'HBP': norm_act = "死球"
                elif '犠打' in act_raw or 'バント' in act_raw: norm_act = "犠打"
                elif '犠飛' in act_raw: norm_act = "犠飛"
                elif '失' in act_raw or 'エラー' in act_raw or '野選' in act_raw: norm_act = "敵失"
                else: norm_act = act_raw

            direction = str(pa.get('direction', pa.get('hit_direction', pa.get('dir', '')))).strip()
            strikes = pa.get('strikes', pa.get('s', '0'))
            game_type = g_data.get('gameType', '')
            vs_left = pa.get('vs_left')
            if vs_left in (None, ''):
                vs_left = g_data.get('opp_pitcher_arm') == 'L'

            records.append({
                'game_date': game_date,
                'game_id': game_id,
                'game_type': game_type,
                'batting_order': p.get('order', ''),
                'result': norm_act,
                'direction': direction,
                'runner': str(pa.get('case', pa.get('runners', pa.get('base', pa.get('situation', '0'))))),
                'strikes': str(strikes),
                'stadium': g_data.get('stadium', '1'),
                'advancing_runner': '1' if pa.get('advancing_runner') or pa.get('adv') else '0',
                'vs_left': '1' if vs_left in (True, 1, '1', 'true', 'True') else '0',
                'is_4th_bat': '1' if str(p.get('order')) == '4' else '0',
                'is_official': '1' if game_type in ('official', '公式戦') else '0'
            })

            # 以降の集計処理
            is_hit = norm_act in ["H", "2BH", "3BH", "HR"]
            is_ab = norm_act not in ["四球", "死球", "犠打", "犠飛"]
