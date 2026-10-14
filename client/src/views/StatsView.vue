<script setup>
import { screenIcons } from '../components/icons.js';
import AppIcon from '../components/AppIcon.vue';
import { computed, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { teamPrefix } from '../api.js';
import DataTable from '../components/DataTable.vue';
import { battingColumns, historyColumns, teamColumns, pitcherColumns, meetingColumns, plateColumns, plateSummary, multiHitSummary, difference, rate } from '../stats.js';
const props = defineProps({ data: Object });
const route = useRoute();
const router = useRouter();
const prefix = computed(() => teamPrefix(route));
const filters = reactive({ year: route.query.year || '', game_type: route.query.game_type || '' });
const config = computed(() => ({
  annual: { columns: battingColumns, rows: props.data.stats || [], total: props.data.team_total },
  history: { columns: historyColumns, rows: props.data.history_stats || [], total: { ...props.data.total_stats, year: '通算' } },
  teamstats: { columns: teamColumns, rows: props.data.stats || [] },
  pitchers: { columns: pitcherColumns, rows: props.data.pitchers || [] },
  meeting: { columns: meetingColumns, rows: props.data.records || [] },
  current: { columns: plateColumns, rows: props.data.records || [] },
})[route.name]);
const multi = computed(() => multiHitSummary(props.data.records));
const summary = computed(() => plateSummary(props.data.records, props.data.player));
function filter() { router.push({ path: route.path, query: Object.fromEntries(Object.entries(filters).filter(([, value]) => value)) }); }
</script>
<template>
  <section class="panel">
    <h1><AppIcon :name="screenIcons[route.name]" />{{ data.player?.name }} {{ route.meta.title }}</h1>
    <div v-if="data.player" class="actions"><RouterLink :to="prefix + '/player_detail_R1/' + data.player.player_id" class="button secondary"><AppIcon name="arrow-left" />選手詳細へ戻る</RouterLink></div>
    <form v-if="['history', 'teamstats'].includes(route.name)" class="filters" @submit.prevent="filter">
      <label>年度 <input v-model="filters.year" type="number" placeholder="すべて" name="year"></label>
      <label>区分 <select v-model="filters.game_type" name="game_type"><option value="">すべて</option><option value="official">公式戦</option><option value="practice">練習試合</option></select></label>
      <button type="submit"><AppIcon name="filter" />絞り込む</button><RouterLink :to="route.path"><AppIcon name="refresh" />クリア</RouterLink>
    </form>
    <p v-if="route.name === 'annual'" class="note">規定打席 {{ data.regulation_pa }}。規定到達者、未到達者の順に表示します。</p>
    <section v-if="route.name === 'current'" class="panel">
      <h2>状況別成績</h2>
      <DataTable :rows="summary" :columns="[{key:'name',label:'状況'},{key:'ab',label:'打数'},{key:'hits',label:'安打'},{key:'avg',label:'打率',format:rate}]" />
      <p>得点圏差 {{ difference(summary, '得点圏') }} / 対左差 {{ difference(summary, '対左') }} / マルチヒット {{ multi.multiple }} 試合（安打のある {{ multi.games }} 試合中 {{ rate(multi.avg) }}）</p>
      <h2>打席データ</h2>
    </section>
    <DataTable :rows="config.rows" :columns="config.columns" :empty="route.name === 'history' ? '過去の成績データはありません。' : 'データがありません。'">
      <template #name="{row, value}"><RouterLink v-if="row.id" :to="prefix + '/player_detail_R1/' + row.id">{{ value }}</RouterLink><span v-else>{{ value }}</span></template>
      <template #year="{value}"><RouterLink v-if="route.name === 'teamstats'" :to="{path:prefix + '/games',query:{year:value}}">{{ value }}</RouterLink><span v-else>{{ value }}</span></template>
    </DataTable>
    <template v-if="config.total && config.rows.length"><h2 style="margin-top:20px">{{ route.name === 'history' ? '通算成績' : 'チーム合計' }}</h2><DataTable :rows="[config.total]" :columns="config.columns" /></template>
  </section>
</template>
