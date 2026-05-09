<script setup lang="ts">
import { computed } from 'vue'
import PieceSprite from './PieceSprite.vue'
import type { PieceInstance, Color } from '../../services/api'

const props = defineProps<{
  piece: PieceInstance | null
  isLight: boolean
  isSelected: boolean
  isLegalMove: boolean
  cooldown: number
  maxCooldown: number
}>()

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'rightClick', event: MouseEvent): void
}>()

const squareClasses = computed(() => [
  props.isLight ? 'light' : 'dark',
  props.isSelected ? 'selected' : '',
  props.isLegalMove ? 'legal-move' : '',
  props.piece ? 'piece' : '',
  props.cooldown > 0 ? 'on-cooldown' : '',
])
</script>

<template>
  <div
    class="square"
    :class="squareClasses"
    @click="emit('click')"
    @contextmenu.prevent="emit('rightClick', $event)"
  >
    <PieceSprite
      v-if="piece"
      :name="piece.name"
      :color="(piece.owner as Color)"
    />
    <div
      v-if="cooldown > 0"
      class="cooldown-overlay"
      :style="{ height: (cooldown / (maxCooldown || 1) * 100) + '%' }"
    />
  </div>
</template>

<style scoped>
.square {
  --sq: var(--chakes-sq, min(64px, calc((100vw - 44px) / 8)));
  width: var(--sq);
  height: var(--sq);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: default;
  user-select: none;
  position: relative;
}
.square.piece { cursor: pointer; }
.square.on-cooldown { cursor: not-allowed; }
.light { background: #f0d9b5; }
.dark  { background: #b58863; }
.square.selected::after,
.square.legal-move::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.square.selected::after { background: rgba(246, 246, 105, 0.6); }
.square.legal-move::after { background: rgba(130, 190, 80, 0.45); }
.square.legal-move { cursor: pointer; }
.cooldown-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background: rgba(80, 80, 80, 0.5);
  pointer-events: none;
}
</style>
