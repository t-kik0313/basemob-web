<script setup>
import { computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { teamPrefix } from '../api.js';
defineProps({ data: Object, meta: Object });
const route = useRoute();
const prefix = computed(() => teamPrefix(route));
const expanded = ref(false);
const activeSection = computed(() => {
  if (['games','game'].includes(route.name)) return 'games';
  if (['annual','pitchers'].includes(route.name)) return 'annual_stats_detail';
  if (['regulation','qualitative','register'].includes(route.name)) return 'settings';
  if (['teamstats','schedule','events'].includes(route.name)) return route.name;
  return 'players';
});
watch(() => route.fullPath, () => { expanded.value = false; });
const links = [['players', '選手一覧'], ['teamstats', 'チーム成績'], ['annual_stats_detail', '個人成績'], ['games', '試合結果'], ['schedule', 'スケジュール'], ['events', 'イベント']];
</script>
<template>
  <header class="site-header">
    <RouterLink :to="prefix + '/players'" class="brand">{{ data.team_name || 'BaseMob' }}</RouterLink>
    <nav aria-label="メインメニュー">
      <template v-for="[path, label] in links" :key="path">
        <RouterLink v-if="meta.logged_in || ['schedule', 'events'].includes(path)" :to="prefix + '/' + path" :class="{'section-active':activeSection === path}">{{ label }}</RouterLink>
      </template>
      <a v-if="meta.logged_in" :href="data.score_entry_url" target="_blank" rel="noopener noreferrer">成績入力 ↗</a>
      <button v-if="meta.logged_in" type="button" :class="{'section-active':activeSection === 'settings'}" :aria-expanded="expanded" @click="expanded = !expanded">設定</button>
    </nav>
    <nav v-if="expanded && meta.logged_in" aria-label="設定">
      <RouterLink :to="prefix + '/register_player'" @click="expanded = false">選手登録</RouterLink>
      <RouterLink :to="prefix + '/admin/qualitative_abilities'" @click="expanded = false">特殊能力設定</RouterLink>
      <RouterLink :to="prefix + '/admin/regulation'" @click="expanded = false">規定打席</RouterLink>
    </nav>
  </header>
</template>
