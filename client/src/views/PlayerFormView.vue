<script setup>
import { computed, onBeforeUnmount, reactive, ref } from 'vue';
import { useRoute } from 'vue-router';
import { teamPrefix, staticImage } from '../api.js';
import { useSave } from '../composables/useSave.js';
import FormStatus from '../components/FormStatus.vue';
const props = defineProps({ data: Object });
const route = useRoute();
const editing = route.name === 'edit';
const fields = reactive({ throw_hand: '右', bat_hand: '右', ...(editing ? props.data.player : props.data.form) });
const { busy, error, message, save } = useSave();
const preview = ref('');
const prefix = computed(() => teamPrefix(route));
function chooseImage(event) {
  if (preview.value) URL.revokeObjectURL(preview.value);
  const file = event.target.files[0];
  preview.value = file ? URL.createObjectURL(file) : '';
}
onBeforeUnmount(() => { if (preview.value) URL.revokeObjectURL(preview.value); });
function submit(event) { save(editing ? '/api/screens/edit_player/' + route.params.playerId : '/api/screens/register_player', new FormData(event.currentTarget)); }
const positions = ['', '投', '捕', '一', '二', '三', '遊', '左', '中', '右'];
</script>
<template>
  <section class="panel">
    <h1>{{ editing ? '選手情報編集' : '選手登録' }}</h1>
    <FormStatus :error="error || data.error" :message="message" />
    <form @submit.prevent="submit">
      <div class="form-grid">
        <label class="field">名前<input v-model="fields.name" name="name" required></label>
        <label class="field">背番号<input v-model="fields.number" name="number" type="number" :required="!editing"></label>
        <template v-if="editing">
          <label v-for="[key, label] in [['pos1', 'メインポジション'], ['pos2', 'サブポジション1'], ['pos3', 'サブポジション2']]" :key="key" class="field">{{ label }}<select v-model="fields[key]" :name="key"><option v-for="position in positions" :key="position" :value="position">{{ position || '未設定' }}</option></select></label>
          <label class="field">投打<select v-model="fields.pitch_bat" name="pitch_bat"><option v-for="hand in ['右投右打','右投左打','右投両打','左投左打','左投右打','左投両打']" :key="hand">{{ hand }}</option></select></label>
          <label class="field">生年月日<input v-model="fields.birth_date" name="birth_date" placeholder="YYYY-MM-DD"></label>
          <label class="field">画像パス<input v-model="fields.image_path" name="image_path"></label>
        </template>
        <template v-else>
          <label class="field">ポジション<input v-model="fields.position" name="position"></label>
          <label class="field">投<select v-model="fields.throw_hand" name="throw_hand"><option v-for="hand in ['右','左','両']" :key="hand">{{ hand }}</option></select></label>
          <label class="field">打<select v-model="fields.bat_hand" name="bat_hand"><option v-for="hand in ['右','左','両']" :key="hand">{{ hand }}</option></select></label>
        </template>
      </div>
      <label class="field">{{ editing ? '新しい画像' : '選手画像' }}<input name="image" type="file" accept="image/jpeg,image/png,image/webp,image/gif" @change="chooseImage"></label>
      <img v-if="preview || (editing && fields.image_path)" :src="preview || staticImage(fields.image_path)" class="image-preview" alt="選手画像のプレビュー">
      <p class="note">画像は jpg・png・webp・gif、8MBまでです。</p>
      <div class="actions"><button type="submit" :disabled="busy">{{ busy ? '保存中…' : '保存' }}</button><RouterLink :to="prefix + (editing ? '/player_detail_R1/' + route.params.playerId : '/players')" class="button secondary">キャンセル</RouterLink></div>
    </form>
  </section>
</template>
