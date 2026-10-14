import { afterEach, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useScreenStore } from '../../src/stores/screen.js';
import { screenApi } from '../../src/api.js';
import router, { screens } from '../../src/router.js';
afterEach(()=>vi.unstubAllGlobals());
it('全18画面と年度クエリを既存 URL に対応させる',()=>{
  expect(screens).toHaveLength(18);
  expect(router.resolve('/t/demo/player_detail_R1/1').name).toBe('detail');
  expect(screenApi({params:{teamSlug:'demo'},path:'/t/demo/games',fullPath:'/t/demo/games?year=2025#top'})).toBe('/t/demo/api/screens/games?year=2025');
});
it('遅れて届いた前画面のデータで現在画面を上書きしない',async()=>{
  setActivePinia(createPinia());const resolvers=[];
  vi.stubGlobal('fetch',vi.fn(()=>new Promise(resolve=>resolvers.push(resolve))));
  const store=useScreenStore();const route=path=>({params:{teamSlug:'demo'},path,fullPath:path});
  const first=store.load(route('/t/demo/players'));const second=store.load(route('/t/demo/games'));
  resolvers[1]({ok:true,json:async()=>({data:{games:[1]}})});await second;
  resolvers[0]({ok:true,json:async()=>({data:{players:[2]}})});await first;
  expect(store.payload).toEqual({data:{games:[1]}});expect(store.loading).toBe(false);
});
it('認証・API エラーを画面状態として表示する',async()=>{
  setActivePinia(createPinia());vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:401,json:async()=>({error:'認証が必要です'})}));
  const store=useScreenStore();await store.load({params:{teamSlug:'demo'},path:'/t/demo/players',fullPath:'/t/demo/players'});
  expect(store.error).toBe('認証が必要です');expect(store.payload).toBe(null);expect(store.loading).toBe(false);
});
