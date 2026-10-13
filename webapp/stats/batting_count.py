import numpy as np
import pandas as pd
from webapp.utils import safe_div


def _calc_bases(pdf):
    result = pdf['result'].astype(str).to_numpy()
    bases = pdf['bases'].astype(str).to_numpy() if 'bases' in pdf.columns else np.full(len(pdf), '1')
    is_hr = pdf['is_hr'].astype(str).to_numpy() if 'is_hr' in pdf.columns else np.full(len(pdf), '0')
    out = np.zeros(len(pdf), dtype=np.int64)
    out[result == '1B'] = 1
    out[result == '2B'] = 2
    out[result == '3B'] = 3
    out[result == 'HR'] = 4
    hits = result == 'H'
    if hits.any():
        vals = np.ones(int(hits.sum()), dtype=np.int64)
        for i, (base, hr) in enumerate(zip(bases[hits], is_hr[hits])):
            if hr == '1':
                vals[i] = 4
            elif base.isdigit():
                vals[i] = int(base)
        out[hits] = vals
    return out


def batting_count(pdf):
    if pdf is None or pdf.empty:
        pdf = pd.DataFrame()
        p_games_count = 0
    else:
        pdf = pdf.copy()
        dup_cols = [c for c in ['game_date', 'game_id'] if c in pdf.columns]
        p_games_count = pdf.drop_duplicates(subset=dup_cols).shape[0] if dup_cols else pdf.shape[0]
        pdf['calc_bases'] = _calc_bases(pdf)

    hit_results = ['H', '1B', '2B', '3B', 'HR']
    ab_results = hit_results + ['O', 'E', 'FC', 'K']

    pa = len(pdf)
    ab_df = pdf[pdf['result'].isin(ab_results)]
    ab = len(ab_df)

    hits = len(pdf[pdf['calc_bases'] > 0]) if not pdf.empty else 0
    hrs = len(pdf[pdf['calc_bases'] == 4]) if not pdf.empty else 0
    total_bases = int(pdf['calc_bases'].sum()) if not pdf.empty else 0

    bb = len(pdf[pdf['result'].isin(['B', 'BB', 'HBP'])]) 
    sf = len(pdf[pdf['result'] == 'SF']) 
    sh = len(pdf[pdf['result'] == 'SH']) 
    so = len(pdf[pdf['result'] == 'K']) 

    sb = int(pd.to_numeric(pdf.get('sb', 0), errors='coerce').fillna(0).sum()) if not pdf.empty else 0
    runs = int(pd.to_numeric(pdf.get('runs', 0), errors='coerce').fillna(0).sum()) if not pdf.empty else 0
    rbi = int(pd.to_numeric(pdf.get('rbi', 0), errors='coerce').fillna(0).sum()) if not pdf.empty else 0
    errors = int(pd.to_numeric(pdf.get('errors', 0), errors='coerce').fillna(0).sum()) if not pdf.empty else 0
    gidp = int(pd.to_numeric(pdf.get('gidp', 0), errors='coerce').fillna(0).sum()) if not pdf.empty else 0

    avg = safe_div(hits, ab)
    slg = safe_div(total_bases, ab)
    obp = safe_div(hits + bb, pa) 
    return {
        "pdf": pdf,
        "p_games_count": p_games_count,
        "pa": pa,
        "ab": ab,
        "hits": hits,
        "hrs": hrs,
        "bb": bb,
        "sf": sf,
        "sh": sh,
        "so": so,
        "sb": sb,
        "runs": runs,
        "rbi": rbi,
        "errors": errors,
        "gidp": gidp,
        "avg": avg,
        "slg": slg,
        "obp": obp,
        "ab_results": ab_results,
    }
