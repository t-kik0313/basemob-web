<script setup>
import { reactive, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useSave } from '../composables/useSave.js';
import FormStatus from '../components/FormStatus.vue';
const props = defineProps({data:Object});
const route = useRoute(); const {busy,error,message,save} = useSave();
const coefficient = ref(props.data.pa_coef);
const selected = reactive(Object.fromEntries((props.data.abilities || []).map(([key])=>[key,(props.data.players||[]).filter(p=>p.flags[key]).map(p=>String(p.player_id))])));
function submit(event) { save('/api/screens/admin/'+(route.name==='regulation'?'regulation':'qualitative_abilities'),new FormData(event.currentTarget)); }
</script>
<template>
  <section class="panel"><h1>{{ route.meta.title }}</h1><FormStatus :error="error || data.error" :message="message || (data.saved?'保存しました。':'')" />
    <form v-if="route.name==='regulation'" @submit.prevent="submit"><p class="note">チームの試合数にこの数をかけ、端数を切り上げた打席数を規定打席にします。</p><label class="field">1試合あたりの規定打席<input v-model="coefficient" name="pa_coef" type="number" min="0.1" max="20" step="0.1" required></label><button type="submit" :disabled="busy">保存する</button></form>
    <form v-else @submit.prevent="submit"><p class="note">成績からは判定しない特殊能力です。チェックを入れて保存します。</p><input v-for="[key] in data.abilities" :key="key" name="kind_keys" type="hidden" :value="key">
      <div class="table-scroll"><table><thead><tr><th>背番号</th><th>選手</th><th v-for="[key,label] in data.abilities" :key="key">{{ label }}</th></tr></thead><tbody><tr v-for="player in data.players" :key="player.player_id"><td>{{ player.no }}</td><td>{{ player.name }}</td><td v-for="[key,label] in data.abilities" :key="key"><input v-model="selected[key]" type="checkbox" :name="key" :value="String(player.player_id)" :aria-label="player.name+' '+label"></td></tr></tbody></table></div>
      <label class="field" style="margin-top:16px">新しい特殊能力の名前<input name="new_kind"></label><button type="submit" :disabled="busy">保存する</button>
    </form>
  </section>
</template>
