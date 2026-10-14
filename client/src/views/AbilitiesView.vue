<script setup>
import { useSave } from '../composables/useSave.js';
import { abilityFields, abilityRank, specialFields } from '../stats.js';
import FormStatus from '../components/FormStatus.vue';
defineProps({ data: Object });
const {busy,error,message,save} = useSave();
function update(player,key,value) { save('/api/update_attr',{player_id:player.player_id || player.id,attr:key,value},true); }
</script>
<template>
  <section class="panel"><h1>選手能力一覧</h1><FormStatus :error="error" :message="message" />
    <div class="table-scroll"><table><thead><tr><th>名前</th><th>投打</th><th v-for="[,label] in abilityFields" :key="label">{{ label }}</th><th v-for="label in ['ケガしにくさ','送球','キャッチャー','チャンス','対左','盗塁','走塁']" :key="label">{{ label }}</th><th v-for="[,label] in specialFields" :key="label">{{ label }}</th></tr></thead>
      <tbody><tr v-for="player in data.players_data" :key="player.player_id"><td>{{ player.name }}</td><td>{{ player.pitch_bat }}</td><td v-for="[key,,valueKey] in abilityFields" :key="key"><span class="ability-rank" :class="'rank-'+abilityRank(player[valueKey] || 50)">{{ abilityRank(player[valueKey] || 50) }}</span><strong>{{ player[valueKey] || 50 }}</strong></td><td v-for="key in ['injury','throw','catcher']" :key="key"><select :value="player[key] || 'D'" :aria-label="player.name+' '+key" :disabled="busy" @change="update(player,key,$event.target.value)"><option v-for="rank in ['A','B','C','D','E','F','G']" :key="rank">{{ rank }}</option></select></td><td v-for="key in ['chance_rank','left_rank','steal_rank','run_rank']" :key="key">{{ player[key] || 'D' }}</td><td v-for="[key] in specialFields" :key="key">{{ player[key] ? '○' : '' }}</td></tr></tbody>
    </table></div><p v-if="!data.players_data?.length" class="note">能力データがありません。</p>
  </section>
</template>
