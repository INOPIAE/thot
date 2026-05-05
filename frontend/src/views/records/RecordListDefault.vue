<template>
  <div class="records-container">
    <RecordList :defaultListMode="true" />
  </div>
</template>

<script setup>
import RecordList from './RecordList.vue'
</script>

<style scoped>
.records-container {
  padding: 2rem;
}
</style>
