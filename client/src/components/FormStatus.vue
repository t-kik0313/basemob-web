<script setup>import AppIcon from './AppIcon.vue';
defineProps({ error: String, message: String });</script>
<template><p v-if="error" class="error" role="alert"><AppIcon name="alert" />{{ error }}</p><p v-if="message" class="success" role="status"><AppIcon name="check" />{{ message }}</p></template>
