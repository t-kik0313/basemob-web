<script setup>
import { computed, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { usePoll } from '../composables/usePoll.js';
import { dateWindow, scheduleDays } from '../scheduling/dates.js';
import AttendanceForm from '../components/AttendanceForm.vue';
import PeopleEditor from '../components/PeopleEditor.vue';
import FormStatus from '../components/FormStatus.vue';
import AddressSearch from '../components/AddressSearch.vue';
const props = defineProps({ data: Object });
const route = useRoute(); const router = useRouter();
const { poll, busy, error, message, request } = usePoll('/api/schedule', '/api/schedule/poll');
const days = computed(() => scheduleDays(poll.value));
const view = computed(() => ['board','answer','game'].includes(route.query.view) ? route.query.view : (props.data.logged_in ? 'board' : 'answer'));
const windowDates = dateWindow(); const newDate = ref(windowDates.today); const gameDate = ref('');
const game = reactive({});
const gameDays = computed(() => Object.entries(poll.value.games || {}).sort(([a],[b]) => a.localeCompare(b)));
function count(iso, slot) { return Object.values(poll.value.answers?.[iso] || {}).filter(answer => ['all',slot].includes(answer.status)).length; }
function editGame(iso) {
  gameDate.value = iso;
  Object.assign(game, { slot:'am', opponent:'', eventName:'練習試合', stadium:'', address:'', uniform:'黒', bat:'情報なし', timeGather:'', timePB:'', bench:'', lineup:Array.from({length:10},()=>({n:'',p:''})) }, JSON.parse(JSON.stringify(poll.value.games?.[iso] || {})));
}
function answerName(id, answer) { return poll.value.people?.find(person => String(person.id) === id)?.name || answer.name || props.data.roster?.find(person => String(person.player_id) === id)?.name || id; }
const labels = { all:'終日',am:'午前',pm:'午後',pending:'未定',out:'不参加' };
</script>
<template>
  <h1>日程・出欠</h1>
  <div class="toolbar"><button v-for="[key,label] in [['board','出欠一覧'],['answer','回答'],['game','試合カード']]" :key="key" @click="router.replace({ query:{...route.query,view:key} })">{{ label }}</button></div>
  <FormStatus :error="error" :message="message" />
  <p v-if="busy" role="status">読み込み・保存中です。</p>
  <template v-if="view === 'board'">
    <section v-for="iso in days" :key="iso" class="panel day-card">
      <h2>{{ iso }}</h2><p>午前 {{ count(iso,'am') }} 人 / 午後 {{ count(iso,'pm') }} 人（7人・9人を目安に調整）</p>
      <p v-if="poll.games?.[iso]">{{ poll.games[iso].eventName }} / {{ poll.games[iso].opponent }} / {{ poll.games[iso].stadium }}</p>
      <ul><li v-for="(answer,id) in poll.answers?.[iso] || {}" :key="id">{{ answerName(id,answer) }}：{{ labels[answer.status] }} {{ answer.by ? `（${answer.by}まで）` : '' }} <span v-if="data.conditions?.[answerName(id,answer)]"> / {{ data.conditions[answerName(id,answer)] }}</span></li></ul>
      <template v-if="data.logged_in"><button @click="editGame(iso)">試合を編集</button><button :disabled="busy" @click="request({action:'remove',iso})">日程を削除</button></template>
    </section>
    <form v-if="data.logged_in" class="panel" @submit.prevent="request({action:'add',iso:newDate})"><label>日程を追加<input v-model="newDate" type="date" :min="windowDates.today" :max="windowDates.end" required></label><button :disabled="busy">追加</button></form>
  </template>
  <AttendanceForm v-if="view === 'answer'" :dates="days" :people="poll.people || []" :answers="poll.answers || {}" :busy="busy" @save="body => request({action:'answer',...body})" />
  <template v-if="view === 'game'">
    <section v-for="[iso, card] in gameDays" :key="iso" class="panel">
      <h2>{{ iso }} {{ card.eventName }} vs {{ card.opponent }}</h2>
      <p>{{ card.slot === 'am' ? '午前' : '午後' }} / {{ card.stadium }} / {{ card.address }}</p>
      <p>集合 {{ card.timeGather || '未定' }} / 開始 {{ card.timePB || '未定' }} / ユニフォーム {{ card.uniform }} / {{ card.bat }}</p>
      <ol><li v-for="(player,index) in card.lineup" :key="index">{{ player.n }} {{ player.p }} {{ data.conditions?.[player.n] || '' }}</li></ol><p>{{ card.bench }}</p>
      <template v-if="data.logged_in && iso >= windowDates.today && iso <= windowDates.end"><button @click="editGame(iso)">編集</button><button :disabled="busy" @click="request({action:'clear-game',iso})">試合カードを削除</button></template>
    </section><p v-if="!gameDays.length">試合カードはありません。</p>
  </template>
  <form v-if="gameDate && data.logged_in" class="panel" @submit.prevent="request({action:'game',iso:gameDate,game})">
    <h2>{{ gameDate }} 試合カード</h2>
    <label>時間帯<select v-model="game.slot"><option value="am">午前</option><option value="pm">午後</option></select></label>
    <label v-for="[key,label] in [['opponent','対戦相手'],['stadium','球場'],['address','住所']]" :key="key">{{ label }}<input v-model="game[key]" maxlength="120"></label>
    <AddressSearch @select="address => game.address = address" />
    <label v-for="[key,label,options] in [['eventName','種別',['公式戦','練習試合']],['uniform','ユニフォーム',['黒','青']],['bat','バット',['ウレタン可','金属・木製のみ','情報なし']]]" :key="key">{{ label }}<select v-model="game[key]"><option v-for="option in options" :key="option">{{ option }}</option></select></label>
    <label>集合<input v-model="game.timeGather" type="time"></label><label>開始<input v-model="game.timePB" type="time"></label>
    <div v-for="(player,index) in game.lineup" :key="index" class="form-row"><span>{{ index + 1 }}</span><input v-model="player.n" list="roster-names" aria-label="選手名"><select v-model="player.p" aria-label="守備位置"><option v-for="position in ['','投','捕','一','二','三','遊','左','中','右','DH']" :key="position">{{ position }}</option></select></div>
    <datalist id="roster-names"><option v-for="person in poll.people || []" :key="person.id" :value="person.name" /></datalist>
    <label>ベンチ・備考<textarea v-model="game.bench" maxlength="500" /></label><button :disabled="busy">保存</button><button type="button" @click="gameDate = ''">閉じる</button>
  </form>
  <PeopleEditor v-if="data.logged_in" :people="poll.people || []" :busy="busy" @save="people => request({action:'people',people})" />
</template>
