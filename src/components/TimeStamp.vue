<template>
  <el-tooltip
    v-if="isValid"
    :content="absoluteTime"
    placement="top"
    :show-after="300"
  >
    <span class="timestamp" :class="staleClass">{{ relativeTime }}</span>
  </el-tooltip>
  <span v-else class="timestamp timestamp-invalid">--</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 时间值：ISO 字符串、时间戳(ms) 或 Date 对象
  time: { type: [String, Number, Date], default: null },
  // 过期阈值（分钟），超过则标红
  staleAfter: { type: Number, default: 30 }
})

const date = computed(() => {
  if (!props.time) return null
  if (props.time instanceof Date) return props.time
  const d = new Date(props.time)
  return isNaN(d.getTime()) ? null : d
})

const isValid = computed(() => date.value !== null)

const relativeTime = computed(() => {
  if (!date.value) return '--'
  const now = new Date()
  const diff = (now - date.value) / 1000

  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 86400 * 7) return Math.floor(diff / 86400) + '天前'

  const m = String(date.value.getMonth() + 1).padStart(2, '0')
  const day = String(date.value.getDate()).padStart(2, '0')
  return `${date.value.getFullYear()}-${m}-${day}`
})

const absoluteTime = computed(() => {
  if (!date.value) return '--'
  const y = date.value.getFullYear()
  const m = String(date.value.getMonth() + 1).padStart(2, '0')
  const d = String(date.value.getDate()).padStart(2, '0')
  const h = String(date.value.getHours()).padStart(2, '0')
  const min = String(date.value.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${d} ${h}:${min}`
})

const staleClass = computed(() => {
  if (!date.value) return ''
  const diffMin = (new Date() - date.value) / 60000
  if (diffMin > props.staleAfter) return 'stale'
  return ''
})
</script>

<style lang="scss" scoped>
.timestamp {
  font-size: 12px;
  color: var(--text-color-secondary);

  &.stale {
    color: var(--el-color-danger);
  }

  &.timestamp-invalid {
    color: var(--text-color-secondary);
    opacity: 0.5;
  }
}
</style>
