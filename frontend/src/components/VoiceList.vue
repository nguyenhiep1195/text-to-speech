<script setup>
import { computed } from 'vue'

const props = defineProps({
  voices: { type: Array, default: () => [] },
  engines: { type: Array, default: () => [] },
  selectedVoice: { type: String, default: '' },
  selectedEngine: { type: String, default: 'all' },
  selectedLang: { type: String, default: 'vi' },
})

const emit = defineEmits(['update:selectedVoice', 'update:selectedEngine'])

const engineTabs = computed(() => {
  const tabs = props.engines.map((e) => ({ key: e, label: e }))
  tabs.push({ key: 'all', label: 'All' })
  return tabs
})

const filteredVoices = computed(() => {
  return props.voices.filter((v) => {
    const langMatch = v.lang === props.selectedLang
    const engineMatch =
      props.selectedEngine === 'all' || voiceBelongsToEngine(v, props.selectedEngine)
    return langMatch && engineMatch
  })
})

function voiceBelongsToEngine(voice, engine) {
  if (engine === 'edge-tts') {
    return voice.voice.includes('Neural')
  }
  if (engine === 'gtts') {
    return !voice.voice.includes('Neural')
  }
  return true
}

function selectEngine(key) {
  emit('update:selectedEngine', key)
}

function selectVoice(key) {
  emit('update:selectedVoice', key)
}

function getVoiceDisplayName(voice) {
  const raw = voice.voice
  const match = raw.match(/-([A-Za-z]+?)(?:Neural)?$/)
  return match ? match[1] : voice.key
}

function isOnline(voice) {
  return voice.voice.includes('Neural')
}
</script>

<template>
  <div class="voice-list">
    <label class="voice-list__label">Voice List:</label>

    <div class="voice-list__tabs">
      <button
        v-for="tab in engineTabs"
        :key="tab.key"
        class="voice-list__tab"
        :class="{ 'voice-list__tab--active': selectedEngine === tab.key }"
        @click="selectEngine(tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="voice-list__items">
      <label
        v-for="voice in filteredVoices"
        :key="voice.key"
        class="voice-item"
        :class="{ 'voice-item--selected': selectedVoice === voice.key }"
      >
        <input
          type="radio"
          :value="voice.key"
          :checked="selectedVoice === voice.key"
          @change="selectVoice(voice.key)"
          class="voice-item__radio"
        />
        <div class="voice-item__info">
          <span class="voice-item__name">{{ getVoiceDisplayName(voice) }}</span>
          <span class="voice-item__desc">{{ voice.desc }}</span>
        </div>
        <span
          class="voice-item__status"
          :class="isOnline(voice) ? 'voice-item__status--online' : 'voice-item__status--offline'"
          :title="isOnline(voice) ? 'Online (Neural)' : 'Online (Google)'"
        ></span>
      </label>

      <p v-if="filteredVoices.length === 0" class="voice-list__empty">
        No voices available for this language/engine.
      </p>
    </div>
  </div>
</template>

<style scoped>
.voice-list {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}

.voice-list__label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
}

.voice-list__tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
}

.voice-list__tab {
  padding: 6px 14px;
  border: none;
  border-radius: 20px;
  background: #eee;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  transition: all var(--transition);
}

.voice-list__tab--active {
  background: var(--primary);
  color: #fff;
}

.voice-list__tab:hover:not(.voice-list__tab--active) {
  background: #ddd;
}

.voice-list__items {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 260px;
  overflow-y: auto;
}

.voice-list__items::-webkit-scrollbar {
  width: 4px;
}

.voice-list__items::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 2px;
}

.voice-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--transition);
}

.voice-item:hover {
  background: #f5f3ff;
}

.voice-item--selected {
  background: var(--primary-bg);
}

.voice-item__radio {
  accent-color: var(--primary);
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.voice-item__info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.voice-item__name {
  font-size: 14px;
  font-weight: 500;
}

.voice-item__desc {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.voice-item__status {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.voice-item__status--online {
  background: var(--success);
}

.voice-item__status--offline {
  background: var(--border);
}

.voice-list__empty {
  padding: 20px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
}
</style>
