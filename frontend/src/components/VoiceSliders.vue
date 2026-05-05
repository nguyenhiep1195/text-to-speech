<script setup>
import { computed } from 'vue'

const props = defineProps({
  speed: { type: Number, default: 1.0 },
  pitch: { type: String, default: '+0Hz' },
})

const emit = defineEmits(['update:speed', 'update:pitch'])

const pitchValue = computed(() => {
  const match = props.pitch.match(/([+-]?\d+)/)
  return match ? parseInt(match[1]) : 0
})

const speedLabel = computed(() => {
  if (props.speed === 1.0) return 'Default'
  return `${props.speed.toFixed(1)}x`
})

const pitchLabel = computed(() => {
  if (pitchValue.value === 0) return 'Default'
  return props.pitch
})

function onSpeedInput(e) {
  emit('update:speed', parseFloat(e.target.value))
}

function onPitchInput(e) {
  const val = parseInt(e.target.value)
  emit('update:pitch', `${val >= 0 ? '+' : ''}${val}Hz`)
}

function resetSpeed() {
  emit('update:speed', 1.0)
}

function resetPitch() {
  emit('update:pitch', '+0Hz')
}
</script>

<template>
  <div class="sliders">
    <div class="slider-row">
      <div class="slider-row__header">
        <span class="slider-row__label">Voice Speed</span>
        <button class="slider-row__reset" @click="resetSpeed" :title="speedLabel">
          {{ speedLabel }}
        </button>
      </div>
      <input
        type="range"
        class="slider-row__input"
        min="0.5"
        max="2.0"
        step="0.1"
        :value="speed"
        @input="onSpeedInput"
      />
      <div class="slider-row__marks">
        <span>0.5x</span>
        <span>1.0x</span>
        <span>2.0x</span>
      </div>
    </div>

    <div class="slider-row">
      <div class="slider-row__header">
        <span class="slider-row__label">Speech Pitch</span>
        <button class="slider-row__reset" @click="resetPitch" :title="pitchLabel">
          {{ pitchLabel }}
        </button>
      </div>
      <input
        type="range"
        class="slider-row__input"
        min="-50"
        max="50"
        step="5"
        :value="pitchValue"
        @input="onPitchInput"
      />
      <div class="slider-row__marks">
        <span>-50Hz</span>
        <span>0Hz</span>
        <span>+50Hz</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sliders {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.slider-row__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.slider-row__label {
  font-size: 14px;
  font-weight: 500;
}

.slider-row__reset {
  font-size: 13px;
  color: var(--text-secondary);
  background: none;
  border: none;
  padding: 2px 6px;
  border-radius: 4px;
  transition: background var(--transition);
}

.slider-row__reset:hover {
  background: #f0f0f0;
  color: var(--primary);
}

.slider-row__input {
  width: 100%;
  height: 6px;
  appearance: none;
  background: var(--primary);
  border-radius: 3px;
  outline: none;
}

.slider-row__input::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--primary);
  border: 3px solid #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.slider-row__input::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--primary);
  border: 3px solid #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.slider-row__marks {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 11px;
  color: var(--text-secondary);
}
</style>
