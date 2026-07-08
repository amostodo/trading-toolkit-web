<template>
  <div class="page-container closed-end-page">
    <div class="page-header page-header-flex">
      <h2>封闭式基金折价套利</h2>
      <TierBadge :tier="store.tier" :threshold="store.threshold" />
      <el-input
        v-model="searchKeyword"
        class="search-input"
        placeholder="搜索基金名称/代码"
        clearable
        :prefix-icon="Search"
        size="default"
      />
    </div>

    <!-- 市场概览 -->
    <div class="market-overview" v-loading="store.loading && !store.summary">
      <div class="overview-header">
        <span class="overview-title">市场概览</span>
        <TimeStamp v-if="store.lastUpdated" :time="store.lastUpdated" :stale-after="30" />
      </div>
      <div class="overview-grid">
        <div class="overview-item">
          <div class="overview-value">{{ summary?.count ?? '--' }}</div>
          <div class="overview-label">基金数量</div>
        </div>
        <div class="overview-item">
          <div class="overview-value" :class="{ hl: parseFloat(summary?.avg_discount) > 0 }">
            {{ summary?.avg_discount != null ? (parseFloat(summary.avg_discount) > 0 ? '+' : '') + summary.avg_discount + '%' : '--' }}
          </div>
          <div class="overview-label">平均折溢价</div>
        </div>
        <div class="overview-item">
          <div class="overview-value hl">{{ summary?.high_discount_count ?? '--' }}</div>
          <div class="overview-label">高折价数</div>
        </div>
        <div class="overview-item">
          <div class="overview-value">{{ summary?.premium_count ?? '--' }}</div>
          <div class="overview-label">溢价数</div>
        </div>
      </div>
    </div>

    <!-- Tab 栏 -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
        <span class="tab-count" :class="{ hot: tab.key === 'discount' || tab.key === 'premium' }">{{ tabStats[tab.key] }}</span>
      </button>
    </div>

    <el-alert
      class="guide-alert"
      title="折溢价套利原理：封闭式基金场内价格与净值存在差异。折价时买入可等待价值回归；溢价时则反映市场情绪，需注意回落风险。"
      type="info"
      :closable="false"
      show-icon
    />

    <!-- 桌面表格 -->
    <el-table
      class="desktop-table"
      :data="filteredList"
      v-loading="store.loading"
      stripe
      @row-click="openDetail"
    >
      <el-table-column label="基金" min-width="220">
        <template #default="{ row }">
          <div class="fund-cell">
            <div class="fund-name-line">
              <span class="exchange-badge" :class="row.exchange === '沪' ? 'sh' : 'sz'" v-if="row.exchange">{{ row.exchange }}</span>
              <span class="fund-name">{{ row.name }}</span>
            </div>
            <span class="fund-code">{{ row.code }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="场内价" width="100" align="right">
        <template #default="{ row }">{{ row.price }}</template>
      </el-table-column>
      <el-table-column label="涨跌幅" width="100" align="right">
        <template #default="{ row }">
          <span :class="row.changeClass">{{ row.changePct }}</span>
        </template>
      </el-table-column>
      <el-table-column label="单位净值" width="100" align="right">
        <template #header>
          <el-tooltip content="最近一期公布的单位净值 (REITs 净值定期公布，非每日更新)" placement="top">
            <span>单位净值 ℹ️</span>
          </el-tooltip>
        </template>
        <template #default="{ row }">
          <div>{{ row.nav }}</div>
          <div class="nav-date" v-if="row.navDate">{{ row.navDate }}</div>
        </template>
      </el-table-column>
      <el-table-column label="折价率" width="110" align="right">
        <template #header>
          <el-tooltip content="(单位净值 - 场内价格) / 单位净值 × 100%。正值表示折价，负值表示溢价" placement="top">
            <span>折价率 ℹ️</span>
          </el-tooltip>
        </template>
        <template #default="{ row }">
          <span class="discount-value" :class="row.discountClass">{{ row.discount }}</span>
        </template>
      </el-table-column>
      <el-table-column label="成交额" width="110" align="right">
        <template #default="{ row }">{{ row.amount }}</template>
      </el-table-column>
      <el-table-column label="到期日" width="120" v-if="hasMaturity">
        <template #default="{ row }">{{ row.maturityDate || '--' }}</template>
      </el-table-column>
      <el-table-column label="剩余年限" width="100" align="right" v-if="hasMaturity">
        <template #default="{ row }">{{ row.yearsToMaturity }}</template>
      </el-table-column>
    </el-table>

    <!-- 移动端卡片 -->
    <div class="mobile-cards" v-loading="store.loading">
      <el-card
        v-for="item in filteredList"
        :key="item.code"
        shadow="hover"
        class="fund-mobile-card"
        @click="openDetail(item)"
      >
        <div class="card-header-row">
          <span class="card-code">{{ item.code }}</span>
          <span class="card-name">{{ item.name }}</span>
          <span class="discount-badge" :class="item.discountClass">{{ item.discount }}</span>
        </div>
        <div class="card-info-row">
          <span>场内: <b>{{ item.price }}</b></span>
          <span :class="item.changeClass">{{ item.changePct }}</span>
          <span>净值: <b>{{ item.nav }}</b></span>
        </div>
        <div class="card-info-row">
          <span>成交: {{ item.amount }}</span>
          <span v-if="item.maturityDate">到期: {{ item.maturityDate }}</span>
        </div>
      </el-card>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" :title="currentItem?.name || '基金详情'" width="500">
      <template v-if="currentItem">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="基金代码">{{ currentItem.code }}</el-descriptions-item>
          <el-descriptions-item label="基金名称">{{ currentItem.name }}</el-descriptions-item>
          <el-descriptions-item label="基金净值">{{ currentItem.nav }}</el-descriptions-item>
          <el-descriptions-item label="场内价格">{{ currentItem.price }}</el-descriptions-item>
          <el-descriptions-item label="折价率">
            <span :class="currentItem.discountClass">{{ currentItem.discount }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="年化折价">{{ currentItem.annualizedDiscount }}</el-descriptions-item>
          <el-descriptions-item label="到期日">{{ currentItem.maturityDate || '--' }}</el-descriptions-item>
          <el-descriptions-item label="剩余年限">{{ currentItem.yearsToMaturity }}</el-descriptions-item>
          <el-descriptions-item label="基金规模">{{ currentItem.size }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="currentItem.topHoldings.length" class="holdings-section">
          <div class="holdings-title">持仓前十大</div>
          <div class="holdings-tags">
            <el-tag v-for="h in currentItem.topHoldings" :key="h" size="small" effect="plain">{{ h }}</el-tag>
          </div>
        </div>
        <el-alert
          style="margin-top: 12px"
          title="套利策略"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            折价买入，持有至到期折价收敛。当前折价 {{ currentItem.discount }}，年化收益 {{ currentItem.annualizedDiscount }}。
          </template>
        </el-alert>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { useClosedEndStore } from '@/stores/closedEnd'
import TierBadge from '@/components/TierBadge.vue'
import TimeStamp from '@/components/TimeStamp.vue'

const store = useClosedEndStore()
const searchKeyword = ref('')
const activeTab = ref('all')
const detailVisible = ref(false)
const currentItem = ref(null)

const tabs = [
  { key: 'all', label: '全部' },
  { key: 'discount', label: '折价(>0)' },
  { key: 'highDiscount', label: '高折价(≥5%)' },
  { key: 'premium', label: '溢价(<0)' }
]

const filteredList = computed(() => {
  let list = store.fundList
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter(i =>
      i.name.toLowerCase().includes(kw) || i.code.includes(kw)
    )
  }
  switch (activeTab.value) {
    case 'discount':
      return list.filter(i => i.discountRaw > 0)
    case 'highDiscount':
      return list.filter(i => i.discountRaw >= 5)
    case 'premium':
      return list.filter(i => i.discountRaw < 0)
    default:
      return list
  }
})

const tabStats = computed(() => ({
  all: store.fundList.length,
  discount: store.fundList.filter(i => i.discountRaw > 0).length,
  highDiscount: store.fundList.filter(i => i.discountRaw >= 5).length,
  premium: store.fundList.filter(i => i.discountRaw < 0).length
}))

const summary = computed(() => store.summary)

// 是否有任何基金带到期日（mock 数据有，REITs 真实数据无）
const hasMaturity = computed(() => store.fundList.some(i => i.maturityDate))

function openDetail(item) {
  currentItem.value = item
  detailVisible.value = true
}

onMounted(() => {
  if (!store.fundList.length) store.loadAll()
})
onActivated(() => {
  if (!store.fundList.length) store.loadAll()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.closed-end-page {
  .page-header-flex {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;

    h2 {
      margin: 0;
      font-size: 20px;
    }

    .search-input {
      max-width: 300px;
      margin-left: auto;
    }
  }

  .market-overview {
    background: var(--bg-color-secondary);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: var(--card-shadow);

    .overview-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;

      .overview-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-color);
      }
    }

    .overview-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 12px;

      .overview-item {
        text-align: center;

        .overview-value {
          font-size: 24px;
          font-weight: 700;
          color: var(--text-color);

          &.hl {
            color: var(--el-color-danger);
          }
        }

        .overview-label {
          font-size: 12px;
          color: var(--text-color-secondary);
          margin-top: 4px;
        }
      }
    }
  }

  .tab-bar {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
    flex-wrap: wrap;

    .tab-btn {
      padding: 6px 14px;
      border: 1px solid var(--border-color);
      border-radius: 16px;
      background: transparent;
      color: var(--text-color-secondary);
      font-size: 13px;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      gap: 4px;

      &:hover {
        border-color: #409eff;
        color: #409eff;
      }

      &.active {
        background: #409eff;
        border-color: #409eff;
        color: #fff;
      }

      .tab-count {
        font-size: 11px;
        opacity: 0.7;

        &.hot {
          color: var(--el-color-danger);
          opacity: 1;
        }
      }

      &.active .tab-count.hot {
        color: #fff;
      }
    }
  }

  .guide-alert {
    margin-bottom: 12px;
  }

  .desktop-table {
    .fund-cell {
      display: flex;
      flex-direction: column;

      .fund-name-line {
        display: flex;
        align-items: center;
        gap: 6px;
      }

      .exchange-badge {
        display: inline-block;
        font-size: 10px;
        padding: 1px 4px;
        border-radius: 3px;
        background: #f0f0f0;
        color: #666;

        &.sh { background: #fef0f0; color: #d63031; }
        &.sz { background: #f0f7ff; color: #2196f3; }
      }

      .fund-code {
        font-size: 12px;
        color: var(--text-color-secondary);
      }

      .fund-name {
        font-size: 14px;
        color: var(--text-color);
      }
    }

    .nav-date {
      font-size: 11px;
      color: var(--text-color-secondary);
    }

    .up { color: var(--el-color-danger); }
    .down { color: var(--el-color-success); }

    .discount-value {
      font-weight: 600;

      &.high {
        color: var(--el-color-danger);
      }

      &.mid {
        color: var(--el-color-warning);
      }

      &.premium {
        color: var(--el-color-success);
      }
    }
  }

  .mobile-cards {
    display: none;
  }

  .fund-mobile-card {
    margin-bottom: 10px;
    cursor: pointer;

    .card-header-row {
      display: flex;
      align-items: center;
      gap: 8px;

      .card-code {
        font-size: 12px;
        color: var(--text-color-secondary);
      }

      .card-name {
        font-size: 14px;
        font-weight: 600;
        flex: 1;
      }

      .discount-badge {
        font-size: 12px;
        font-weight: 600;
        color: var(--el-color-danger);

        &.mid {
          color: var(--el-color-warning);
        }

        &.premium {
          color: var(--el-color-success);
        }
      }
    }

    .card-info-row {
      display: flex;
      gap: 12px;
      margin-top: 6px;
      font-size: 12px;
      color: var(--text-color);
    }
  }

  .holdings-section {
    margin-top: 12px;

    .holdings-title {
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 6px;
    }

    .holdings-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
  }
}

@media (max-width: 768px) {
  .closed-end-page {
    .desktop-table {
      display: none;
    }

    .mobile-cards {
      display: block;
    }
  }
}
</style>
