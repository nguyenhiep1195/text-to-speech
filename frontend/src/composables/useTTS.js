import { ref } from 'vue'
import axios from 'axios'
import JSZip from 'jszip'

const API_BASE = import.meta.env.VITE_API_URL || ''

function parseSSE(text) {
  const events = []
  const blocks = text.split('\n\n')
  for (const block of blocks) {
    if (!block.trim()) continue
    let eventType = ''
    let data = ''
    for (const line of block.split('\n')) {
      if (line.startsWith('event: ')) eventType = line.slice(7)
      else if (line.startsWith('data: ')) data = line.slice(6)
    }
    if (eventType && data) events.push({ event: eventType, data })
  }
  return events
}

export function useTTS() {
  const voices = ref([])
  const engines = ref([])
  const selectedVoice = ref('vi-female')
  const selectedEngine = ref('all')
  const selectedLang = ref('vi')
  const text = ref('')
  const speed = ref(1.3)
  const pitch = ref('-10Hz')
  const generateSrt = ref(false)
  const wordsPerCue = ref(8)
  const isConverting = ref(false)
  const isGeneratingSrt = ref(false)
  const progress = ref(null)
  const audioUrl = ref(null)
  const srtContent = ref('')
  const errorMessage = ref('')

  let convertController = null
  let srtController = null

  async function fetchVoices() {
    try {
      const { data } = await axios.get(`${API_BASE}/api/voices`)
      voices.value = data.voices || []
      engines.value = data.engines || []
      if (voices.value.length && !selectedVoice.value) {
        selectedVoice.value = voices.value[0].key
      }
    } catch (err) {
      console.error('Failed to fetch voices:', err)
    }
  }

  async function _streamSSE(url, body, { onProgress, onDone, onError, getController }) {
    const controller = new AbortController()
    getController(controller)

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    })

    if (!response.ok) {
      const errText = await response.text()
      try {
        const json = JSON.parse(errText)
        throw new Error(json.detail || 'Request failed.')
      } catch (e) {
        if (e.message !== 'Request failed.') throw new Error(errText || 'Request failed.')
        throw e
      }
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const events = parseSSE(buffer)
      const lastNewline = buffer.lastIndexOf('\n\n')
      buffer = lastNewline >= 0 ? buffer.slice(lastNewline + 2) : buffer

      for (const evt of events) {
        if (evt.event === 'progress') {
          onProgress(JSON.parse(evt.data))
        } else if (evt.event === 'done') {
          await onDone(evt.data)
          return
        } else if (evt.event === 'error') {
          const err = JSON.parse(evt.data)
          onError(err.detail || 'Unknown error')
          return
        }
      }
    }
  }

  async function convert() {
    if (!text.value.trim()) return

    isConverting.value = true
    errorMessage.value = ''
    audioUrl.value = null
    srtContent.value = ''
    progress.value = { current: 0, total: 0 }

    try {
      await _streamSSE(
        `${API_BASE}/api/tts/convert`,
        {
          text: text.value,
          voice: selectedVoice.value,
          speed: speed.value,
          pitch: pitch.value,
          engine: selectedEngine.value === 'all' ? 'edge-tts' : selectedEngine.value,
          generate_srt: generateSrt.value,
          words_per_cue: wordsPerCue.value,
        },
        {
          getController: (c) => { convertController = c },
          onProgress: (p) => { progress.value = p },
          onDone: async (b64Data) => {
            const binary = atob(b64Data)
            const bytes = new Uint8Array(binary.length)
            for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)

            const zip = await JSZip.loadAsync(bytes)

            const mp3File = zip.file('output.mp3')
            if (mp3File) {
              const mp3Blob = await mp3File.async('blob')
              if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
              audioUrl.value = URL.createObjectURL(mp3Blob)
            }

            const srtFile = zip.file('output.srt')
            if (srtFile) srtContent.value = await srtFile.async('string')
          },
          onError: (detail) => {
            errorMessage.value = detail || 'Conversion failed. Please try again.'
          },
        },
      )
    } catch (err) {
      if (err.name === 'AbortError') {
        errorMessage.value = ''
      } else {
        console.error('TTS conversion failed:', err)
        errorMessage.value = err.message || 'Network error. Is the backend running?'
      }
    } finally {
      isConverting.value = false
      progress.value = null
      convertController = null
    }
  }

  function cancelConvert() {
    if (convertController) {
      convertController.abort()
      convertController = null
    }
  }

  async function convertSrtOnly() {
    if (!text.value.trim()) return

    isGeneratingSrt.value = true
    errorMessage.value = ''
    srtContent.value = ''
    progress.value = { current: 0, total: 0 }

    try {
      await _streamSSE(
        `${API_BASE}/api/tts/srt`,
        {
          text: text.value,
          voice: selectedVoice.value,
          speed: speed.value,
          pitch: pitch.value,
          engine: selectedEngine.value === 'all' ? 'edge-tts' : selectedEngine.value,
          words_per_cue: wordsPerCue.value,
        },
        {
          getController: (c) => { srtController = c },
          onProgress: (p) => { progress.value = p },
          onDone: async (srtText) => {
            srtContent.value = srtText
          },
          onError: (detail) => {
            errorMessage.value = detail || 'SRT generation failed. Please try again.'
          },
        },
      )
    } catch (err) {
      if (err.name === 'AbortError') {
        errorMessage.value = ''
      } else {
        console.error('SRT generation failed:', err)
        errorMessage.value = err.message || 'Network error. Is the backend running?'
      }
    } finally {
      isGeneratingSrt.value = false
      progress.value = null
      srtController = null
    }
  }

  function cancelSrt() {
    if (srtController) {
      srtController.abort()
      srtController = null
    }
  }

  return {
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
  }
}
