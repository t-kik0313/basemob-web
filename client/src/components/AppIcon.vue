<script setup>
import { computed } from 'vue';
const props = defineProps({ name: { type: String, default: 'clipboard' } });
// Shared SVG symbols stay local and inherit the surrounding text color.
const symbols = {
  users: ['M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2', 'M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8', 'M22 21v-2a4 4 0 0 0-3-3.87', 'M16 3.13a4 4 0 0 1 0 7.75'],
  user: ['M20 21v-2a7 7 0 0 0-14 0v2', 'M13 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8'],
  'user-plus': ['M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2', 'M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8', 'M20 8v6m-3-3h6'],
  chart: ['M3 3v18h18', 'M7 15v-4m5 4V7m5 8V4'],
  trophy: ['M8 3h8v5a4 4 0 0 1-8 0V3Z', 'M8 5H4v2a4 4 0 0 0 4 4m8-6h4v2a4 4 0 0 1-4 4', 'M12 12v6m-4 3h8m-7-3h6v3H9v-3Z'],
  calendar: ['M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z', 'M16 2v4M8 2v4M3 10h18', 'M8 14h2m4 0h2m-8 4h2'],
  clipboard: ['M9 4H5v17h14V4h-4', 'M9 2h6v4H9V2Z', 'M8 11h8m-8 4h8'],
  settings: ['M12 19a7 7 0 1 0 0-14 7 7 0 0 0 0 14', 'M12 2v3m0 14v3M2 12h3m14 0h3M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2', 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6'],
  alert: ['m12 3 10 18H2L12 3Z', 'M12 9v5m0 3h.01'],
  edit: ['m16 3 5 5-12 12-6 1 1-6L16 3Z', 'm13 6 5 5'],
  save: ['M3 3h14l4 4v14H3V3Z', 'M7 3v6h10V3M7 21v-8h10v8'],
  trash: ['M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15', 'M10 10v7m4-7v7'],
  plus: ['M12 5v14M5 12h14'],
  check: ['m5 12 4 4L19 6'],
  close: ['m6 6 12 12M6 18 18 6'],
  search: ['M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13', 'm16 16 5 5'],
  filter: ['M3 4h18l-7 8v7l-4 2v-9L3 4Z'],
  history: ['M3 10a9 9 0 1 1 2 8M3 3v7h7', 'M12 7v5l3 2'],
  sparkles: ['m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z', 'M21 2v4m-2-2h4'],
  ball: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20', 'M6 4a12 12 0 0 1 0 16M18 4a12 12 0 0 0 0 16'],
  location: ['M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z', 'M12 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6'],
  image: ['M3 3h18v18H3V3Z', 'M8 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4', 'm3 17 5-5 4 4 4-5 5 6'],
  video: ['M3 5h13v14H3V5Z', 'm16 10 5-3v10l-5-3'],
  external: ['M14 3h7v7m0-7L10 14', 'M10 3H3v18h18v-7'],
  'arrow-left': ['M20 12H4m6-6-6 6 6 6'],
  refresh: ['M3 10a9 9 0 0 1 15-6l3 3M21 3v4h-4M21 14a9 9 0 0 1-15 6l-3-3M3 21v-4h4'],
};
const paths = computed(() => symbols[props.name] || symbols.clipboard);
</script>
<template>
  <svg class="app-icon" :data-icon="name" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path v-for="(path,index) in paths" :key="index" :d="path" /></svg>
</template>
