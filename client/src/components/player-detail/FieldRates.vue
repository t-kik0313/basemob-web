<script setup>
import { computed } from 'vue';
import { rate } from '../../stats.js';
const props=defineProps({stats:Object,mobile:Boolean,cases:Boolean});
const items=computed(()=>props.cases ? [
  ['run13','1,3塁','top:3%;left:50%;transform:translateX(-50%);'],
  ['run23','2,3塁',`top:24%;left:${props.mobile?'5':'10'}%;`],
  ['run12','1,2塁',`top:24%;right:${props.mobile?'5':'10'}%;`],
  ['run2','2塁','top:29%;left:50%;transform:translateX(-50%);'],
  ['runF','満塁',`top:${props.mobile?'calc(51% - 10px)':'51%'};left:50%;transform:translateX(-50%);`],
  ['run3','3塁',`top:58%;left:${props.mobile?'12':'18'}%;`],
  ['run1','1塁',`top:58%;right:${props.mobile?'12':'18'}%;`],
  ['run0','無走者','top:calc(80% - 50px);left:50%;transform:translateX(-50%);'],
] : [['left','レフト方向',`top:25%;left:${props.mobile?'12':'15'}%;`],['center','センター方向','top:15%;left:50%;transform:translateX(-50%);'],['right','ライト方向',`top:25%;right:${props.mobile?'12':'15'}%;`]]);
</script>
<template>
  <div :class="mobile?'mob-field-wrapper':'pc-field-box'">
    <div :class="mobile?'mob-field-bg':'field-bg'" />
    <div class="field-title" :class="{'mob-field-title':mobile}">{{ cases?'ケース別打率':'打球方向' }}</div>
    <div v-for="[key,label,position] in items" :key="key" class="stat-box" :class="{'hot-zone':stats[key].ab && stats[key].avg>=.3,'cold-zone':stats[key].ab && stats[key].avg<.2}" :style="position">
      <div class="box-label">{{ label }}</div><div class="box-rate">{{ rate(stats[key].avg) }}</div><div class="box-detail">{{ stats[key].ab }}-{{ stats[key].hits }}</div>
    </div>
  </div>
</template>
