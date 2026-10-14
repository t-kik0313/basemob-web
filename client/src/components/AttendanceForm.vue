<script setup>
import AppIcon from './AppIcon.vue';
import { dayLabel } from './schedule/days.js';
import { computed, reactive, ref, watch } from 'vue';
const props = defineProps({ dates: Array, people: Array, answers: Object, event: Boolean, busy: Boolean, sheet: Boolean });
const emit = defineEmits(['save']);
const person = ref(''); const guest = ref(''); const entries = reactive({});
const options = computed(() => props.event ? [['in','参加'],['pending','未定'],['out','不参加']] : [['all','終日'],['am','午前'],['pm','午後'],['pending','未定'],['out','不参加']]);
watch([person, () => props.dates, () => props.answers], () => {
  for (const key of Object.keys(entries)) delete entries[key];
  for (const iso of props.dates || []) entries[iso] = { status: '', by: '', ...props.answers?.[iso]?.[person.value] };
}, { immediate: true });
function submit() {
  const answers = Object.fromEntries(Object.entries(entries).map(([iso, entry]) => [iso, { status: entry.status, ...(entry.status === 'pending' ? { by: entry.by } : {}) }]));
  emit('save', { ...(person.value ? { person_id: person.value } : { name: guest.value }), answers });
}
</script>
<template>
  <form class="panel" :class="{'schedule-answer-sheet':sheet}" @submit.prevent="submit">
    <h3><AppIcon name="clipboard" />出欠を回答</h3>
    <label>回答者<select v-model="person"><option value="">ゲスト</option><option v-for="item in people || []" :key="item.id" :value="String(item.id)">{{ item.name }}</option></select></label>
    <label v-if="!person">名前<input v-model="guest" maxlength="40" required></label>
    <div v-for="iso in dates" :key="iso" :class="sheet?'schedule-answer-day':'form-row'">
      <template v-if="sheet"><div class="schedule-date"><strong>{{ dayLabel(iso).short }}</strong><span class="schedule-weekday" :class="dayLabel(iso).kind">{{ dayLabel(iso).weekday }}</span><small v-if="dayLabel(iso).holiday">{{ dayLabel(iso).holiday }}</small></div>
        <div class="schedule-choices"><button v-for="[value,label] in options" :key="value" type="button" :class="{selected:entries[iso].status===value}" :aria-pressed="entries[iso].status===value" :disabled="busy || (!person && !guest.trim())" @click="entries[iso].status = entries[iso].status === value ? '' : value"><AppIcon :name="{all:'check',am:'calendar',pm:'calendar',pending:'history',out:'close',in:'check'}[value]"/>{{ label }}</button></div>
      </template>
      <label v-else>{{ iso }}<select v-model="entries[iso].status"><option value="">未回答</option><option v-for="[value,label] in options" :key="value" :value="value">{{ label }}</option></select></label>
      <label v-if="entries[iso].status === 'pending'" class="schedule-answer-by">回答予定日<input v-model="entries[iso].by" type="date" min="2000-01-01" max="2100-12-31" required></label>
    </div>
    <button :disabled="busy"><AppIcon name="save" />回答を保存</button>
  </form>
</template>
