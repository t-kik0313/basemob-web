import { afterEach, describe, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createRouter, createMemoryHistory } from 'vue-router';
import AttendanceForm from './AttendanceForm.vue';
import EventsView from '../views/EventsView.vue';
import ScheduleView from '../views/ScheduleView.vue';
import DataTable from './DataTable.vue';
import { dateWindow } from '../scheduling/dates.js';

afterEach(() => vi.unstubAllGlobals());
async function router() {
  const instance = createRouter({ history: createMemoryHistory(), routes: [{path:'/t/:teamSlug/:screen',component:{template:'<div />'}}] });
  await instance.push('/t/demo/events'); await instance.isReady(); return instance;
}
describe('Vue の出欠・イベント管理', () => {
  it('既存回答を読み込み、メンバーと未定期日を JSON 保存用に通知する', async () => {
    const wrapper = mount(AttendanceForm, { props: {dates:['2026-10-25'],people:[{id:'1',name:'選手A'}],answers:{'2026-10-25':{'1':{status:'pending',by:'2026-10-20'}}}} });
    await wrapper.find('select').setValue('1');
    expect(wrapper.find('input[type=date]').element.value).toBe('2026-10-20');
    await wrapper.find('form').trigger('submit');
    expect(wrapper.emitted('save')[0][0]).toEqual({person_id:'1',answers:{'2026-10-25':{status:'pending',by:'2026-10-20'}}});
    wrapper.unmount();
  });
  it('イベントの作成・編集がリアクティブな API データを扱える', async () => {
    const saved = {events:{aabb0011:{name:'練習',place:'球場',dates:[dateWindow().today],answers:{},confirmed:false}},people:[]};
    const fetchMock = vi.fn().mockResolvedValue({ok:true,json:async()=>saved}); vi.stubGlobal('fetch',fetchMock);
    const wrapper = mount(EventsView,{props:{data:{logged_in:true}},global:{plugins:[await router()]}});
    await flushPromises();
    await wrapper.findAll('button').find(button=>button.text()==='編集').trigger('click');
    expect(wrapper.find('input').element.value).toBe('練習');
    await wrapper.find('input').setValue('懇親会'); await wrapper.find('form').trigger('submit'); await flushPromises();
    expect(fetchMock.mock.calls[1][0]).toBe('/t/demo/api/events');
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toMatchObject({action:'update',id:'aabb0011',event:{name:'懇親会'}});
    wrapper.unmount();
  });
  it('試合カードを編集・保存し、画面終了時に通信を中断する', async () => {
    const iso = dateWindow().today;
    const saved = {added:[iso],removed:[],people:[],answers:{},games:{[iso]:{slot:'pm',opponent:'対戦チーム',lineup:Array.from({length:10},()=>({n:'選手',p:'投'}))}}};
    const fetchMock = vi.fn().mockResolvedValue({ok:true,json:async()=>saved}); vi.stubGlobal('fetch',fetchMock);
    const wrapper = mount(ScheduleView,{props:{data:{logged_in:true}},global:{plugins:[await router()]}});
    await flushPromises();
    await wrapper.findAll('button').find(button=>button.text()==='試合を編集').trigger('click');
    const form = wrapper.findAll('form').find(form=>form.text().includes('試合カード'));
    await form.trigger('submit'); await flushPromises();
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toMatchObject({action:'game',iso,game:{slot:'pm',opponent:'対戦チーム'}});
    const signal=fetchMock.mock.calls[0][1].signal;wrapper.unmount();expect(signal.aborted).toBe(true);
  });
  it('データ内の HTML を実行せず文字として表示する', () => {
    const wrapper=mount(DataTable,{props:{rows:[{name:'<img src=x onerror=alert(1)>'}],columns:[{key:'name',label:'名前'}]}});
    expect(wrapper.find('img').exists()).toBe(false);expect(wrapper.text()).toContain('<img src=x onerror=alert(1)>');wrapper.unmount();
  });
});
