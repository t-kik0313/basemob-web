import { onBeforeUnmount, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { fetchJson, teamPrefix } from '../api.js';
import { useScreenStore } from '../stores/screen.js';

export function useSave() {
  const route = useRoute();
  const router = useRouter();
  const store = useScreenStore();
  const busy = ref(false);
  const error = ref('');
  const message = ref('');
  let controller;
  onBeforeUnmount(() => controller?.abort());
  async function save(path, body, json = false) {
    if (busy.value) return;
    busy.value = true;
    error.value = '';
    message.value = '';
    controller = new AbortController();
    try {
      const result = await fetchJson(teamPrefix(route) + path, {
        method: 'POST', signal: controller.signal,
        body: json ? JSON.stringify(body) : body,
        headers: json ? { 'Content-Type': 'application/json' } : {},
      });
      if (result.redirect) {
        const url = new URL(result.redirect, window.location.origin);
        if (url.origin !== window.location.origin) throw new Error('移動先を確認してください。');
        const sameScreen = route.fullPath === url.pathname + url.search;
        await router.push(url.pathname + url.search);
        if (sameScreen) await store.load(route);
      } else if (result.view) {
        store.payload = result;
        if (result.data.error) error.value = result.data.error;
      } else message.value = '保存しました。';
      return result;
    } catch (exception) {
      if (exception.name !== 'AbortError') error.value = exception.message;
    } finally { busy.value = false; }
  }
  return { busy, error, message, save };
}
