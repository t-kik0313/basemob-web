import { parseDate, holidayMap } from '../../scheduling/dates.js';
export function dayLabel(iso) {
  const date=parseDate(iso); const holiday=holidayMap(date.getFullYear()).get(iso);
  return {short:`${date.getMonth()+1}/${date.getDate()}`,weekday:['日','月','火','水','木','金','土'][date.getDay()],holiday,kind:holiday?'holiday':date.getDay()===0?'sun':date.getDay()===6?'sat':'weekday'};
}
export const positionColors = {'投':'#ff7eae','捕':'#5ec8f5','一':'#ffe14a','二':'#ffe14a','三':'#ffe14a','遊':'#ffe14a','左':'#7ed957','中':'#7ed957','右':'#7ed957','DH':'#ffb020'};
