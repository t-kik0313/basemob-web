<script setup>
defineProps({ columns: Array, rows: Array, empty: { default: 'データがありません。' }, rowKey: { default: 'id' } });
</script>
<template>
  <div v-if="rows?.length" class="table-scroll">
    <table>
      <thead><tr><th v-for="column in columns" :key="column.key" scope="col">{{ column.label }}</th></tr></thead>
      <tbody>
        <tr v-for="(row, index) in rows" :key="row[rowKey] ?? index" :class="{ qualified: row.qualified }">
          <td v-for="column in columns" :key="column.key">
            <slot :name="column.key" :row="row" :value="row[column.key]">{{ column.format ? column.format(row[column.key], row) : row[column.key] ?? '—' }}</slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <p v-else class="note">{{ empty }}</p>
</template>
