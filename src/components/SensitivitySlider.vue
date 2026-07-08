<template>
  <div class="sensitivity-slider">
    <div class="slider-header">
      <span class="slider-label">{{ label }}</span>
      <span class="slider-value" :class="valueClass">{{ displayValue }}</span>
    </div>
    <el-slider
      v-model="modelValue"
      :min="min"
      :max="max"
      :step="step"
      :format-tooltip="v => formatTooltip(v)"
      @input="onInput"
    />
    <div class="slider-range">
      <span>{{ formatTooltip(min) }}</span>
      <span>{{ formatTooltip(max) }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Number, default: 0 },
  label: { type: String, default: '' },
  min: { type: Number, default: 0 },
  max: { type: Number, default: 100 },
  step: { type: Number, default: 1 },
  unit: { type: String, default: '' },
  formatFn: { type: Function, default: null }
})

const emit = defineEmits(['update:modelValue', 'change'])

const modelValue = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

function onInput(val) {
  emit('change', val)
}

function formatTooltip(v) {
  if (props.formatFn) return props.formatFn(v)
  return v + (props.unit || '')
}

const displayValue = computed(() => formatTooltip(props.modelValue))

const valueClass = computed(() => {
  if (props.modelValue > (props.min + props.max) / 2) return 'high'
  if (props.modelValue < props.min * 1.2) return 'low'
  return ''
})
</script>

<style lang="scss" scoped>
.sensitivity-slider {
  padding: 8px 0;

  .slider-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 4px;

    .slider-label {
      font-size: 13px;
      color: var(--text-color);
    }

    .slider-value {
      font-size: 14px;
      font-weight: 700;
      color: #409eff;

      &.high {
        color: var(--el-color-danger);
      }

      &.low {
        color: var(--el-color-success);
      }
    }
  }

  .slider-range {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: var(--text-color-secondary);
    margin-top: -4px;
  }
}
</style>
