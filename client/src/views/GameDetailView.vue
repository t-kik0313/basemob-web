<script setup>
import { ref } from 'vue';
import { useRoute } from 'vue-router';
import { staticImage } from '../api.js';
import { useSave } from '../composables/useSave.js';
import DataTable from '../components/DataTable.vue';
import FormStatus from '../components/FormStatus.vue';
defineProps({ data: Object });
const route = useRoute(); const tab = ref('batters');
const {busy,error,message,save} = useSave();
const columns = [['order','打順'],['name','選手名'],['position','守備'],['PA','打席'],['AB','打数'],['H','安打'],['HR','HR'],['RBI','打点'],['RUNS','得点'],['SB','盗塁'],['BH2','2BH'],['BH3','3BH'],['RISP_AB','得点圏打数'],['RISP_H','得点圏安打'],['K','三振'],['BB','四球'],['HBP','死球'],['SAC','犠打'],['SF','犠飛'],['DP','併殺打'],['ERR','敵失'],['defensive_errors','失策']].map(([key,label])=>({key,label}));
const pitcherColumns = [['name','投手'],['display_innings','投球回'],['hits','被安打'],['hr','被本塁打'],['so','奪三振'],['bb','四球'],['hbp','死球'],['runs','失点'],['er','自責点']].map(([key,label])=>({key,label}));
function submit(event, action) { save('/api/actions/game/' + encodeURIComponent(route.params.gameId) + '/' + action, new FormData(event.currentTarget)); }
function upload(event) { if (event.target.files.length) event.target.form.requestSubmit(); }
</script>
<template>
  <section class="panel"><h1>{{ data.game.date }}　vs {{ data.game.opponent }}</h1>
    <h2>{{ data.game.scoreMy }} − {{ data.game.scoreOpp }}</h2><p>{{ data.game.gameType }}　{{ data.game.stadium }}</p>
    <div class="table-scroll"><table><thead><tr><th>チーム</th><th v-for="inning in 9" :key="inning">{{ inning }}</th><th>計</th></tr></thead><tbody><tr><th>{{ data.team_name }}</th><td v-for="inning in 9" :key="inning">{{ data.game.my_scores?.[inning-1] ?? '' }}</td><td>{{ data.game.scoreMy }}</td></tr><tr><th>{{ data.game.opponent }}</th><td v-for="inning in 9" :key="inning">{{ data.game.opp_scores?.[inning-1] ?? '' }}</td><td>{{ data.game.scoreOpp }}</td></tr></tbody></table></div>
    <FormStatus :error="error" :message="message" />
    <img v-if="data.game.scoreboard_image" :src="staticImage(data.game.scoreboard_image)" alt="スコアボード" class="media">
    <form @submit.prevent="submit($event,'scoreboard_image')"><label class="field">スコアボード画像<input name="scoreboard_image" type="file" accept="image/jpeg,image/png,image/webp,image/gif" :disabled="busy" @change="upload"></label><button type="submit" :disabled="busy">画像を保存</button></form>
    <form class="filters" @submit.prevent="submit($event,'youtube')"><label>YouTube URL <input name="youtube_url" :value="data.game.youtube_url" type="url" placeholder="https://..."></label><button type="submit" :disabled="busy">保存</button></form>
    <a v-if="data.game.youtube_url" :href="data.game.youtube_url" target="_blank" rel="noopener noreferrer">YouTube で見る ↗</a>
    <iframe v-if="data.game.youtube_id" :src="'https://www.youtube.com/embed/' + data.game.youtube_id" class="media" title="試合動画" loading="lazy" allowfullscreen />
    <div class="actions"><button :class="{selected:tab==='batters'}" @click="tab='batters'">打者成績</button><button :class="{selected:tab==='pitchers'}" @click="tab='pitchers'">投手成績</button></div>
    <DataTable v-if="tab==='batters'" :rows="data.batters" :columns="columns" empty="打者データがありません。" />
    <DataTable v-else :rows="data.pitchers" :columns="pitcherColumns" empty="投手データがありません。" />
  </section>
</template>
