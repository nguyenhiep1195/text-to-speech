<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const charCount = computed(() => props.modelValue.length)

function onInput(e) {
  emit('update:modelValue', e.target.value)
}
</script>

<template>
  <div class="text-input">
    <textarea
      class="text-input__area"
      :value="modelValue"
      @input="onInput"
      placeholder="Enter text to convert to speech..."
      rows="6"
    ></textarea>
    <div class="text-input__footer">
      <span class="text-input__count">
        {{ charCount.toLocaleString() }} characters
      </span>
    </div>
  </div>
</template>

<style scoped>
.text-input {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: border-color var(--transition);
}

.text-input:focus-within {
  border-color: var(--border-focus);
}

.text-input__area {
  width: 100%;
  padding: 16px;
  border: none;
  outline: none;
  resize: vertical;
  font-size: 15px;
  line-height: 1.6;
  color: var(--text);
  background: transparent;
  min-height: 140px;
}

.text-input__area::placeholder {
  color: #b2bec3;
}

.text-input__footer {
  display: flex;
  justify-content: flex-end;
  padding: 8px 16px;
  border-top: 1px solid var(--border);
  background: #fafafa;
}

.text-input__count {
  font-size: 13px;
  color: var(--text-secondary);
}

</style>
