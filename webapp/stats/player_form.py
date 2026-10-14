def build_form_summary(records, annual_h, annual_ab):
    # --- 月別データと直近5試合データの自動計算 ---
    monthly_stats = {str(m).zfill(2): {'ab': 0, 'h': 0} for m in range(1, 13)}
    hit_results = ['H', '1B', '2B', '3B', 'HR', '単打', '2BH', '3BH', '本塁打']
    ab_results = ['H', '1B', '2B', '3B', 'HR', 'O', 'E', 'FC', 'K', '単打', '2BH', '3BH', '本塁打', 'ゴロ', 'フライ', 'ライナー', '三振', '失策出塁', '野手選択', '併殺']

    games_summary = {}
    for r in records:
        date_str = r['game_date']
        if len(date_str) >= 10:
            month_str = date_str[5:7]
            res_str = r['result']
            is_ab = res_str in ab_results
            is_h = res_str in hit_results

            if date_str not in games_summary:
                games_summary[date_str] = {'ab': 0, 'h': 0}

            if is_ab:
                games_summary[date_str]['ab'] += 1
                if month_str in monthly_stats:
                    monthly_stats[month_str]['ab'] += 1
                if is_h:
                    games_summary[date_str]['h'] += 1
                    if month_str in monthly_stats:
                        monthly_stats[month_str]['h'] += 1

    monthly_avg_data = []
    for m in range(1, 13):
        m_str = str(m).zfill(2)
        ab = monthly_stats[m_str]['ab']
        h = monthly_stats[m_str]['h']
        if ab > 0:
            monthly_avg_data.append(round(h / ab, 3))
        else:
            monthly_avg_data.append("null")

    condition_emoji, condition_color, condition_text = '➖', '#999999', 'データなし'
    recent_5_avg = ".000"
    recent_5_ab = 0
    recent_5_hits = 0

    sorted_dates = sorted(games_summary.keys(), reverse=True)
    recent_5_dates = sorted_dates[:5]
    if recent_5_dates:
        recent_5_ab = sum([games_summary[d]['ab'] for d in recent_5_dates])
        recent_5_hits = sum([games_summary[d]['h'] for d in recent_5_dates])

        if recent_5_ab > 0:
            recent_avg_val = recent_5_hits / recent_5_ab
            recent_5_avg = f".{'{:.3f}'.format(recent_avg_val)[2:]}"

            if recent_avg_val >= 0.400:
                condition_emoji, condition_color, condition_text = '🔥', '#e60000', '絶好調'
            elif recent_avg_val >= 0.300:
                condition_emoji, condition_color, condition_text = '☀️', '#ff8c00', '好調'
            elif recent_avg_val >= 0.200:
                condition_emoji, condition_color, condition_text = '☁️', '#666666', '普通'
            elif recent_avg_val >= 0.100:
                condition_emoji, condition_color, condition_text = '☔', '#004d99', '不調'
            else:
                condition_emoji, condition_color, condition_text = '🥶', '#6a0dad', '絶不調'

    monthly_json_str = "[" + ", ".join(map(str, monthly_avg_data)) + "]"

    # 🌟 打率の計算
    annual_avg_val = annual_h / annual_ab if annual_ab > 0 else 0.0
    annual_avg_str = f".{'{:.3f}'.format(annual_avg_val)[2:]}" if annual_avg_val < 1 else '{:.3f}'.format(annual_avg_val)
    return {
        "annual_avg": annual_avg_str,
        "condition_emoji": condition_emoji,
        "condition_color": condition_color,
        "condition_text": condition_text,
        "recent_5_avg": recent_5_avg,
        "recent_5_ab": recent_5_ab,
        "recent_5_hits": recent_5_hits,
        "monthly_avg_data": monthly_json_str,
    }
