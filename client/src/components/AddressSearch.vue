<script setup>
import { onBeforeUnmount, ref } from 'vue';
const emit = defineEmits(['select']);
const query = ref(''); const results = ref([]); const error = ref(''); const busy = ref(false);
let controller;
onBeforeUnmount(() => controller?.abort());
async function search() {
  controller?.abort(); controller = new AbortController(); busy.value = true; error.value = '';
  try {
    const response = await fetch('https://msearch.gsi.go.jp/address-search/AddressSearch?q=' + encodeURIComponent(query.value), {signal:controller.signal});
    if (!response.ok) throw new Error('住所を検索できませんでした。');
    results.value = await response.json();
  } catch (exception) { if (exception.name !== 'AbortError') error.value = exception.message; }
  finally { busy.value = false; }
}
</script>
<template>
  <div class="panel"><label>住所検索（国土地理院）<input v-model="query" placeholder="球場名・住所"></label><button type="button" :disabled="busy || !query.trim()" @click="search">検索</button>
    <p v-if="error" role="alert">{{ error }}</p><ul><li v-for="(item,index) in results" :key="index"><button type="button" @click="emit('select',item.properties.title); results = []">{{ item.properties.title }}</button></li></ul>
  </div>
</template>
