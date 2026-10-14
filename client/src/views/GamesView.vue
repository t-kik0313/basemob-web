<script setup>
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { teamPrefix, staticImage } from '../api.js';
const props = defineProps({ data: Object });
const route = useRoute(); const router = useRouter();
const year = ref(route.query.year || props.data.selected_year || '');
const prefix = computed(() => teamPrefix(route));
function filter() { router.push({ path: route.path, query: year.value ? { year: year.value } : {} }); }
</script>
<template>
  <section class="panel"><h1>試合結果一覧</h1>
    <form class="filters" @submit.prevent="filter"><label>年度 <input v-model="year" name="year" type="number" placeholder="すべて"></label><button>絞り込む</button><RouterLink :to="route.path">クリア</RouterLink></form>
    <div class="cards"><article v-for="game in data.games" :key="game.id" class="day-card">
      <RouterLink :to="prefix + '/game/' + encodeURIComponent(game.id)"><h2>{{ game.date }}　vs {{ game.opponent }}</h2><p>{{ game.scoreMy }} − {{ game.scoreOpp }}　{{ {W:'勝利',L:'敗戦',D:'引分'}[game.result] || game.result }}</p></RouterLink>
      <p>{{ game.gameType }}　{{ game.stadium }}</p>
      <img v-if="game.scoreboard_image" :src="staticImage(game.scoreboard_image)" alt="スコアボード" class="media">
      <a v-if="game.youtube_url" :href="game.youtube_url" target="_blank" rel="noopener noreferrer">YouTube で見る ↗</a>
    </article></div><p v-if="!data.games?.length" class="note">試合データがありません。</p>
  </section>
</template>
