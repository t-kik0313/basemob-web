<script setup>
import { computed, shallowRef, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useScreenStore } from './stores/screen.js';
import AppNav from './components/AppNav.vue';

function reload() { window.location.reload(); }
const route = useRoute();
const screen = useScreenStore();
const navigation = shallowRef(null);
watch(() => route.params.teamSlug, () => { navigation.value = null; });
watch(() => screen.payload, payload => {
  if (payload) navigation.value = { data: { team_name: payload.data.team_name, score_entry_url: payload.data.score_entry_url }, meta: payload.meta };
});
const ready = computed(() => !screen.loading && Boolean(screen.payload));
watch(() => route.fullPath, () => { if (!route.meta.notFound) screen.load(route); }, { immediate: true });
watch(() => route.meta.title, title => { document.title = title ? `${title} | BaseMob` : 'BaseMob'; }, { immediate: true });
</script>

<template>
  <div class="spa" :class="{'player-detail-shell':route.name === 'detail'}" :data-client-ready="ready ? 'true' : 'false'">
    <AppNav v-if="route.params.teamSlug" :data="navigation?.data || {}" :meta="navigation?.meta || {}" />
    <main>
      <p v-if="screen.loading" class="status" role="status">読み込んでいます。</p>
      <section v-else-if="screen.error" class="error" role="alert">
        <p>{{ screen.error }}</p>
        <button type="button" @click="screen.load(route)">再試行</button>
        <button type="button" @click="reload">再ログイン</button>
      </section>
      <RouterView v-else-if="ready || route.meta.notFound" :key="route.fullPath" v-slot="{ Component }">
        <component :is="Component" :data="screen.payload?.data || {}" :meta="screen.payload?.meta || {}" />
      </RouterView>
    </main>
  </div>
</template>
