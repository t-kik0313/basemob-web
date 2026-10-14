import { defineStore } from 'pinia';
import { ref, shallowRef } from 'vue';
import { fetchJson, screenApi } from '../api.js';

export const useScreenStore = defineStore('screen', () => {
  const payload = shallowRef(null);
  const loading = ref(false);
  const error = ref('');
  let controller;
  let version = 0;
  async function load(route) {
    const current = ++version;
    controller?.abort();
    controller = new AbortController();
    loading.value = true;
    error.value = '';
    payload.value = null;
    try {
      const result = await fetchJson(screenApi(route), { signal: controller.signal });
      if (current === version) payload.value = result;
    } catch (exception) {
      if (current === version && exception.name !== 'AbortError') error.value = exception.message;
    } finally {
      if (current === version) loading.value = false;
    }
  }
  return { payload, loading, error, load };
});
