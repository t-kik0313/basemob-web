<script setup>
import { computed, reactive } from 'vue';
import AppIcon from '../AppIcon.vue';
import { dayLabel } from './days.js';
const props=defineProps({poll:Object,dates:Array,canEdit:Boolean,busy:Boolean,today:String});
const emit=defineEmits(['edit','remove']);const opened=reactive({});
const statuses=[['all','終日'],['am','午前だけ'],['pm','午後だけ'],['pending','未定'],['out','不参加'],['','未回答']];
const people=computed(()=>props.poll.people || []);
function count(iso,slot) {return Object.values(props.poll.answers?.[iso] || {}).filter(answer=>['all',slot].includes(answer.status)).length;}
function width(value) { return Math.min(100,value/Math.max(people.value.length,1)*100); }
function members(iso,status) {
  const bucket=props.poll.answers?.[iso] || {};
  const listed=people.value.map(person=>({...person,...bucket[String(person.id)]}));
  const guests=Object.entries(bucket).filter(([id])=>!people.value.some(person=>String(person.id)===id)).map(([id,answer])=>({id,name:answer.name || id,...answer}));
  return [...listed,...guests].filter(person=>(person.status || '')===status);
}
function pill(iso){ const game=props.poll.games?.[iso];return game?`${game.slot==='pm'?'午後':'午前'}で活動予定`:Math.max(count(iso,'am'),count(iso,'pm'))>=7?'手配候補':'様子見'; }
</script>
<template>
  <div class="schedule-board">
    <p class="note schedule-legend">人数メーター：7人以上で手配候補 / 縦線は9人の目安。日付を押すと回答の内訳を表示します。</p>
    <article v-for="iso in dates" :key="iso" class="schedule-day" :class="{'is-ready':Math.max(count(iso,'am'),count(iso,'pm'))>=7}">
      <button type="button" class="schedule-day-summary" :aria-expanded="Boolean(opened[iso])" @click="opened[iso]=!opened[iso]">
        <span class="schedule-date"><AppIcon name="calendar"/><span><strong>{{ dayLabel(iso).short }}</strong><span class="schedule-weekday" :class="dayLabel(iso).kind">{{ dayLabel(iso).weekday }}</span><small v-if="dayLabel(iso).holiday">{{ dayLabel(iso).holiday }}</small></span></span>
        <span class="schedule-meters"><span v-for="[slot,label] in [['am','午前（〜13:00）'],['pm','午後（13:00〜）']]" :key="slot" class="schedule-meter-row" :class="{'is-ready':count(iso,slot)>=7}"><span>{{ label }}</span><strong>{{ count(iso,slot) }}<small>人</small></strong><span class="schedule-meter"><i :style="{width:width(count(iso,slot))+'%'}"/><em :style="{left:width(9)+'%'}"/></span></span></span>
        <span class="schedule-pill" :class="{'is-ready':Math.max(count(iso,'am'),count(iso,'pm'))>=7,'is-planned':poll.games?.[iso]}">{{ pill(iso) }}</span>
      </button>
      <div v-if="opened[iso]" class="schedule-groups"><section v-for="[status,label] in statuses" :key="status"><h3>{{ label }} <span>{{ members(iso,status).length }}</span></h3><span v-for="person in members(iso,status)" :key="person.id" class="schedule-person" :class="{'is-late':person.by && person.by < today}">{{ person.name }}<small v-if="person.by"> {{ person.by.slice(5).replace('-','/') }}まで{{ person.by < today?'・期限超過':'' }}</small></span><span v-if="!members(iso,status).length" class="note">なし</span></section></div>
      <div v-if="canEdit" class="schedule-day-actions"><template v-if="!poll.games?.[iso]"><button v-for="slot in ['am','pm'].filter(slot => count(iso,slot)>=7)" :key="slot" type="button" @click="emit('edit',iso,slot)"><AppIcon name="ball"/>{{ slot==='am'?'午前':'午後' }}に試合を設定</button></template><button class="secondary" type="button" @click="emit('edit',iso)"><AppIcon name="edit"/>試合を編集</button><button class="secondary schedule-remove" type="button" :disabled="busy" @click="emit('remove',iso)"><AppIcon name="trash"/>日程を削除</button></div>
    </article>
    <p v-if="!dates.length" class="note">候補日がありません。日程を追加してください。</p>
  </div>
</template>
