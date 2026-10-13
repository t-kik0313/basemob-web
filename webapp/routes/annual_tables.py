def _plain_name(value):
    return str(value or '').replace(' ', '').replace('　', '').strip()


def _registered_player(stats, roster_ids, roster_names):
    if not roster_ids and not roster_names:
        return True
    try:
        pid = int(stats.get('id'))
    except (TypeError, ValueError):
        pid = None
    if pid in roster_ids:
        return True
    plain = _plain_name(stats.get('name'))
    if not plain:
        return False
    exact = roster_names.get(plain)
    if exact and len(exact) == 1:
        return True
    found = set()
    for roster_name, ids in roster_names.items():
        if plain in roster_name or roster_name in plain:
            found.update(ids)
    return len(found) == 1


def build_annual_tables(player_stats, regulation_pa=0, roster=None):
    # === 🌟 チーム合計の箱 ===
    team_total = {
        'name': 'チーム合計', 'id': '', 'games': '-', 'pa': 0, 'ab': 0, 'hits': 0, 'hr': 0, 'rbi': 0, 'runs': 0, 'sb': 0,
        'doubles': 0, 'triples': 0,
        'so': 0, 'bb': 0, 'hbp': 0, 'sh': 0, 'sf': 0, 'gidp': 0, 'errors': 0, 'fielding_errors': 0,
        'risp_ab': 0, 'risp_h': 0
    }

    def calc_avg(h, ab): return h / ab if ab > 0 else 0.0
    def calc_obp(h, bb, hbp, ab, sf):
        den = ab + bb + hbp + sf
        return (h + bb + hbp) / den if den > 0 else 0.0
    def calc_slg(h, doubles, triples, hr, ab):
        singles = h - doubles - triples - hr
        tb = singles + (doubles * 2) + (triples * 3) + (hr * 4)
        return tb / ab if ab > 0 else 0.0

    roster_ids = set()
    roster_names = {}
    for player in roster or []:
        try:
            pid = int(player.get('player_id') or player.get('id'))
        except (TypeError, ValueError):
            continue
        roster_ids.add(pid)
        plain = _plain_name(player.get('name'))
        if plain:
            roster_names.setdefault(plain, set()).add(pid)

    stats_list = []
    for name, stats in player_stats.items():
        if roster is not None and not _registered_player(stats, roster_ids, roster_names):
            continue
        for key in ['pa', 'ab', 'hits', 'hr', 'rbi', 'runs', 'sb', 'doubles', 'triples', 'so', 'bb', 'hbp', 'sh', 'sf', 'gidp', 'errors', 'fielding_errors', 'risp_ab', 'risp_h']:
            team_total[key] += stats[key]

        stats['avg'] = calc_avg(stats['hits'], stats['ab'])
        stats['obp'] = calc_obp(stats['hits'], stats['bb'], stats['hbp'], stats['ab'], stats['sf'])
        stats['slg'] = calc_slg(stats['hits'], stats['doubles'], stats['triples'], stats['hr'], stats['ab'])
        stats['ops'] = stats['obp'] + stats['slg']
        stats['risp_avg'] = calc_avg(stats['risp_h'], stats['risp_ab'])
        stats_list.append(stats)

    team_total['avg'] = calc_avg(team_total['hits'], team_total['ab'])
    team_total['obp'] = calc_obp(team_total['hits'], team_total['bb'], team_total['hbp'], team_total['ab'], team_total['sf'])
    team_total['slg'] = calc_slg(team_total['hits'], team_total['doubles'], team_total['triples'], team_total['hr'], team_total['ab'])
    team_total['ops'] = team_total['obp'] + team_total['slg']
    team_total['risp_avg'] = calc_avg(team_total['risp_h'], team_total['risp_ab'])

    # 規定到達を打率の高い順、その下に規定未達を打率の高い順
    line = float(regulation_pa or 0)
    reached = []
    short = []
    for row in stats_list:
        row['qualified'] = line > 0 and row.get('pa', 0) >= line
        (reached if row['qualified'] else short).append(row)
    reached.sort(key=lambda x: x['avg'], reverse=True)
    short.sort(key=lambda x: x['avg'], reverse=True)
    return reached + short, team_total
