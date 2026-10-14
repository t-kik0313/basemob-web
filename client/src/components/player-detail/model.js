import { abilityFields, number } from '../../stats.js';
export function pointCost(value) {
  if (value <= 4) return value;
  if (value <= 8) return 4 + (value - 4) * 2;
  if (value <= 12) return 12 + (value - 8) * 3;
  if (value <= 16) return 24 + (value - 12) * 4;
  return 0;
}
export function positionGradient(player) {
  const colors = [];
  for (const key of ['pos1','pos2','pos3']) {
    const position = String(player[key] || '').trim();
    const color = [['投','投手'],['捕','捕手'],['一','二','三','遊','内','内野'],['左','中','右','外','外野'],['DH','ＤＨ']].map((items,index)=>items.includes(position)?['#ff7eae','#5ec8f5','#ffe14a','#7ed957','#ffb020'][index]:null).find(Boolean);
    if (color && colors.at(-1) !== color) colors.push(color);
  }
  return colors.length ? `linear-gradient(90deg, ${colors.map((color,index)=>`${color} ${index*100/colors.length}% ${(index+1)*100/colors.length}%`).join(', ')})` : '';
}
export function detailSituations(records = []) {
  const hitResults = new Set(['H','1B','2B','3B','HR','単打','2BH','3BH','本塁打']);
  const abResults = new Set([...hitResults,'O','E','FC','K','ゴロ','フライ','ライナー','三振','失策出塁','野手選択','併殺']);
  const groups = [['left',['5','6','7','三','遊','左'],'direction'],['center',['1','2','8','投','捕','中'],'direction'],['right',['3','4','9','一','二','右'],'direction'],['run0',['なし','0','無','無走者'],'runner'],['run1',['1','1塁'],'runner'],['run2',['2','2塁'],'runner'],['run3',['3','3塁'],'runner'],['run12',['1.2','1,2','1,2塁','1・2','1・2塁'],'runner'],['run13',['1.3','1,3','1,3塁','1・3','1・3塁'],'runner'],['run23',['2.3','2,3','2,3塁','2・3','2・3塁'],'runner'],['runF',['F','満塁','満'],'runner']];
  return Object.fromEntries(groups.map(([key,values,field])=>{
    const eligible=records.filter(row=>abResults.has(String(row.result)) && values.includes(String(row[field] ?? '').replaceAll('.0','').replaceAll('，',',').replaceAll('、',',').trim()));
    const hits=eligible.filter(row=>hitResults.has(String(row.result))).length;
    return [key,{ab:eligible.length,hits,avg:eligible.length?hits/eligible.length:0}];
  }));
}
export const specialRanks = [['chance_rank','チャンス'],['left_rank','対左投手'],['injury','ｹｶﾞしにくさ'],['steal_rank','盗　塁'],['run_rank','走　塁'],['throw','送　球'],[null,''],['recovery','回　復']];
export function baseValues(player) { return Object.fromEntries(abilityFields.map(([key,,valueKey])=>[key,number(player[valueKey] ?? 50) - number(player['plus_'+key])])); }
