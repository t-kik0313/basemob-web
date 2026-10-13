import json
import pandas as pd
from webapp.utils import safe_div


def _log_error(message):
    from webapp import app
    app.logger.error(message)


def recent_form(p_data, box):
    pdf = box["pdf"]
    ab_results = box["ab_results"]
    # --- ▼ 月別打率と最近の調子 ▼ ---
    try:
        monthly_data = [None] * 12
        recent_5_avg_str, recent_5_ab, recent_5_hits = ".000", 0, 0
        cond_text, cond_color, cond_emoji = "普通", "#d4af37", "😐"

        if not pdf.empty and 'game_date' in pdf.columns:
            pdf_dates = pdf.copy()
            pdf_dates['game_date_dt'] = pd.to_datetime(pdf_dates['game_date'], errors='coerce')

            for m in range(1, 13):
                m_df = pdf_dates[pdf_dates['game_date_dt'].dt.month == m]
                if not m_df.empty:
                    m_ab = len(m_df[m_df['result'].isin(ab_results)])
                    m_hits = len(m_df[m_df['calc_bases'] > 0])
                    if m_ab > 0: monthly_data[m - 1] = round(safe_div(m_hits, m_ab), 3)

            unique_games = pdf_dates.sort_values('game_date_dt', ascending=False)[['game_date', 'game_id']].drop_duplicates().head(5)
            if not unique_games.empty:
                recent_df = pd.merge(pdf_dates, unique_games, on=['game_date', 'game_id'], how='inner')
                recent_5_ab = len(recent_df[recent_df['result'].isin(ab_results)])
                recent_5_hits = len(recent_df[recent_df['calc_bases'] > 0])

                if recent_5_ab > 0:
                    r_avg = safe_div(recent_5_hits, recent_5_ab)
                    recent_5_avg_str = f"{r_avg:.3f}".replace('0.', '.') if r_avg < 1.0 else "1.000"

                    if r_avg >= 0.350: cond_text, cond_color, cond_emoji = "絶好調", "#ff007f", "😆"
                    elif r_avg >= 0.280: cond_text, cond_color, cond_emoji = "好調", "#e60000", "😃"
                    elif r_avg >= 0.230: cond_text, cond_color, cond_emoji = "普通", "#d4af37", "😐"
                    elif r_avg >= 0.150: cond_text, cond_color, cond_emoji = "不調", "#0073e6", "😨"
                    else: cond_text, cond_color, cond_emoji = "絶不調", "#8a2be2", "😱"

        p_data.update({
            'monthly_avg_data': json.dumps(monthly_data).replace('NaN', 'null'),
            'recent_5_avg': recent_5_avg_str,
            'recent_5_ab': recent_5_ab,
            'recent_5_hits': recent_5_hits,
            'condition_text': cond_text,
            'condition_color': cond_color,
            'condition_emoji': cond_emoji
        })
    except Exception as e: _log_error(f"Error stats: {e}")
