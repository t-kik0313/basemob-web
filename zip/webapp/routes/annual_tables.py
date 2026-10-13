def build_annual_tables(player_stats):
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

    stats_list = []
    for name, stats in player_stats.items():
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

    # 打率順にソート
    stats_list.sort(key=lambda x: x['avg'], reverse=True)
    return stats_list, team_total
