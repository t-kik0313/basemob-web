<script setup>
import { abilityFields } from '../../stats.js';
const props=defineProps({mobile:Boolean,age:Number,remaining:Number,corrections:Object,editing:Boolean,busy:Boolean});
const emit=defineEmits(['edit','save','change']);
function change(key,event) { emit('change',key,Number(event.target.value)); event.target.value=props.corrections['plus_'+key]; }
</script>
<template>
  <div :class="mobile?'mob-slider-section':'pc-status-footer-row'">
    <div v-if="!mobile" class="pc-age-point-area"><div class="pc-status-box"><span style="color:#000;font-weight:bold">年齢</span><span style="font-size:2.4rem;font-weight:bold;color:#1e90ff">{{ age }}</span></div><div class="pc-status-box"><span style="color:#000;font-weight:bold">年齢ポイント</span><span class="hold-point-display" :style="{fontSize:'2.4rem',fontWeight:'bold',color:remaining<0?'#ff0000':'#ff8c00'}">{{ Math.max(0,remaining) }}</span></div></div>
    <div class="ability-editor" :class="{'is-editing':editing,'mobile-editor':mobile}">
      <button type="button" class="edit-ability-button" :class="{'save-ability-button':editing}" :title="editing?'保存して完了':'編集する'" :aria-label="editing?'補正を保存':'能力補正を編集'" :disabled="busy" @click="editing?emit('save'):emit('edit')">
        <svg v-if="editing" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10" fill="currentColor"/><path d="m7 12 3 3 7-7" fill="none" stroke="white" stroke-width="2"/></svg>
        <svg v-else viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="m9 2-.7 3-2 1-3-.9-2 3.4 2.2 2.1v2.8L1.3 15.5l2 3.4 3-.9 2 1 .7 3h4l.7-3 2-1 3 .9 2-3.4-2.2-2.1v-2.8L20.7 8.5l-2-3.4-3 .9-2-1L13 2z"/><circle cx="11" cy="12" r="3.5" fill="white"/></svg>
      </button>
      <div v-if="mobile" class="mob-age-row" style="padding-top:5px"><div class="mob-age-box"><span class="l">年齢</span><span class="v">{{ age }}</span></div><div class="mob-age-box"><span class="l">年齢ポイント</span><span class="vp hold-point-display" :style="{color:remaining<0?'#ff0000':'#ff8c00'}">{{ Math.max(0,remaining) }}</span></div></div>
      <div :class="mobile?'mob-sliders-grid':'pc-slider-grid'" :style="mobile?{}:{marginTop:'5px'}">
        <div v-for="[key,label] in abilityFields" :key="key" :class="mobile?'mob-slider-box':'pc-status-box'" :style="mobile?{}:{marginLeft:0,alignItems:'stretch'}">
          <div :class="mobile?'mob-slider-header':'slider-header'"><span>{{ label }}</span><span class="plus-val" style="color:#1e90ff;font-weight:bold">+{{ corrections['plus_'+key] }}</span></div>
          <input class="ability-slider" type="range" :aria-label="label+'補正'" :data-attr="key" min="0" max="16" :value="corrections['plus_'+key]" :disabled="!editing || busy" @input="change(key,$event)" @pointerup="$event.target.blur()" @change="$event.target.blur()">
        </div>
      </div>
    </div>
  </div>
</template>
