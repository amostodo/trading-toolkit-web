<template>
  <span class="formula-info" @mouseenter="visible = true" @mouseleave="visible = false">
    <el-icon class="info-icon"><InfoFilled /></el-icon>
    <transition name="expand">
      <div v-show="visible" class="formula-popover">
        <div class="formula-text"><code>{{ formula }}</code></div>
        <div v-if="example" class="formula-example">例：{{ example }}</div>
        <div v-if="note" class="formula-note">{{ note }}</div>
      </div>
    </transition>
  </span>
</template>

<script setup>
import { ref } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'

defineProps({
  formula: { type: String, default: '' },
  example: { type: String, default: '' },
  note: { type: String, default: '' }
})

const visible = ref(false)
</script>

<style lang="scss" scoped>
.formula-info {
  display: inline-flex;
  align-items: center;
  position: relative;
  margin-left: 4px;

  .info-icon {
    font-size: 14px;
    color: var(--text-color-secondary);
    cursor: pointer;
    transition: color 0.2s;

    &:hover {
      color: #409eff;
    }
  }

  .formula-popover {
    position: absolute;
    top: 100%;
    left: 0;
    z-index: 100;
    margin-top: 4px;
    padding: 10px 12px;
    background: var(--bg-color-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
    min-width: 240px;
    max-width: 360px;

    .formula-text {
      code {
        font-size: 12px;
        color: #409eff;
        word-break: break-all;
      }
    }

    .formula-example {
      font-size: 11px;
      color: var(--text-color);
      margin-top: 6px;
      opacity: 0.8;
    }

    .formula-note {
      font-size: 11px;
      color: var(--text-color-secondary);
      margin-top: 4px;
    }
  }
}

.expand-enter-active, .expand-leave-active {
  transition: all 0.2s ease;
}

.expand-enter-from, .expand-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
