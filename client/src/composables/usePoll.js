import { onMounted, onBeforeUnmount, ref } from 'vue';
import { useRoute } from 'vue-router';
import { fetchJson, teamPrefix } from '../api.js';

export function usePoll(path, postPath = path) {
  const route = useRoute();
  const poll = ref({});
  const busy = ref(false);
  const error = ref('');
  const message = ref('');
  const controller = new AbortController();
  let active = true;
  onBeforeUnmount(() => { active = false; controller.abort(); });
  async function request(body) {
    if (busy.value) return;
    busy.value = true;
    error.value = ''; message.value = '';
    try {
      const result = await fetchJson(teamPrefix(route) + (body ? postPath : path), {
        signal: controller.signal,
        ...(body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}),
      });
      if (active) { poll.value = result; if (body) message.value = '保存しました。'; }
      return result;
    } catch (exception) { if (active && exception.name !== 'AbortError') error.value = exception.message; }
    finally { if (active) busy.value = false; }
  }
  onMounted(() => request());
  return { poll, busy, error, message, request };
}
