<template>
  <div class="float-formula">
    <!-- 策略选择 -->
    <div class="formula-tabs">
      <button
        v-for="s in strategyList"
        :key="s.key"
        class="formula-tab"
        :class="{ active: activeKey === s.key }"
        @click="activeKey = s.key"
      >
        {{ s.name }}
      </button>
    </div>

    <!-- 公式列表 -->
    <div class="formula-list">
      <div v-for="f in currentFormulas" :key="f.name" class="formula-item">
        <div class="formula-name">{{ f.name }}</div>
        <div class="formula-text"><code>{{ f.formula }}</code></div>
        <div class="formula-example">例：{{ f.example }}</div>
        <div class="formula-note">{{ f.note }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { FORMULAS, getStrategyList } from '@/data/formulas'

const strategyList = getStrategyList()
const activeKey = ref('lof')

const currentFormulas = computed(() => {
  return FORMULAS[activeKey.value]?.formulas || []
})
</script>

<style lang="scss" scoped>
.float-formula {
  .formula-tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 10px;

    .formula-tab {
      padding: 3px 10px;
      border: 1px solid var(--border-color);
      border-radius: 10px;
      background: transparent;
      color: var(--text-color-secondary);
      font-size: 11px;
      cursor: pointer;
      transition: all 0.2s;

      &.active {
        background: #409eff;
        border-color: #409eff;
        color: #fff;
      }
    }
  }

  .formula-list {
    max-height: 320px;
    overflow-y: auto;

    .formula-item {
      padding: 8px 10px;
      border-radius: 6px;
      background: var(--bg-color);
      margin-bottom: 8px;

      .formula-name {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-color);
        margin-bottom: 4px;
      }

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
        margin-top: 4px;
        opacity: 0.8;
      }

      .formula-note {
        font-size: 11px;
        color: var(--text-color-secondary);
        margin-top: 2px;
      }
    }
  }
}
</style>
