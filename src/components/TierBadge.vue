<template>
  <span
    v-if="tierInfo.color"
    class="tier-badge"
    :style="badgeStyle"
  >
    <span class="dot" :style="{ background: tierInfo.color }" />
    <template v-if="showLabel">{{ text }}</template>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { getTierInfo } from '@/data/strategyTiers'

const props = defineProps({
  tier: { type: String, default: '' },
  threshold: { type: Number, default: 0 },
  showLabel: { type: Boolean, default: true }
})

const tierInfo = computed(() => getTierInfo(props.tier))

const text = computed(() => {
  if (!props.showLabel) return ''
  if (props.threshold > 0 && tierInfo.value.threshold) {
    return `${tierInfo.value.label} · ${tierInfo.value.threshold}`
  }
  return tierInfo.value.label
})

const badgeStyle = computed(() => ({
  color: tierInfo.value.color,
  borderColor: tierInfo.value.color
}))
</script>

<style lang="scss" scoped>
.tier-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 10px;
  border: 1px solid;
  border-radius: 10px;
  font-size: 12px;
  line-height: 1.6;
  white-space: nowrap;

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }
}
</style>
