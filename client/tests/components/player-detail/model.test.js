import { expect, it } from 'vitest';
import { pointCost, detailSituations, positionGradient } from '../../../src/components/player-detail/model.js';
it('元の補正ポイント単価と各段階の境界を維持する',()=>{
  expect([0,4,5,8,9,12,13,16].map(pointCost)).toEqual([0,4,6,12,15,24,28,40]);
});
it('守備位置の順番と連続する同色の整理を維持する',()=>{
  expect(positionGradient({pos1:'投',pos2:'遊',pos3:'二'})).toBe('linear-gradient(90deg, #ff7eae 0% 50%, #ffe14a 50% 100%)');
});
it('球場図の旧表記・走者・安打と打数の条件を維持する',()=>{
  const stats=detailSituations([{result:'H',direction:7,runner:'1、3塁'},{result:'O',direction:'7.0',runner:'無走者'},{result:'BB',direction:7,runner:'1.3'},{result:'併殺',direction:'8',runner:'1.3'}]);
  expect(stats.left).toEqual({ab:2,hits:1,avg:.5});expect(stats.run13).toEqual({ab:2,hits:1,avg:.5});expect(stats.run0).toEqual({ab:1,hits:0,avg:0});
});
