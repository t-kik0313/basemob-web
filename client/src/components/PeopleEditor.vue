<script setup>
import AppIcon from './AppIcon.vue';
import { ref } from 'vue';
const props = defineProps({ people: { type: Array, default: () => [] }, busy: Boolean });
const emit = defineEmits(['save']);
const editing = ref(false);
const rows = ref([]);
function open() { rows.value = props.people.map(person => ({ ...person })); editing.value = true; }
function submit() { emit('save', rows.value.filter(person => person.name.trim())); editing.value = false; }
</script>
<template>
  <button type="button" @click="open"><AppIcon name="users" />回答メンバーを編集</button>
  <form v-if="editing" class="panel" @submit.prevent="submit">
    <div v-for="(person, index) in rows" :key="index" class="form-row">
      <input v-model="person.name" aria-label="メンバー名" maxlength="40" required>
      <button type="button" @click="rows.splice(index, 1)"><AppIcon name="trash" />削除</button>
    </div>
    <button type="button" @click="rows.push({ id: '', name: '' })"><AppIcon name="user-plus" />メンバーを追加</button>
    <button :disabled="busy"><AppIcon name="save" />保存</button><button type="button" @click="editing = false"><AppIcon name="close" />閉じる</button>
  </form>
</template>
