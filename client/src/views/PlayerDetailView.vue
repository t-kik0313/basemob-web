<script setup>
import { iconForPath } from '../components/icons.js';
import AppIcon from '../components/AppIcon.vue';
import { computed, reactive, ref } from 'vue';
import { useRoute } from 'vue-router';
import { teamPrefix, staticImage } from '../api.js';
import { useSave } from '../composables/useSave.js';
import FormStatus from '../components/FormStatus.vue';
import AbilitySliders from '../components/player-detail/AbilitySliders.vue';
import FieldRates from '../components/player-detail/FieldRates.vue';
import RecentForm from '../components/player-detail/RecentForm.vue';
import { baseValues, detailSituations, pointCost, positionGradient, specialRanks } from '../components/player-detail/model.js';
import { abilityFields, abilityRank, rate, ratio, number } from '../stats.js';
import '../components/player-detail/legacy.css';
import '../components/player-detail/layout.css';
const props = defineProps({ data: Object });
const route = useRoute(); const prefix = computed(() => teamPrefix(route));
const player = computed(() => props.data.player);
const initialBase = baseValues(props.data.player);
const corrections = reactive(Object.fromEntries(abilityFields.map(([key]) => ['plus_' + key, number(props.data.player['plus_' + key])])));
const editing = ref(false); const {busy,error,message,save} = useSave();
const remaining = computed(() => 40 - number(player.value.age ?? 25) - Object.values(corrections).reduce((total,value)=>total+pointCost(value),0));
const values = computed(() => Object.fromEntries(abilityFields.map(([key])=>[key,initialBase[key]+corrections['plus_'+key]])));
const situations = computed(() => detailSituations(props.data.records));
const firstName = computed(() => {const name=String(player.value.name || '').split(' ')[0];return name.length===2?name[0]+'　'+name[1]:name;});
const gradient = computed(() => positionGradient(player.value));
const dan = computed(() => [1,2,3,4].includes(Number(player.value.dan))?Number(player.value.dan):2);
const skills = computed(() => props.data.active_skills || []);
const batting = computed(() => `率${rate(ratio(props.data.annual_h, props.data.annual_ab))}　${props.data.annual_hr ?? 0}本　${props.data.annual_rbi ?? 0}点　${props.data.annual_sb ?? 0}盗`);
const groups = computed(() => [['','チーム',[['teamstats','チーム成績'],['games','チーム試合結果'],['annual_stats_detail','打者成績一覧'],['pitchers','投手成績'],['pawapuro','パワプロ能力一覧']]],['mine','この選手',[[`current_year_stats/${player.value.player_id}`,'今年度個人成績'],[`player_history/${player.value.player_id}`,'過去成績']]],['meet','記録会',[['record_summary','記録会成績']]]]);
const mobileLinks = computed(() => [[`current_year_stats/${player.value.player_id}`,'今年度個人成績'],['record_summary','記録まとめ'],[`player_history/${player.value.player_id}`,'通算成績'],['pitchers','投手成績'],[`input_form_R1/${player.value.player_id}`,'入力フォーム'],['pawapuro','パワプロ風'],[`edit_player/${player.value.player_id}`,'編集']]);
function changeCorrection(key,value) { const name='plus_'+key; const previous=corrections[name]; if(value>previous && 40-number(player.value.age ?? 25)-Object.entries(corrections).reduce((total,[field,current])=>total+pointCost(field===name?value:current),0)<0)return;corrections[name]=value; }
async function saveAbilities() {const result=await save('/api/update_abilities',{player_id:player.value.player_id,abilities:{...corrections}},true);if(result?.ok)editing.value=false;}
</script>
<template>
  <div class="player-detail-page">
    <FormStatus :error="error" :message="message" />
    <div class="pc-layout">
      <div class="player-detail-container">
        <div class="abilities-frame"><div class="player-card-wrapper">
          <div class="pc-ability-item name-plate" style="top:18px;left:18px;width:190px;height:68px;justify-content:center;font-size:3.2rem;font-weight:bold;background:#bcdcfa;color:#000"><span class="name-fill" :style="{backgroundImage:gradient}"/><span class="name-letters">{{ firstName }}</span></div>
          <div style="position:absolute;top:18px;left:215px;width:68px;height:68px;border:1.5px solid #cce0ff"><img :src="'/static/uniform.jpeg'" alt="ユニフォーム" style="width:100%;height:100%;object-fit:contain"></div>
          <div style="position:absolute;top:18px;left:283px;width:65px;height:68px;border:1.5px solid #cce0ff;display:flex;align-items:center;justify-content:center;font-size:2.3rem;font-weight:bold;color:#000">{{ player.number }}</div>
          <div style="position:absolute;top:18px;left:360px;width:170px;height:150px;border:1.5px solid #cce0ff;background:#eee"><img class="detail-player-photo" :src="staticImage(player.image_path)" :alt="player.name" style="width:100%;height:100%;object-fit:cover"></div>
          <div class="pc-ability-item" style="top:95px;left:18px;width:330px;height:58px;background:#fff;color:#000"><div class="pc-label-box pc-label-pos" style="left:8px;width:100px">守備位置</div><span style="margin-left:115px;font-size:2.4rem;font-weight:bold">{{ player.pos1 }}</span><span style="font-size:2rem;font-weight:bold">{{ player.pos2 ? '　'+player.pos2 : '' }}{{ player.pos3 ? '　'+player.pos3 : '' }}</span></div>
          <div class="pc-info-panel" style="top:18px;color:#000"><div class="pc-label-box" style="position:static;width:80px;height:50px;flex-shrink:0">成 績</div><span>{{ batting }}</span></div>
          <div class="pc-info-panel stats-small" style="top:98px;color:#000"><div class="pc-label-box" style="position:static;width:60px;height:40px;flex-shrink:0">性 格</div><span style="margin-right:1em">{{ player.character ?? 'ふつう' }}</span><div class="pc-label-box" style="position:static;width:60px;height:40px;flex-shrink:0">投 打</div><span>{{ player.pitch_bat ?? '右投右打' }}</span></div>
          <div class="pc-ability-item" style="top:165px;left:18px;width:330px;height:70px"><div class="pc-label-box" style="left:8px;width:100px;color:#000">弾　道</div><span class="dan-mark"><img :src="'/static/trajectory/arrow_'+dan+'.png'" alt="弾道"><span class="dan-num">{{ dan }}</span></span></div>
          <div v-for="([key,label],index) in abilityFields" :key="key" class="pc-ability-item" :style="{top:(245+index*80)+'px',left:'18px',width:'330px',height:'70px'}"><div class="pc-label-box" style="left:8px;width:100px;color:#000">{{ label }}</div><span class="pc-rank-shadow" :class="'rank-'+abilityRank(values[key])" style="flex-grow:1;text-align:center;font-weight:bold">{{ abilityRank(values[key]) }}</span><span :class="'val-display-'+key" style="padding-right:20px;font-weight:bold;font-size:2.2rem;color:#000">{{ values[key] }}</span></div>
          <div class="pc-special-ability-grid-container">
            <div class="pc-spec-grid"><div v-for="[key,label] in specialRanks" :key="label" class="pc-spec-item" :style="key?{}:{background:'#f9fafb'}"><template v-if="key"><span :class="{'spec-label-keep':key==='injury'}">{{ label }}</span><span class="pc-rank-shadow" :class="'rank-'+(player[key] || 'D')">{{ player[key] || 'D' }}</span></template></div></div>
            <div class="pc-spec-grid" style="grid-template-rows:repeat(6,50px)"><div v-for="([label,type],index) in skills" :key="index" class="pc-spec-item" :class="'skill-'+type">{{ label }}</div><div v-for="index in Math.max(0,24-skills.length)" :key="'empty'+index" class="pc-spec-item skill-empty" /></div>
          </div>
        </div></div>
        <AbilitySliders :age="number(player.age ?? 25)" :remaining="remaining" :corrections="corrections" :editing="editing" :busy="busy" @edit="editing=true" @save="saveAbilities" @change="changeCorrection" />
        <div class="nav-button-container"><div v-for="[kind,label,links] in groups" :key="label" class="nav-group" :class="kind"><span class="nav-group-label">{{ label }}</span><div class="nav-group-links"><RouterLink v-for="[path,text] in links" :key="path" :to="prefix+'/'+path" class="pc-nav-link"><AppIcon :name="iconForPath(path)" />{{ text }}</RouterLink></div></div><RouterLink :to="prefix+'/edit_player/'+player.player_id" class="pc-edit-btn"><AppIcon name="edit" />編集</RouterLink></div>
        <div class="pc-field-section"><FieldRates :stats="situations"/><FieldRates :stats="situations" cases /></div>
        <RecentForm :data="data" />
      </div>
    </div>
    <div class="mobile-layout"><div class="mob-container">
      <div class="mob-header-row"><div class="mob-name-block"><span class="name-fill" :style="{backgroundImage:gradient}"/><span class="name-letters">{{ firstName }}</span></div><div class="mob-logo-block"><img :src="'/static/uniform.jpeg'" alt="ユニフォーム"></div><div class="mob-number-block">{{ player.number }}</div></div>
      <div class="mob-pos-row"><span class="mob-label-pill">守備位置</span><span class="mob-pos-val">{{ [player.pos1,player.pos2,player.pos3].filter(Boolean).join(' ') }}</span></div>
      <div class="mob-photo-block"><img class="detail-player-photo" :src="staticImage(player.image_path)" :alt="player.name"></div>
      <div class="mob-info-row"><span class="mob-label-pill">成 績</span><span class="mob-info-val">{{ batting }}</span></div>
      <div class="mob-info-row"><span class="mob-label-pill">性 格</span><span class="mob-info-val-s" style="margin-right:auto">{{ player.character ?? 'ふつう' }}</span><span class="mob-label-pill">投 打</span><span class="mob-info-val-s">{{ player.pitch_bat ?? '右投右打' }}</span></div>
      <div class="mob-ability-row" style="margin-top:15px"><span class="mob-ability-label">弾　道</span><span class="dan-mark"><img :src="'/static/trajectory/arrow_'+dan+'.png'" alt="弾道"><span class="dan-num">{{ dan }}</span></span></div>
      <div v-for="[key,label] in abilityFields" :key="key" class="mob-ability-row"><span class="mob-ability-label">{{ label }}</span><span class="mob-ability-rank" :class="'rank-'+abilityRank(values[key])">{{ abilityRank(values[key]) }}</span><span class="mob-ability-val" :class="'val-display-'+key">{{ values[key] }}</span></div>
      <AbilitySliders mobile :age="number(player.age ?? 25)" :remaining="remaining" :corrections="corrections" :editing="editing" :busy="busy" @edit="editing=true" @save="saveAbilities" @change="changeCorrection" />
      <div style="margin-top:15px"><div class="mob-spec-grid" style="margin-bottom:10px"><div v-for="[key,label] in specialRanks" :key="label" class="mob-spec-item" :style="key?{}:{background:'#f9fafb'}"><template v-if="key"><span class="s-label" :class="{'spec-label-keep':key==='injury'}">{{ label }}</span><span class="s-rank" :class="'rank-'+(player[key] || 'D')">{{ player[key] || 'D' }}</span></template></div></div>
        <div class="mob-active-skill-grid"><div v-for="([label,type],index) in skills" :key="index" class="mob-active-skill" :class="'skill-'+type">{{ label }}</div><div v-for="index in Math.max(0,12-skills.length)" :key="'empty'+index" class="mob-active-skill skill-empty" /></div>
      </div>
      <div class="mob-btn-wrap"><RouterLink v-for="[path,label] in mobileLinks" :key="path" :to="prefix+'/'+path" class="mob-nav-btn" :class="{edit:label==='編集'}"><AppIcon :name="iconForPath(path)" />{{ label }}</RouterLink></div>
      <FieldRates mobile :stats="situations"/><FieldRates mobile cases :stats="situations"/><RecentForm mobile :data="data" />
    </div></div>
  </div>
</template>
