import { afterEach, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
import App from '../src/App.vue';
afterEach(()=>vi.unstubAllGlobals());
it('選手詳細を含む画面遷移・読込中・API エラーでもホーム上部のタブを残す',async()=>{
  const router=createRouter({history:createMemoryHistory(),routes:[{path:'/t/:teamSlug/players',name:'players',component:{template:'<div>一覧</div>'}},{path:'/t/:teamSlug/player_detail_R1/:playerId',name:'detail',component:{template:'<div>詳細</div>'}}]});
  await router.push('/t/demo/players');await router.isReady();
  let complete;
  vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce({ok:true,json:async()=>({data:{team_name:'テストチーム',score_entry_url:'https://example.test'},meta:{logged_in:true}})}).mockImplementationOnce(()=>new Promise(resolve=>{complete=resolve;})));
  const wrapper=mount(App,{global:{plugins:[createPinia(),router]}});await flushPromises();
  expect(wrapper.find('header').text()).toContain('テストチーム');expect(wrapper.find('nav').findAll('a')).toHaveLength(7);
  await router.push('/t/demo/player_detail_R1/1');await flushPromises();
  expect(wrapper.classes()).toContain('player-detail-shell');expect(wrapper.find('nav').findAll('a')).toHaveLength(7);expect(wrapper.text()).toContain('読み込んでいます');
  complete({ok:false,status:500,json:async()=>({error:'テストエラー'})});await flushPromises();
  expect(wrapper.find('nav').findAll('a')).toHaveLength(7);expect(wrapper.find('[role=alert]').text()).toContain('テストエラー');wrapper.unmount();
});
