<script setup>
import AppIcon from '../components/AppIcon.vue';
import ScheduleBoard from '../components/schedule/ScheduleBoard.vue';
import ScheduleGameCard from '../components/schedule/ScheduleGameCard.vue';
import { positionColors, dayLabel } from '../components/schedule/days.js';
import '../components/schedule/schedule.css';
import { computed, nextTick, reactive, ref } from 'vue';
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
const gameEditor = ref(null);
const gameDays = computed(() => Object.entries(poll.value.games || {}).sort(([a],[b]) => a.localeCompare(b)));
function editGame(iso,slot = 'am') {
  gameDate.value = iso;
  Object.assign(game, { slot, opponent:'', eventName:'練習試合', stadium:'', address:'', uniform:'黒', bat:'情報なし', timeGather:'', timePB:'', bench:'', lineup:Array.from({length:10},()=>({n:'',p:''})) }, JSON.parse(JSON.stringify(poll.value.games?.[iso] || {})));
  nextTick(() => gameEditor.value?.scrollIntoView?.({behavior: window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',block:'start'}));
}
const showAdd = ref(false);
const monthTitle = computed(() => { const d = new Date(); return `${d.getFullYear()}年 ${d.getMonth()+1}月・${new Date(d.getFullYear(),d.getMonth()+1).getMonth()+1}月の日程調整`; });
async function copyLink() { try { await navigator.clipboard.writeText(window.location.origin + route.path + '?view=answer'); message.value='回答用リンクをコピーしました。'; } catch { error.value='リンクをコピーできませんでした。'; } }

</script>
<template>
  <div class="schedule-page">
  <header class="schedule-page-header"><div><h1><AppIcon name="calendar" />日程・出欠</h1><p class="note">{{ monthTitle }}</p></div>
    <nav class="schedule-view-switch" aria-label="スケジュールの表示"><button v-for="[key,label] in [['board','調整ボード'],['answer','回答シート'],['game','試合カード']]" :key="key" :class="{selected:view===key}" :aria-pressed="view===key" @click="router.replace({ query:{...route.query,view:key} })"><AppIcon :name="{board:'users',answer:'clipboard',game:'ball'}[key]" />{{ label }}</button></nav>
  </header>
  <FormStatus :error="error" :message="message" />
  <p v-if="busy" role="status">読み込み・保存中です。</p>
  <template v-if="view === 'board'">
    <section class="panel schedule-tools"><div class="actions"><button class="secondary" type="button" @click="copyLink"><AppIcon name="external"/>回答用リンクをコピー</button><button v-if="data.logged_in" class="secondary" type="button" :aria-expanded="showAdd" @click="showAdd=!showAdd"><AppIcon name="plus"/>日程を追加</button></div>
      <form v-if="showAdd && data.logged_in" class="form-row" @submit.prevent="request({action:'add',iso:newDate})"><label>日程を追加<input v-model="newDate" type="date" :min="windowDates.today" :max="windowDates.end" required></label><button :disabled="busy"><AppIcon name="plus"/>追加</button></form>
    </section>
    <ScheduleBoard :dates="days" :poll="poll" :can-edit="data.logged_in" :busy="busy" :today="windowDates.today" @edit="editGame" @remove="iso => request({action:'remove',iso})" />
  </template>
  <AttendanceForm sheet v-if="view === 'answer'" :dates="days" :people="poll.people || []" :answers="poll.answers || {}" :busy="busy" @save="body => request({action:'answer',...body})" />
  <template v-if="view === 'game'">
    <ScheduleGameCard v-for="[iso,card] in gameDays" :key="iso" :iso="iso" :card="card" :conditions="data.conditions" :past="iso < windowDates.today" :busy="busy" :can-edit="data.logged_in && iso >= windowDates.today && iso <= windowDates.end" @edit="editGame" @remove="date => request({action:'clear-game',iso:date})" />
    <section v-if="!gameDays.length" class="panel schedule-empty"><AppIcon name="ball"/><h2>試合カードはありません。</h2><p class="note">調整ボードから日程を選び、試合を設定してください。</p></section>
  </template>
  <form ref="gameEditor" v-if="gameDate && data.logged_in" class="panel schedule-game-editor" @submit.prevent="request({action:'game',iso:gameDate,game})">
    <h2><AppIcon name="edit"/>{{ dayLabel(gameDate).short }} 試合カード</h2>
    <FormStatus :error="error" :message="message" />
    <div class="form-grid">
    <label>時間帯<select v-model="game.slot"><option value="am">午前</option><option value="pm">午後</option></select></label>
    <label v-for="[key,label] in [['opponent','対戦相手'],['stadium','球場'],['address','住所']]" :key="key">{{ label }}<input v-model="game[key]" maxlength="120"></label>
    <div class="schedule-wide"><AddressSearch @select="address => game.address = address" /></div>
    <label v-for="[key,label,options] in [['eventName','種別',['公式戦','練習試合']],['uniform','ユニフォーム',['黒','青']],['bat','バット',['ウレタン可','金属・木製のみ','情報なし']]]" :key="key">{{ label }}<select v-model="game[key]"><option v-for="option in options" :key="option">{{ option }}</option></select></label>
    <label>集合<input v-model="game.timeGather" type="time"></label><label>開始<input v-model="game.timePB" type="time"></label></div>
    <h3><AppIcon name="users"/>スターティングメンバー</h3>
    <div v-for="(player,index) in game.lineup" :key="index" class="schedule-lineup-row"><strong>{{ index + 1 }}</strong><input :style="{backgroundColor:positionColors[player.p] || '#f1f5f9'}" v-model="player.n" list="roster-names" aria-label="選手名"><select v-model="player.p" aria-label="守備位置" :style="{backgroundColor:positionColors[player.p] || '#f1f5f9'}"><option v-for="position in ['','投','捕','一','二','三','遊','左','中','右','DH']" :key="position">{{ position }}</option></select></div>
    <datalist id="roster-names"><option v-for="person in poll.people || []" :key="person.id" :value="person.name" /></datalist>
    <label>ベンチ・備考<textarea v-model="game.bench" maxlength="500" /></label><button :disabled="busy"><AppIcon name="save" />保存</button><button type="button" @click="gameDate = ''"><AppIcon name="close" />閉じる</button>
  </form>
  <section v-if="data.logged_in" class="panel schedule-people"><h2><AppIcon name="users"/>回答メンバー</h2><p class="note">調整ボード・回答シートの対象者を設定します。</p>
  <PeopleEditor v-if="data.logged_in" :people="poll.people || []" :busy="busy" @save="people => request({action:'people',people})" />
  </section>
  </div>
</template>
