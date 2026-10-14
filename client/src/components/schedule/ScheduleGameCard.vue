<script setup>
import AppIcon from '../AppIcon.vue';
import { dayLabel, positionColors } from './days.js';
const props=defineProps({iso:String,card:Object,conditions:Object,canEdit:Boolean,busy:Boolean,past:Boolean});
const emit=defineEmits(['edit','remove']);
function condition(name) { return props.conditions?.[name] || '普通'; }
function conditionImage(name) {return '/static/condition_'+({'絶好調':'excellent','好調':'good','普通':'normal','不調':'poor','絶不調':'bad'})[condition(name)]+'.png';}
</script>
<template>
  <details class="panel schedule-game-card" :open="!past">
    <summary><span class="schedule-date"><AppIcon name="calendar"/><strong>{{ dayLabel(iso).short }}</strong><span class="schedule-weekday" :class="dayLabel(iso).kind">{{ dayLabel(iso).weekday }}</span><span>{{ card.timePB || (card.slot==='am'?'午前':'午後') }}</span></span><span class="schedule-pill is-planned"><AppIcon name="location"/>{{ card.stadium || '試合会場未定' }}</span></summary>
    <div class="schedule-game-layout"><div><h2><AppIcon name="ball"/>{{ card.eventName }} <span v-if="card.opponent">vs {{ card.opponent }}</span></h2>
      <dl class="schedule-game-facts"><div><dt>試合会場</dt><dd>{{ card.stadium || '未定' }}</dd></div><div><dt>住所</dt><dd>{{ card.address || '未定' }}</dd></div><div><dt>集合時間</dt><dd class="schedule-time">{{ card.timeGather || '未定' }}</dd></div><div><dt>試合開始</dt><dd class="schedule-time">{{ card.timePB || '未定' }}</dd></div><div><dt>ユニフォーム</dt><dd><span class="schedule-uniform" :class="card.uniform==='青'?'blue':'black'">{{ card.uniform }}</span></dd></div><div><dt>バット使用条件</dt><dd>{{ card.bat || '情報なし' }}</dd></div></dl><p v-if="card.bench" class="multiline schedule-game-note">{{ card.bench }}</p>
    </div><section class="schedule-lineup"><h3><AppIcon name="users"/>スターティングメンバー</h3><div v-for="(player,index) in card.lineup" :key="index" class="schedule-lineup-row"><strong>{{ index===9 && card.lineup.slice(0,9).some(row => row.p==='DH') && player.p==='投' ? 'P' : index+1 }}</strong><span class="schedule-lineup-name" :style="{backgroundColor:positionColors[player.p] || '#f1f5f9'}">{{ player.n || '未定' }}</span><img v-if="player.n" :src="conditionImage(player.n)" :alt="condition(player.n)" :title="condition(player.n)"><span v-else class="schedule-condition-blank"/><span class="schedule-lineup-position" :style="{backgroundColor:positionColors[player.p] || '#f1f5f9'}">{{ player.p || '—' }}</span></div></section></div>
    <div v-if="canEdit" class="actions"><button class="secondary" type="button" @click="emit('edit',iso)"><AppIcon name="edit"/>編集</button><button class="secondary schedule-remove" type="button" :disabled="busy" @click="emit('remove',iso)"><AppIcon name="trash"/>試合カードを削除</button></div>
  </details>
</template>
