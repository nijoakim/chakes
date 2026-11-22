<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue'
import LobbyBrowser from '@/components/lobby/LobbyBrowser.vue'
</script>

<template>
  <section
    id="center"
    class="home"
  >
    <AppHeader />
    <LobbyBrowser />
  </section>
</template>

<style scoped>
#center.home {
  justify-content: flex-start;
  padding: 72px 24px 48px;
  gap: 48px;
}
@media (max-width: 1024px) {
  #center.home {
    padding: 40px 20px 32px;
    gap: 32px;
  }
}
</style>
