<template>
  <div class="float-calc">
    <!-- 策略预设 -->
    <div class="calc-section">
      <div class="section-label">策略预设</div>
      <el-select v-model="presetKey" placeholder="选择策略公式" size="small" @change="applyPreset">
        <el-option-group v-for="g in presetGroups" :key="g.key" :label="g.name">
          <el-option v-for="f in g.formulas" :key="f.name" :label="f.name" :value="f.name" />
        </el-option-group>
      </el-select>
    </div>

    <!-- 当前公式 -->
    <div v-if="currentFormula" class="calc-formula">
      <code>{{ currentFormula }}</code>
    </div>

    <!-- 参数输入 -->
    <div class="calc-section">
      <div class="section-label">参数</div>
      <div v-for="p in params" :key="p.key" class="param-row">
        <label>{{ p.label }}</label>
        <el-input-number v-model="p.value" size="small" :step="p.step || 0.01" :precision="2" @input="calcResult" />
      </div>
    </div>

    <!-- 结果 -->
    <div v-if="result !== null" class="calc-result">
      <span class="result-label">{{ resultLabel }}</span>
      <span class="result-value">{{ result }}</span>
    </div>

    <el-divider />

    <!-- 通用计算器 -->
    <div class="calc-section">
      <div class="section-label">通用计算</div>
      <el-input v-model="expression" placeholder="输入表达式，如 10000*0.05-15" size="small" @keyup.enter="evalExpression">
        <template #append>
          <el-button @click="evalExpression">=</el-button>
        </template>
      </el-input>
      <div v-if="exprResult !== null" class="calc-result">
        <span class="result-label">结果</span>
        <span class="result-value">{{ exprResult }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { FORMULAS } from '@/data/formulas'

const presetGroups = Object.entries(FORMULAS).map(([key, val]) => ({
  key,
  name: val.name,
  formulas: val.formulas
}))

const presetKey = ref('')
const currentFormula = ref('')
const params = ref([])
const result = ref(null)
const resultLabel = ref('')

const presetConfig = {
  '溢价率': {
    label: '溢价率',
    inputs: [
      { key: 'price', label: '场内价格', value: 1.05, step: 0.01 },
      { key: 'nav', label: '基金净值', value: 1.00, step: 0.01 }
    ],
    calc: (p) => {
      if (!p.nav) return null
      return ((p.price - p.nav) / p.nav * 100).toFixed(2) + '%'
    }
  },
  '套利收益': {
    label: '套利收益',
    inputs: [
      { key: 'amount', label: '申购金额(元)', value: 10000, step: 100 },
      { key: 'premium', label: '溢价率(%)', value: 5, step: 0.1 },
      { key: 'fee', label: '申购费(元)', value: 15, step: 1 },
      { key: 'commission', label: '卖出佣金(元)', value: 5, step: 1 }
    ],
    calc: (p) => (p.amount * p.premium / 100 - p.fee - p.commission).toFixed(2) + ' 元'
  },
  '净溢价': {
    label: '净溢价',
    inputs: [
      { key: 'premium', label: '溢价率(%)', value: 5, step: 0.1 },
      { key: 'purchaseFee', label: '申购费率(%)', value: 0.15, step: 0.01 },
      { key: 'sellFee', label: '卖出佣金率(%)', value: 0.05, step: 0.01 }
    ],
    calc: (p) => (p.premium - p.purchaseFee - p.sellFee).toFixed(2) + '%'
  },
  '转股价值': {
    label: '转股价值',
    inputs: [
      { key: 'price', label: '正股价', value: 12, step: 0.01 },
      { key: 'convPrice', label: '转股价', value: 10, step: 0.01 }
    ],
    calc: (p) => (100 / p.convPrice * p.price).toFixed(2) + ' 元'
  },
  '双低值': {
    label: '双低值',
    inputs: [
      { key: 'price', label: '转债价格', value: 105, step: 0.1 },
      { key: 'premium', label: '溢价率(%)', value: 10, step: 0.1 }
    ],
    calc: (p) => (p.price + p.premium).toFixed(1)
  },
  '折价率': {
    label: '折价率',
    inputs: [
      { key: 'nav', label: '基金净值', value: 1.20, step: 0.01 },
      { key: 'price', label: '场内价格', value: 1.00, step: 0.01 }
    ],
    calc: (p) => {
      if (!p.nav) return null
      return ((p.nav - p.price) / p.nav * 100).toFixed(2) + '%'
    }
  },
  '年化折价收益': {
    label: '年化收益',
    inputs: [
      { key: 'discount', label: '折价率(%)', value: 15, step: 0.1 },
      { key: 'years', label: '剩余年限', value: 2, step: 0.1 }
    ],
    calc: (p) => p.years ? (p.discount / p.years).toFixed(2) + '%' : null
  }
}

function applyPreset(name) {
  const config = presetConfig[name]
  if (!config) return
  currentFormula.value = ''
  params.value = config.inputs.map(i => ({ ...i }))
  resultLabel.value = config.label
  for (const g of presetGroups) {
    const f = g.formulas.find(f => f.name === name)
    if (f) {
      currentFormula.value = f.formula
      break
    }
  }
  calcResult()
}

function calcResult() {
  const config = presetConfig[presetKey.value]
  if (!config) return
  const p = {}
  params.value.forEach(param => { p[param.key] = param.value })
  result.value = config.calc(p)
}

// 通用表达式计算
const expression = ref('')
const exprResult = ref(null)

function evalExpression() {
  try {
    const sanitized = expression.value.replace(/[^-()\d/*+.%]/g, '')
    if (!sanitized) return
    // eslint-disable-next-line no-new-func
    const val = Function('"use strict";return (' + sanitized + ')')()
    exprResult.value = typeof val === 'number' ? val.toFixed(4).replace(/\.?0+$/, '') : '--'
  } catch {
    exprResult.value = '表达式错误'
  }
}
</script>

<style lang="scss" scoped>
.float-calc {
  .calc-section {
    margin-bottom: 12px;

    .section-label {
      font-size: 12px;
      color: var(--text-color-secondary);
      margin-bottom: 6px;
    }
  }

  .calc-formula {
    background: var(--bg-color);
    padding: 8px 10px;
    border-radius: 6px;
    margin-bottom: 12px;

    code {
      font-size: 12px;
      color: var(--text-color);
      word-break: break-all;
    }
  }

  .param-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
    gap: 8px;

    label {
      font-size: 12px;
      color: var(--text-color);
      flex-shrink: 0;
      min-width: 80px;
    }
  }

  .calc-result {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 10px;
    background: rgba(64, 158, 255, 0.08);
    border-radius: 6px;
    margin-top: 8px;

    .result-label {
      font-size: 12px;
      color: var(--text-color-secondary);
    }

    .result-value {
      font-size: 16px;
      font-weight: 700;
      color: #409eff;
    }
  }
}
</style>
