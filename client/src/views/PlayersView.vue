<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { teamPrefix } from '../api.js';
import PlayerImage from '../components/PlayerImage.vue';
defineProps({ data: Object });
const route = useRoute();
const prefix = computed(() => teamPrefix(route));
</script>
<template>
  <section class="panel">
    <h1>選手一覧</h1>
    <div class="players-grid">
      <RouterLink v-for="player in data.players" :key="player.player_id" :to="prefix + '/player_detail_R1/' + player.player_id" class="player-card">
        <PlayerImage :path="player.image_path" :name="player.name" />
        <h3>{{ player.name }}</h3><p># {{ player.no }}　{{ player.pos1 }}</p>
      </RouterLink>
    </div>
    <p v-if="!data.players?.length" class="note">名簿が空です。</p>
  </section>
</template>
