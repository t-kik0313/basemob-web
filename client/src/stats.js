export const number = value => Number(value) || 0;
export function rate(value) { const n = number(value); return n.toFixed(3).replace(/^0\./, '.'); }
export const ratio = (hits, atBats) => atBats > 0 ? hits / atBats : 0;
export const abilityFields = [['meet', 'ミート', 'meet_val'], ['power', 'パワー', 'power_val'], ['speed', '走力', 'speed_val'], ['arm', '肩力', 'arm_val'], ['defense', '守備力', 'defense_val'], ['catching', '捕球', 'catch_val']];
export const specialFields = [['t_pull', 'プルヒッター'], ['t_chancemaker', 'チャンスメーカー'], ['t_nagashi', '流し打ち'], ['t_koukaku', '広角打法'], ['t_firststrike', '初球○'], ['t_vsace', '対エース○'], ['t_nebari', '粘り打ち'], ['t_bat4', '4番○'], ['t_katame', '固め打ち'], ['t_infield', '内野安打○'], ['t_manrui', '満塁男'], ['t_bunt', 'バント○'], ['t_sayonara', 'サヨナラ男']];
export function abilityRank(value) { const n = number(value); return n >= 90 ? 'S' : n >= 80 ? 'A' : n >= 70 ? 'B' : n >= 60 ? 'C' : n >= 50 ? 'D' : n >= 40 ? 'E' : n >= 20 ? 'F' : 'G'; }
const pairs = items => items.map(([key, label, format]) => ({ key, label, format }));
export const battingColumns = pairs([
  ['name', '選手'], ['games', '試合数'], ['avg', '打率', rate], ['pa', '打席'], ['ab', '打数'], ['hits', '安打'],
  ['hr', '本塁打'], ['rbi', '打点'], ['runs', '得点'], ['sb', '盗塁'], ['obp', '出塁率', rate], ['slg', '長打率', rate],
  ['risp_avg', '得点圏打率', rate], ['ops', 'OPS', rate], ['doubles', '二塁打'], ['triples', '三塁打'],
  ['so', '三振'], ['bb', '四球'], ['hbp', '死球'], ['sh', '犠打'], ['sf', '犠飛'], ['gidp', '併殺打'], ['errors', '敵失'], ['fielding_errors', '失策'],
]);
export const historyColumns = pairs([
  ['year', '年度'], ['games', '試合数'], ['batting_average', '打率', rate], ['plate_apperances', '打席'], ['at_bats', '打数'],
  ['hits', '安打'], ['homeruns', '本塁打'], ['runs_batted_in', '打点'], ['scores', '得点'], ['stolen_bases', '盗塁'],
  ['obp', '出塁率', rate], ['slg', '長打率', rate], ['risp_avg', '得点圏打率', (v, r) => number(r.year) <= 2023 ? '－' : rate(v)],
  ['OPS', 'OPS', rate], ['doubles', '二塁打'], ['triples', '三塁打'], ['strike_outs', '三振'], ['bb', '四球'], ['hbp', '死球'],
  ['sacrifice_bants', '犠打'], ['sacrifice_flies', '犠飛'], ['double_plays', '併殺打'], ['errors', '失策'],
]);
export const teamColumns = pairs([['year', '年度'], ['games', '試合数'], ['wins', '勝'], ['losses', '敗'], ['draws', '分'], ['win_pct', '勝率', rate], ['runs', '得点'], ['runs_allowed', '失点'], ['avg', '打率', rate], ['hr', '本塁打'], ['sb', '盗塁'], ['era', '防御率', v => number(v).toFixed(2)]]);
export const pitcherColumns = pairs([['name', '投手'], ['games', '登板'], ['wins', '勝'], ['losses', '敗'], ['saves', 'セーブ'], ['cg', '完投'], ['sho', '完封'], ['display_innings', '投球回'], ['hits', '被安打'], ['hr', '被本塁打'], ['bb', '四球'], ['hbp', '死球'], ['so', '奪三振'], ['runs', '失点'], ['er', '自責点'], ['calc_whip', 'WHIP', v => number(v).toFixed(2)], ['calc_era', '防御率', v => number(v).toFixed(2)], ['calc_k_bb', 'K/BB', v => number(v).toFixed(2)]]);
export const meetingColumns = pairs([['name', '名前'], ['record_date', '測定日'], ['throw_distance', '遠投'], ['batting_distance', '飛距離'], ['run_short', '短距離', v => v == null ? '—' : number(v).toFixed(2)], ['run_long', '長距離', v => v == null ? '—' : number(v).toFixed(2)], ['pitch_speed', '球速'], ['memo', 'メモ']]);
export const plateColumns = pairs([['game_date', '日付'], ['game_id', '試合'], ['game_type', '区分', v => ({ official: '公式戦', practice: '練習試合' })[v] || v], ['batting_order', '打順'], ['result', '結果'], ['direction', '打球方向'], ['runner', '走者'], ['strikes', 'ストライク'], ['stadium', '球場'], ['advancing_runner', '進塁', v => String(v) === '1' ? '○' : ''], ['vs_left', '対左', v => String(v) === '1' ? '○' : '']]);

const hits = new Set(['H', '1B', '2B', '3B', 'HR', '単打', '2BH', '3BH', '本塁打']);
const atBats = new Set([...hits, 'O', 'E', 'FC', 'K', 'ゴロ', 'フライ', 'ライナー', '三振', '失策出塁', '敵失', '野手選択', '併殺打']);
const risp = new Set(['2塁', '3塁', '1,2塁', '1,3塁', '2,3塁', '満塁', '2', '3', '1.2', '1.3', '2.3', 'F']);
export function plateSummary(records = [], player = {}) {
  const left = String(player.pitch_bat || '').includes('左打');
  const pull = new Set(left ? ['3', '4', '9', '一', '二', '右'] : ['5', '6', '7', '三', '遊', '左']);
  const push = new Set(left ? ['5', '6', '7', '三', '遊', '左'] : ['3', '4', '9', '一', '二', '右']);
  const groups = [
    ['全体', () => true], ['左方向', r => ['5','6','7','三','遊','左'].includes(r.direction)], ['中方向', r => ['1','2','8','投','捕','中'].includes(r.direction)], ['右方向', r => ['3','4','9','一','二','右'].includes(r.direction)], ['引張', r => pull.has(r.direction)], ['流し', r => push.has(r.direction)],
    ['無走者', r => ['なし', '0'].includes(r.runner)], ['満塁', r => ['満塁', 'F'].includes(r.runner)], ...[['1','1塁'],['2','2塁'],['3','3塁'],['1.2','1,2塁'],['1.3','1,3塁'],['2.3','2,3塁']].map(([code,label]) => [label,r => [code,label].includes(r.runner)]),
    ['得点圏', r => risp.has(r.runner)], ['非得点圏', r => !risp.has(r.runner)],
    ['0スト', r => r.strikes === '0'], ['2スト', r => r.strikes === '2'],
    ['公式戦', r => r.is_official === '1' || r.game_type === 'official'], ['対左', r => r.vs_left === '1'],
    ['4番', r => r.is_4th_bat === '1' || r.batting_order === '4'],
    ...[1, 2, 3, 4, 5].map(n => [`球場${n}`, r => r.stadium === String(n)]),
  ];
  const normalized = records.map(row => Object.fromEntries(Object.entries(row).map(([key, value]) => [key, String(value ?? '').replaceAll('.0', '')])));
  return groups.map(([name, filter]) => {
    const eligible = normalized.filter(r => atBats.has(r.result) && filter(r));
    const h = eligible.filter(r => hits.has(r.result)).length;
    return { name, ab: eligible.length, hits: h, avg: ratio(h, eligible.length) };
  });
}

export function multiHitSummary(records = []) {
  const games = new Map();
  for (const row of records) if (hits.has(String(row.result))) { const key = row.game_date + '_' + row.game_id; games.set(key, (games.get(key) || 0) + 1); }
  const multiple = [...games.values()].filter(count => count >= 2).length;
  return { games: games.size, multiple, avg: ratio(multiple, games.size) };
}
export function difference(summary, name) {
  const all = summary.find(row => row.name === '全体'); const group = summary.find(row => row.name === name);
  if (!all?.ab || !group?.ab) return '—';
  const value = group.avg - all.avg;
  return (value >= 0 ? '+' : '-') + rate(Math.abs(value));
}
