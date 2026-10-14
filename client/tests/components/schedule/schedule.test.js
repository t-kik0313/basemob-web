import { expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import ScheduleBoard from '../../../src/components/schedule/ScheduleBoard.vue';
import ScheduleGameCard from '../../../src/components/schedule/ScheduleGameCard.vue';
import AttendanceForm from '../../../src/components/AttendanceForm.vue';
it('旧ボードの7人判定・午前午後の集計と未回答者を表示する',async()=>{
  const people=Array.from({length:9},(_,index)=>({id:String(index+1),name:`選手${index+1}`}));
  const answers=Object.fromEntries(people.slice(0,7).map(person=>[person.id,{status:'all'}]));
  const wrapper=mount(ScheduleBoard,{props:{dates:['2026-10-17'],today:'2026-10-15',poll:{people,answers:{'2026-10-17':answers}},canEdit:true}});
  expect(wrapper.find('.schedule-pill').text()).toBe('手配候補');expect(wrapper.findAll('.schedule-meter-row strong').map(el=>el.text())).toEqual(['7人','7人']);
  await wrapper.find('.schedule-day-summary').trigger('click');expect(wrapper.find('.schedule-groups').text()).toContain('選手9');
  await wrapper.findAll('button').find(el=>el.text()==='午後に試合を設定').trigger('click');expect(wrapper.emitted('edit')[0]).toEqual(['2026-10-17','pm']);wrapper.unmount();
});
it('ボタン式回答シートで未定期日を保存し、選択を解除できる',async()=>{
  const wrapper=mount(AttendanceForm,{props:{sheet:true,dates:['2026-10-17'],people:[{id:'1',name:'選手A'}],answers:{}}});
  await wrapper.find('select').setValue('1');await wrapper.findAll('button').find(el=>el.text()==='未定').trigger('click');await wrapper.find('input[type=date]').setValue('2026-10-16');await wrapper.find('form').trigger('submit');
  expect(wrapper.emitted('save')[0][0]).toEqual({person_id:'1',answers:{'2026-10-17':{status:'pending',by:'2026-10-16'}}});
  await wrapper.findAll('button').find(el=>el.text()==='未定').trigger('click');expect(wrapper.find('input[type=date]').exists()).toBe(false);wrapper.unmount();
});
it('色付き打順表と調子アイコン、DH 時の10番目の投手表示を復元する',()=>{
  const lineup=Array.from({length:10},(_,index)=>({n:`選手${index+1}`,p:index===9?'投':'DH'}));
  const wrapper=mount(ScheduleGameCard,{props:{iso:'2026-10-17',card:{eventName:'練習試合',slot:'pm',lineup},conditions:{'選手1':'絶好調'}}});
  expect(wrapper.find('.schedule-lineup-row img').attributes('src')).toBe('/static/condition_excellent.png');expect(wrapper.findAll('.schedule-lineup-row > strong')[9].text()).toBe('P');wrapper.unmount();
});
