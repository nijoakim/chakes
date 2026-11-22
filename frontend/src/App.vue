<script setup lang="ts">
import SoundControl from '@/components/SoundControl.vue'
import { useGameSounds } from '@/composables/useGameSounds'

useGameSounds()
</script>

<template>
  <RouterView />
  <SoundControl />
</template>
