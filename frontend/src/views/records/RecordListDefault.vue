<template>
  <div class="records-container">
    <div class="records-header">
      <h1>Objektliste Default</h1>
    </div>
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
