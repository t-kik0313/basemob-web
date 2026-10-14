<script setup>
import AppIcon from '../components/AppIcon.vue';
import { reactive } from 'vue';
import { useRoute } from 'vue-router';
import { useSave } from '../composables/useSave.js';
import FormStatus from '../components/FormStatus.vue';
defineProps({data:Object});
const route = useRoute(); const {busy,error,message,save} = useSave();
const game = reactive({game_date:'',game_id:'',stadium:'1',game_type:'official',batting_order:'sub',fielding_position:'PR',game_sb:0,game_runs:0,game_rbi:0,game_errors:0,game_gidp:0});
const blank = () => ({result:'O',direction:'',runner:'0',strikes:'0',vs_left:false,sayonara:false});
const records = reactive([blank()]);
const results = [['H','安打'],['1B','単打'],['2B','二塁打'],['3B','三塁打'],['HR','本塁打'],['O','アウト'],['E','敵失'],['FC','野選'],['K','三振'],['BB','四球'],['HBP','死球'],['SH','犠打'],['SF','犠飛']];
function submit(event) { save('/api/actions/save_record/'+route.params.playerId,new FormData(event.currentTarget)); }
</script>
<template>
  <section class="panel"><h1><AppIcon name="clipboard" />成績入力 — {{ data.player.name }}</h1><FormStatus :error="error" :message="message" />
    <form @submit.prevent="submit"><div class="form-grid">
      <label class="field">試合日<input v-model="game.game_date" name="game_date" type="date" required></label><label class="field">試合 ID<input v-model="game.game_id" name="game_id" required></label>
      <label class="field">球場形状<select v-model="game.stadium" name="stadium"><option v-for="n in 5" :key="n" :value="String(n)">{{ n }}</option></select></label>
      <label class="field">試合区分<select v-model="game.game_type" name="game_type"><option value="official">公式戦</option><option value="practice">練習試合</option></select></label>
      <label class="field">打順<select v-model="game.batting_order" name="batting_order"><option v-for="n in 9" :key="n" :value="String(n)">{{ n }}番</option><option value="sub">途中出場</option></select></label>
      <label class="field">守備位置<select v-model="game.fielding_position" name="fielding_position"><option v-for="p in ['P','C','1B','2B','3B','SS','LF','CF','RF','DH','PH','PR']" :key="p">{{ p }}</option></select></label>
      <label v-for="[key,label] in [['game_sb','盗塁'],['game_runs','得点'],['game_rbi','打点'],['game_errors','失策'],['game_gidp','併殺打']]" :key="key" class="field">{{ label }}<input v-model.number="game[key]" :name="key" type="number" min="0"></label>
    </div>
    <article v-for="(record,index) in records" :key="index" class="day-card" style="margin-bottom:12px"><h2>{{ index+1 }}打席目</h2><div class="form-grid">
      <label class="field">結果<select v-model="record.result" name="result[]"><option v-for="[key,label] in results" :key="key" :value="key">{{ label }}</option></select></label>
      <label class="field">打球方向<select v-model="record.direction" name="direction[]"><option value="">なし</option><option v-for="[key,label] in [['1','投'],['2','捕'],['3','一'],['4','二'],['5','三'],['6','遊'],['7','左'],['8','中'],['9','右']]" :key="key" :value="key">{{ label }}</option></select></label>
      <label class="field">走者<select v-model="record.runner" name="runner[]"><option v-for="[key,label] in [['0','なし'],['1','1塁'],['2','2塁'],['3','3塁'],['1.2','1・2塁'],['1.3','1・3塁'],['2.3','2・3塁'],['F','満塁']]" :key="key" :value="key">{{ label }}</option></select></label>
      <label class="field">ストライク<select v-model="record.strikes" :name="'s'+(index+1)"><option v-for="n in [0,1,2]" :key="n" :value="String(n)">{{ n }}</option></select></label>
    </div><label><input v-model="record.vs_left" type="checkbox"> 対左</label><input name="vs_left[]" type="hidden" :value="record.vs_left?'1':'0'">　<label><input v-model="record.sayonara" type="checkbox"> サヨナラ</label><input name="sayonara[]" type="hidden" :value="record.sayonara?'1':'0'"></article>
    <div class="actions"><button type="button" class="secondary" @click="records.push(blank())"><AppIcon name="plus" />打席を追加</button><button type="submit" :disabled="busy"><AppIcon name="save" />成績を登録する</button></div></form>
  </section>
</template>
