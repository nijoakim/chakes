<template>
  <header class="app-header">
    <div class="wordmark">
      <svg
        class="mark"
        viewBox="0 0 32 32"
        aria-hidden="true"
      >
        <rect
          width="32"
          height="32"
          rx="7"
          class="mark-bg"
        />
        <circle
          cx="16"
          cy="16"
          r="12"
          class="mark-track"
        />
        <path
          d="M16 4a12 12 0 0 1 11.4 15.7"
          class="mark-arc"
        />
        <g class="mark-piece">
          <circle
            cx="16"
            cy="11"
            r="3.2"
          />
          <path d="M13.6 14.6h4.8l1.3 5.6h-7.4z" />
          <rect
            x="10.5"
            y="20.2"
            width="11"
            height="2.8"
            rx="1.2"
          />
        </g>
      </svg>
      <h1>Chakes</h1>
    </div>
    <p class="pitch">
      Chess without turns. Both players move at once &mdash; every piece goes on a
      short cooldown after it moves, so play each one again as soon as it recovers.
    </p>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  max-width: 640px;
  width: 100%;
}
.wordmark {
  display: flex;
  align-items: center;
  gap: 12px;
}
.mark {
  width: 44px;
  height: 44px;
  flex: none;
}
.mark-bg { fill: var(--accent); }
.mark-track {
  fill: none;
  stroke: var(--accent-fg);
  stroke-opacity: 0.28;
  stroke-width: 2.5;
}
.mark-arc {
  fill: none;
  stroke: var(--accent-fg);
  stroke-width: 2.5;
  stroke-linecap: round;
}
.mark-piece { fill: var(--accent-fg); }
.pitch {
  font-size: 17px;
  line-height: 1.5;
  color: var(--text);
  text-wrap: balance;
}
@media (max-width: 1024px) {
  .mark {
    width: 36px;
    height: 36px;
  }
  .pitch { font-size: 15px; }
}
</style>
