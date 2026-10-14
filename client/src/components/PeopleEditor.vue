<script setup>
import { ref } from 'vue';
const props = defineProps({ people: { type: Array, default: () => [] }, busy: Boolean });
const emit = defineEmits(['save']);
const editing = ref(false);
const rows = ref([]);
function open() { rows.value = props.people.map(person => ({ ...person })); editing.value = true; }
function submit() { emit('save', rows.value.filter(person => person.name.trim())); editing.value = false; }
</script>
<template>
  <button type="button" @click="open">回答メンバーを編集</button>
  <form v-if="editing" class="panel" @submit.prevent="submit">
    <div v-for="(person, index) in rows" :key="index" class="form-row">
      <input v-model="person.name" aria-label="メンバー名" maxlength="40" required>
      <button type="button" @click="rows.splice(index, 1)">削除</button>
    </div>
    <button type="button" @click="rows.push({ id: '', name: '' })">メンバーを追加</button>
    <button :disabled="busy">保存</button><button type="button" @click="editing = false">閉じる</button>
  </form>
</template>
