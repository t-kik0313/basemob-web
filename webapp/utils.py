import numpy as np
import pandas as pd


def numpy_encoder(obj):
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def safe_float(val, default=0.0):
    try:
        if pd.isna(val) or str(val).strip() == "":
            return default
        return float(val)
    except Exception:
        return default


def safe_int(val, default=0):
    try:
        if pd.isna(val) or str(val).strip() == "":
            return default
        return int(float(val))
    except Exception:
        return default


def sort_int(val, empty=999):
    if val is None or str(val).strip() == "":
        return empty
    try:
        return int(val)
    except (ValueError, TypeError):
        return empty


def safe_div(num, den):
    return float(num) / float(den) if float(den) > 0 else 0.0


def calc_t_score(val, mean, std, invert=False):
    if std == 0 or pd.isna(val) or val == "":
        return 50.0
    val = float(val)
    if invert:
        return 50.0 + 10.0 * (mean - val) / std
    return 50.0 + 10.0 * (val - mean) / std


def get_nested_int(player, stats_box, *keys):
    for key in keys:
        val = player.get(key, stats_box.get(key) if stats_box else None)
        if val not in [None, ""]:
            try:
                return int(float(val))
            except Exception:
                pass
    return 0
