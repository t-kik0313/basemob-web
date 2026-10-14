<script setup>
import { ref, watch } from 'vue';
import { staticImage } from '../api.js';
const props = defineProps({ path: String, name: String });
const failed = ref(false);
watch(() => props.path, () => { failed.value = false; });
</script>
<template>
  <div v-if="failed || !path" class="image-placeholder" role="img" :aria-label="name">⚾</div>
  <img v-else :src="staticImage(path)" :alt="name" class="player-image" @error="failed = true">
</template>
