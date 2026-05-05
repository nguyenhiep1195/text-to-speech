<script setup>
import { ref } from 'vue'

const props = defineProps({
  audioUrl: { type: String, required: true },
  srtContent: { type: String, default: '' },
})

const audioRef = ref(null)

function downloadFile(url, filename) {
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
}

function downloadMp3() {
  downloadFile(props.audioUrl, 'output.mp3')
}

function downloadSrt() {
  if (!props.srtContent) return
  const blob = new Blob([props.srtContent], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  downloadFile(url, 'output.srt')
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="player">
    <div class="player__header">
      <span class="player__icon">&#127911;</span>
      <span class="player__title">Your Audio</span>
    </div>

    <audio
      ref="audioRef"
      :src="audioUrl"
      controls
      class="player__audio"
    ></audio>

    <div class="player__actions">
      <button class="player__btn player__btn--primary" @click="downloadMp3">
        &#11015; Download MP3
      </button>
      <button
        v-if="srtContent"
        class="player__btn player__btn--secondary"
        @click="downloadSrt"
      >
        &#11015; Download SRT
      </button>
    </div>
  </div>
</template>

<style scoped>
.player {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
}

.player__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.player__icon {
  font-size: 20px;
}

.player__title {
  font-size: 16px;
  font-weight: 600;
}

.player__audio {
  width: 100%;
  margin-bottom: 16px;
  border-radius: var(--radius-sm);
}

.player__actions {
  display: flex;
  gap: 10px;
}

.player__btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition);
}

.player__btn--primary {
  background: var(--primary);
  color: #fff;
}

.player__btn--primary:hover {
  background: #5a4bd1;
}

.player__btn--secondary {
  background: var(--primary-bg);
  color: var(--primary);
}

.player__btn--secondary:hover {
  background: #ddd8ff;
}
</style>
