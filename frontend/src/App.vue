<script setup>
import { ref, computed, onMounted } from 'vue'
import TextInput from './components/TextInput.vue'
import LanguageSelect from './components/LanguageSelect.vue'
import VoiceList from './components/VoiceList.vue'
import VoiceSliders from './components/VoiceSliders.vue'
import AudioPlayer from './components/AudioPlayer.vue'
import { useTTS } from './composables/useTTS'

const {
  voices,
  engines,
  selectedVoice,
  selectedEngine,
  selectedLang,
  text,
  speed,
  pitch,
  generateSrt,
  wordsPerCue,
  isConverting,
  isGeneratingSrt,
  progress,
  audioUrl,
  srtContent,
  errorMessage,
  fetchVoices,
  convert,
  cancelConvert,
  convertSrtOnly,
  cancelSrt,
} = useTTS()

const isProcessing = computed(() => isConverting.value || isGeneratingSrt.value)

function downloadSrt() {
  if (!srtContent.value) return
  const blob = new Blob([srtContent.value], { type: 'text/srt;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'output.srt'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(fetchVoices)
</script>

<template>
  <div class="app">
    <header class="header">
      <h1 class="header__title">Convert Text to Speech Now</h1>
      <p class="header__subtitle">
        Enter your text, choose a language and voice, then convert it to speech.
      </p>
    </header>

    <main class="main">
      <div class="main__top">
        <TextInput v-model="text" />
      </div>

      <div class="main__bottom">
        <div class="main__left">
          <LanguageSelect v-model="selectedLang" />

          <VoiceList
            :voices="voices"
            :engines="engines"
            :selected-lang="selectedLang"
            v-model:selected-voice="selectedVoice"
            v-model:selected-engine="selectedEngine"
          />

          <VoiceSliders v-model:speed="speed" v-model:pitch="pitch" />

          <div class="srt-option">
            <label class="checkbox-label">
              <input type="checkbox" v-model="generateSrt" />
              <span>Generate SRT subtitles</span>
            </label>
            <div v-if="generateSrt" class="srt-option__cue">
              <label>Words per cue:</label>
              <input
                type="number"
                v-model.number="wordsPerCue"
                min="1"
                max="30"
                class="input-number"
              />
            </div>
          </div>
        </div>

        <div class="main__right">
          <button
            class="convert-btn"
            :disabled="!text.trim() || isProcessing"
            @click="convert"
          >
            <span v-if="isConverting" class="convert-btn__spinner"></span>
            <span v-else class="convert-btn__icon">&#10024;</span>
            <template v-if="isConverting && progress">
              Converting... {{ progress.chunk }}/{{ progress.total }}
            </template>
            <template v-else>Convert Speech</template>
          </button>

          <button
            class="srt-btn"
            :disabled="!text.trim() || isProcessing"
            @click="convertSrtOnly"
          >
            <span v-if="isGeneratingSrt" class="convert-btn__spinner"></span>
            <span v-else class="srt-btn__icon">&#9997;</span>
            <template v-if="isGeneratingSrt && progress">
              Generating... {{ progress.chunk }}/{{ progress.total }}
            </template>
            <template v-else>Generate SRT Only</template>
          </button>

          <div v-if="isProcessing && progress && progress.total > 0" class="progress-wrap">
            <div class="progress-bar">
              <div
                class="progress-bar__fill"
                :style="{ width: `${(progress.chunk / progress.total) * 100}%` }"
              ></div>
            </div>
            <span class="progress-text">
              {{ Math.round((progress.chunk / progress.total) * 100) }}%
            </span>
          </div>

          <button
            v-if="isProcessing"
            class="cancel-btn"
            @click="isConverting ? cancelConvert() : cancelSrt()"
          >
            &#10005; Cancel
          </button>

          <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>

          <button
            v-if="srtContent && !audioUrl"
            class="download-srt-btn"
            @click="downloadSrt"
          >
            &#11015; Download SRT
          </button>

          <AudioPlayer
            v-if="audioUrl"
            :audio-url="audioUrl"
            :srt-content="srtContent"
          />
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.app {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 24px 60px;
}

.header {
  text-align: center;
  margin-bottom: 32px;
}

.header__title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
}

.header__subtitle {
  font-size: 15px;
  color: var(--text-secondary);
  margin-top: 8px;
}

.main__top {
  margin-bottom: 24px;
}

.main__bottom {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}

.main__left {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.main__right {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.convert-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 14px 28px;
  border: none;
  border-radius: var(--radius);
  background: var(--primary);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  transition: background var(--transition), transform var(--transition);
}

.convert-btn:hover:not(:disabled) {
  background: #5a4bd1;
  transform: translateY(-1px);
}

.convert-btn:disabled,
.srt-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.srt-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 14px 28px;
  border: 2px solid var(--primary);
  border-radius: var(--radius);
  background: transparent;
  color: var(--primary);
  font-size: 16px;
  font-weight: 600;
  transition: background var(--transition), color var(--transition), transform var(--transition);
}

.srt-btn:hover:not(:disabled) {
  background: var(--primary);
  color: #fff;
  transform: translateY(-1px);
}

.srt-btn__icon {
  font-size: 18px;
}

.convert-btn__icon {
  font-size: 18px;
}

.convert-btn__spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.progress-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: var(--border);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar__fill {
  height: 100%;
  background: var(--primary);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
  min-width: 36px;
  text-align: right;
}

.cancel-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 12px 28px;
  border: 2px solid var(--danger, #e74c3c);
  border-radius: var(--radius);
  background: transparent;
  color: var(--danger, #e74c3c);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition), color var(--transition);
}

.cancel-btn:hover {
  background: var(--danger, #e74c3c);
  color: #fff;
}

.download-srt-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 14px 28px;
  border: none;
  border-radius: var(--radius);
  background: #27ae60;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition), transform var(--transition);
}

.download-srt-btn:hover {
  background: #219a52;
  transform: translateY(-1px);
}

.error-msg {
  background: #ffeaea;
  color: var(--danger);
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  font-size: 14px;
}

.srt-option {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--primary);
}

.srt-option__cue {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-secondary);
}

.input-number {
  width: 60px;
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  text-align: center;
}

@media (max-width: 768px) {
  .main__bottom {
    grid-template-columns: 1fr;
  }

  .app {
    padding: 24px 16px 40px;
  }

  .header__title {
    font-size: 22px;
  }
}
</style>
