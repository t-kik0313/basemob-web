def rate_to_float(val):
    """.327→0.327など、文字列や数値をfloatに変換。空欄や不正値は0.0返却"""
    try:
        if val is None:
            return 0.0
        if isinstance(val, float):
            return val
        if isinstance(val, int):
            return float(val)
        s = str(val).strip()
        if s == '' or s == 'None':
            return 0.0
        if s.startswith('.'):
            return float('0' + s)
        return float(s)
    except Exception:
        return 0.0
