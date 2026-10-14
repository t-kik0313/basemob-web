<script setup>defineProps({ error: String, message: String });</script>
<template><p v-if="error" class="error" role="alert">{{ error }}</p><p v-if="message" class="success" role="status">{{ message }}</p></template>
