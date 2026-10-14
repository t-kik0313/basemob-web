<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue';
import { Chart, LineController, LineElement, PointElement, CategoryScale, LinearScale, Filler, Tooltip } from 'chart.js';
import { rate } from '../../stats.js';
Chart.register(LineController,LineElement,PointElement,CategoryScale,LinearScale,Filler,Tooltip);
const props=defineProps({data:Object,mobile:Boolean});
const canvas=ref(null);let chart;
const image=computed(()=>({'絶好調':'excellent','好調':'good','普通':'normal','不調':'poor','絶不調':'bad'})[props.data.condition_text]);
function monthly() { try { return typeof props.data.monthly_avg_data === 'string'?JSON.parse(props.data.monthly_avg_data):props.data.monthly_avg_data || Array(12).fill(null); } catch { return Array(12).fill(null); } }
onMounted(()=>{ chart=new Chart(canvas.value,{
  type:'line',data:{labels:Array.from({length:12},(_,index)=>`${index+1}月`),datasets:[{label:'月別打率',data:monthly(),borderColor:'#1a3c8d',backgroundColor:'rgba(26,60,141,.1)',borderWidth:props.mobile?2:3,pointBackgroundColor:'#ffb800',pointBorderColor:'#fff',pointRadius:props.mobile?4:5,pointHoverRadius:8,spanGaps:true,fill:true,tension:0}]},
  options:{responsive:true,maintainAspectRatio:false,scales:{y:{min:0,max:1,ticks:{callback:rate}}},plugins:{legend:{display:false},tooltip:{callbacks:{label:context=>'打率: '+rate(context.parsed.y)}}}},
}); });
watch(()=>props.data.monthly_avg_data,()=>{ if(chart){chart.data.datasets[0].data=monthly();chart.update();} });
onBeforeUnmount(()=>chart?.destroy());
</script>
<template>
  <div class="stats-section" :class="{'mobile-stats':mobile}">
    <h3>最近の調子と月別打率</h3>
    <div class="recent-form-card"><div class="condition-icon"><img v-if="image" :src="'/static/condition_'+image+'.png'" :alt="data.condition_text"><span v-else>{{ data.condition_emoji || '➖' }}</span><div :style="{color:data.condition_color || '#e60000'}">{{ data.condition_text || '普通' }}</div></div>
      <div><div class="recent-label">直近5試合打率</div><div class="recent-average">{{ data.recent_5_avg || '.000' }} <span>({{ data.recent_5_ab ?? 0 }}-{{ data.recent_5_hits ?? 0 }})</span></div></div>
    </div>
    <div class="monthly-chart-frame"><div class="monthly-chart-container"><canvas ref="canvas" role="img" aria-label="月別打率グラフ" /></div></div>
  </div>
</template>
