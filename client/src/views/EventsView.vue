<script setup>
import { computed, reactive, ref } from 'vue';
import { usePoll } from '../composables/usePoll.js';
import { dateWindow } from '../scheduling/dates.js';
import AttendanceForm from '../components/AttendanceForm.vue';
import PeopleEditor from '../components/PeopleEditor.vue';
import FormStatus from '../components/FormStatus.vue';
import AddressSearch from '../components/AddressSearch.vue';
defineProps({ data: Object });
const { poll,busy,error,message,request } = usePoll('/api/events');
const events = computed(() => Object.entries(poll.value.events || {}));
const editing = ref(false); const editingId = ref(''); const answerId = ref(''); const date = ref(''); const windowDates = dateWindow(6);
const event = reactive({});
function edit(id='',source={}) {
  editingId.value = id; editing.value = true;
  Object.assign(event,{name:'',place:'',address:'',timeStart:'',note:'',dates:[]},JSON.parse(JSON.stringify(source)));
}
function addDate() { if (date.value && !event.dates.includes(date.value) && event.dates.length < 14) event.dates.push(date.value); }
async function save() { const result = await request({action:editingId.value ? 'update':'create',id:editingId.value,event}); if (result) editing.value = false; }
function name(id,answer) { return poll.value.people?.find(person => String(person.id) === id)?.name || answer.name || id; }
const labels = {in:'参加',pending:'未定',out:'不参加'};
</script>
<template>
  <h1>イベント</h1><FormStatus :error="error" :message="message" /><p v-if="busy" role="status">読み込み・保存中です。</p>
  <button v-if="data.logged_in" @click="edit()">イベントを作成</button>
  <p v-if="!events.length && !busy">イベントはありません。</p>
  <section v-for="[id,item] in events" :key="id" class="panel">
    <h2>{{ item.name }} {{ item.confirmed ? '（確定）' : '' }}</h2><p>{{ item.place }} / {{ item.address }} / {{ item.timeStart }}</p><p class="multiline">{{ item.note }}</p>
    <section v-for="iso in item.dates" :key="iso"><h3>{{ iso }}：参加 {{ Object.values(item.answers?.[iso] || {}).filter(answer => answer.status === 'in').length }} 人</h3><ul><li v-for="(answer,personId) in item.answers?.[iso] || {}" :key="personId">{{ name(personId,answer) }}：{{ labels[answer.status] }} {{ answer.by ? `（${answer.by}まで）` : '' }}</li></ul></section>
    <button @click="answerId = answerId === id ? '' : id">出欠を回答</button>
    <template v-if="data.logged_in"><button @click="edit(id,item)">編集</button><button :disabled="busy" @click="request({action:'confirm',id})">確定</button><button :disabled="busy" @click="request({action:'delete',id})">削除</button></template>
    <AttendanceForm v-if="answerId === id" :dates="item.dates" :people="poll.people || []" :answers="item.answers || {}" event :busy="busy" @save="body => request({action:'answer',id,...body})" />
  </section>
  <form v-if="editing && data.logged_in" class="panel" @submit.prevent="save">
    <h2>{{ editingId ? 'イベントを編集' : 'イベントを作成' }}</h2>
    <label>名前<input v-model="event.name" maxlength="40" required></label><label>会場<input v-model="event.place" maxlength="80"></label><label>住所<input v-model="event.address" maxlength="120"></label><label>開始時刻<input v-model="event.timeStart" type="time"></label><label>備考<textarea v-model="event.note" maxlength="500" /></label>
    <AddressSearch @select="address => event.address = address" />
    <div class="form-row"><label>候補日（最大14日）<input v-model="date" type="date" :min="windowDates.today" :max="windowDates.end"></label><button type="button" @click="addDate">候補日を追加</button></div>
    <ul><li v-for="iso in event.dates" :key="iso">{{ iso }} <button type="button" @click="event.dates.splice(event.dates.indexOf(iso),1)">候補日を削除</button></li></ul>
    <button :disabled="busy || !event.dates.length">保存</button><button type="button" @click="editing = false">閉じる</button>
  </form>
  <PeopleEditor v-if="data.logged_in" :people="poll.people || []" :busy="busy" @save="people => request({action:'people',people})" />
</template>
