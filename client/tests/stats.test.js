import { expect, it, vi, afterEach } from 'vitest';
import { plateSummary, rate } from '../src/stats.js';
import { dateWindow, scheduleDays } from '../src/scheduling/dates.js';
afterEach(()=>vi.useRealTimers());
it('安打と打数・得点圏・左右打者の引張方向を維持する',()=>{
  const records=[{result:'H',direction:3,runner:'2',strikes:0},{result:'O',direction:7,runner:0,strikes:2},{result:'BB',direction:3,runner:2}];
  const summary=plateSummary(records,{pitch_bat:'左打'});
  expect(summary.find(row=>row.name==='全体')).toMatchObject({ab:2,hits:1,avg:.5});
  expect(summary.find(row=>row.name==='引張')).toMatchObject({ab:1,hits:1});
  expect(summary.find(row=>row.name==='得点圏')).toMatchObject({ab:1,hits:1});expect(rate(1)).toBe('1.000');expect(rate(.3333)).toBe('.333');
});
it('年跨ぎ・祝日・追加・削除の日程を処理する',()=>{
  vi.useFakeTimers();vi.setSystemTime(new Date(2026,11,14));
  expect(dateWindow()).toEqual({today:'2026-12-14',end:'2027-01-31'});
  const days=scheduleDays({removed:['2027-01-01'],added:['2026-12-15']});
  expect(days).toContain('2026-12-15');expect(days).not.toContain('2027-01-01');expect(days).toContain('2027-01-11');
});
