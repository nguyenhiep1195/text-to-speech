<script setup>
const props = defineProps({
  modelValue: { type: String, default: 'vi' },
})

const emit = defineEmits(['update:modelValue'])

const languages = [
  { code: 'vi', label: 'Vietnamese (Vietnam) - VN', flag: '🇻🇳' },
  { code: 'en', label: 'English (United States) - US', flag: '🇺🇸' },
]

function onChange(e) {
  emit('update:modelValue', e.target.value)
}
</script>

<template>
  <div class="lang-select">
    <label class="lang-select__label">Language:</label>
    <div class="lang-select__wrapper">
      <select class="lang-select__input" :value="modelValue" @change="onChange">
        <option v-for="lang in languages" :key="lang.code" :value="lang.code">
          {{ lang.flag }}  {{ lang.label }}
        </option>
      </select>
      <span class="lang-select__arrow">&#9662;</span>
    </div>
  </div>
</template>

<style scoped>
.lang-select {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}

.lang-select__label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.lang-select__wrapper {
  position: relative;
}

.lang-select__input {
  width: 100%;
  padding: 10px 36px 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: #fff;
  font-size: 14px;
  color: var(--text);
  appearance: none;
  cursor: pointer;
}

.lang-select__input:focus {
  outline: none;
  border-color: var(--border-focus);
}

.lang-select__arrow {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  color: var(--text-secondary);
  font-size: 12px;
}
</style>
