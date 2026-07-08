<template>
  <div class="page-container convertible-page">
    <div class="page-header page-header-flex">
      <h2>可转债监控</h2>
      <TierBadge :tier="store.tier" :threshold="store.threshold" />
      <el-input
        v-model="searchKeyword"
        class="search-input"
        placeholder="搜索转债名称/代码/正股"
        clearable
        :prefix-icon="Search"
        size="default"
      />
    </div>

    <!-- 市场温度 -->
    <div class="market-overview" v-loading="store.loading && !store.marketTemp">
      <div class="overview-header">
        <span class="overview-title">市场温度</span>
        <el-tag size="small" effect="plain">{{ marketTemp?.marketStatus || '--' }}</el-tag>
        <TimeStamp v-if="store.lastUpdated" :time="store.lastUpdated" :stale-after="30" />
      </div>
      <div class="overview-grid">
        <div class="overview-item">
          <div class="overview-value">{{ marketTemp?.count ?? '--' }}</div>
          <div class="overview-label">在市转债</div>
        </div>
        <div class="overview-item">
          <div class="overview-value">{{ marketTemp?.priceMedian ?? '--' }}</div>
          <div class="overview-label">价格中位数</div>
        </div>
        <div class="overview-item">
          <div class="overview-value">{{ formatPremiumMedian(marketTemp?.premiumMedian) }}</div>
          <div class="overview-label">溢价中位数</div>
        </div>
        <div class="overview-item">
          <div class="overview-value">{{ marketTemp?.doubleLowMedian ?? '--' }}</div>
          <div class="overview-label">双低中位数</div>
        </div>
      </div>
    </div>

    <!-- 信号 Tab 栏 -->
    <div class="tab-bar">
      <button
        v-for="t in tabs"
        :key="t.key"
        class="tab-btn"
        :class="{ active: activeTab === t.key }"
        @click="switchTab(t.key)"
      >
        <span class="tab-label">{{ t.label }}</span>
        <span class="tab-count" :class="{ hot: t.key === 'placement' }">{{ tabCount(t.key) }}</span>
      </button>
    </div>

    <!-- 投资指引 -->
    <el-alert class="guide-alert" type="info" :closable="false" show-icon>
      <span>{{ guideText }}</span>
    </el-alert>

    <!-- 策略沙盘：参数敏感度分析 -->
    <el-card class="sandbox-card" shadow="never">
      <template #header>
        <div class="sandbox-header" @click="sandboxOpen = !sandboxOpen">
          <span class="sandbox-title">策略沙盘 · 双低值敏感度</span>
          <el-icon class="sandbox-toggle" :class="{ expanded: sandboxOpen }"><ArrowDown /></el-icon>
        </div>
      </template>
      <transition name="expand">
        <div v-show="sandboxOpen" class="sandbox-body">
          <div class="sandbox-sliders">
            <SensitivitySlider
              v-model="cbSandbox.price"
              label="转债价格"
              :min="80"
              :max="160"
              :step="1"
              unit=" 元"
            />
            <SensitivitySlider
              v-model="cbSandbox.premium"
              label="溢价率"
              :min="-20"
              :max="60"
              :step="1"
              unit="%"
            />
            <SensitivitySlider
              v-model="cbSandbox.convPrice"
              label="转股价"
              :min="5"
              :max="30"
              :step="0.5"
              unit=" 元"
            />
          </div>
          <div class="sandbox-result">
            <div class="result-row">
              <span class="result-label">双低值</span>
              <span class="result-value" :class="{ low: cbDoubleLow < 130 }">{{ cbDoubleLow.toFixed(1) }}</span>
            </div>
            <div class="result-row">
              <span class="result-label">转股价值</span>
              <span class="result-value">{{ cbConvValue.toFixed(2) }} 元</span>
            </div>
            <div class="result-row">
              <span class="result-label">建议</span>
              <span class="result-tip" :class="{ warn: cbDoubleLow >= 130 }">{{ cbAdvice }}</span>
            </div>
          </div>
        </div>
      </transition>
    </el-card>

    <!-- 配售 Tab -->
    <div v-if="activeTab === 'placement'" class="tab-content">
      <div class="sub-toolbar">
        <div class="sub-tabs">
          <button
            v-for="s in placementSubs"
            :key="s.key"
            class="sub-btn"
            :class="{ active: placementSubTab === s.key }"
            @click="switchPlacementSub(s.key)"
          >
            {{ s.label }}
            <span class="sub-count" :class="{ hot: s.key === 'subscribing' }">{{ placementTabStats[s.stat] }}</span>
          </button>
        </div>
        <div class="sort-row">
          <button
            v-for="f in sortFields"
            :key="f.field"
            class="sort-btn"
            :class="{ active: placementSortBy === f.field }"
            @click="toggleSort(f.field)"
          >
            {{ f.label }}<span v-if="placementSortBy === f.field">{{ placementSortAsc ? '↑' : '↓' }}</span>
          </button>
        </div>
      </div>

      <el-empty v-if="!filteredPlacement.length" description="暂无符合条件的标的" />

      <el-table
        v-else
        :data="filteredPlacement"
        class="desktop-table"
        stripe
        @row-click="openPendingDetail"
      >
        <el-table-column label="正股" min-width="200">
          <template #default="{ row }">
            <div class="name-cell">
              <div class="name-line">
                <span class="exchange-badge" :class="exchangeClass(row.exchange)" v-if="row.exchange">{{ row.exchange }}</span>
                <span class="bond-name">{{ row.stockName }}</span>
                <el-tag v-if="row.riskLevel" size="small" :type="riskTagType(row.riskClass)" effect="light">{{ row.riskLabel }}</el-tag>
                <el-tag v-if="row.regBadge" size="small" :type="row.regBadgeClass === 'hot' ? 'danger' : 'warning'" effect="dark">{{ row.regBadge }}</el-tag>
              </div>
              <div class="code-line">
                <span class="code-text">{{ row.stockCode }}</span>
                <span class="code-price">{{ row.stockPrice }}</span>
                <span class="code-change" :class="row.stockChangeUp ? 'up' : 'down'">{{ row.stockChange }}</span>
                <span class="code-sep">|</span>
                <span class="progress-tag" :class="row.progressClass">{{ row.progress }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="评级" width="90" align="center">
          <template #default="{ row }">
            <el-tooltip placement="top" :show-after="300">
              <template #content>
                <div class="formula-tip">
                  <div class="ft-formula">策略评级 = 综合评分分档</div>
                  <div class="ft-section">
                    <div class="ft-subtitle">当前评分</div>
                    <div class="ft-detail">综合评分：<b>{{ row.strategyScore }}/100</b></div>
                    <div class="ft-detail">评级结果：<b>{{ row.strategyRating }}</b></div>
                  </div>
                  <div class="ft-divider"></div>
                  <div class="ft-subtitle">评分维度</div>
                  <div class="ft-detail">· 安全垫（收益风险比）</div>
                  <div class="ft-detail">· 百元含权（配售性价比）</div>
                  <div class="ft-detail">· 流通盘（上市弹性）</div>
                  <div class="ft-detail">· 正股趋势（短期动能）</div>
                  <div class="ft-divider"></div>
                  <div class="ft-subtitle">分档标准</div>
                  <div class="ft-detail"><b style="color:#67c23a">推荐</b>：评分 ≥ 80</div>
                  <div class="ft-detail"><b style="color:#e6a23c">可关注</b>：60 ≤ 评分 &lt; 80</div>
                  <div class="ft-detail"><b style="color:#f56c6c">谨慎</b>：评分 &lt; 60</div>
                </div>
              </template>
              <el-tag :class="`rating-tag rating-${row.strategyRatingClass}`" size="small">
                {{ row.strategyRating }}
              </el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="安全垫" width="100" align="right">
          <template #default="{ row }">
            <el-tooltip placement="top" :show-after="300">
              <template #content>
                <div class="formula-tip">
                  <div class="ft-formula">安全垫 = 预估收益 ÷ 配售成本 × 100%</div>
                  <div class="ft-section">
                    <div class="ft-subtitle">计算过程</div>
                    <div class="ft-detail">预估收益 = 1000 × 20% = <b>200元</b></div>
                    <div class="ft-detail" v-if="row._sharesFor10Raw != null && row._stockPriceRaw != null">
                      配售成本 = {{ row._sharesFor10Raw }}股 × {{ row._stockPriceRaw.toFixed(2) }}元
                      = <b>{{ Math.round(row._costFor10LotsRaw) }}元</b>
                    </div>
                    <div class="ft-detail" v-if="row._safetyPadRaw != null">
                      安全垫 = 200 ÷ {{ Math.round(row._costFor10LotsRaw) }} × 100%
                      = <b>{{ row._safetyPadRaw.toFixed(2) }}%</b>
                    </div>
                  </div>
                  <div class="ft-note">安全垫越高，正股下跌容错空间越大</div>
                </div>
              </template>
              <span class="hover-value" :class="safetyPadClass(row._safetyPadRaw)">{{ row.safetyPad }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="每股/配10手" width="170">
          <template #default="{ row }">
            <el-tooltip placement="top" :show-after="300">
              <template #content>
                <div class="formula-tip">
                  <div class="ft-formula">每股配售 = 发行规模 ÷ 原股东股本总数</div>
                  <div class="ft-section" v-if="row._perShareRaw != null">
                    <div class="ft-subtitle">计算过程</div>
                    <div class="ft-detail" v-if="row._issueSizeRaw != null">
                      发行规模 = <b>{{ row._issueSizeRaw.toFixed(2) }}亿</b>
                    </div>
                    <div class="ft-detail" v-if="row._perShareRaw != null">
                      每股配售 = <b>{{ row._perShareRaw.toFixed(4) }}元/股</b>
                    </div>
                    <div class="ft-detail" v-if="row._perShareRaw != null && row._issueSizeRaw != null">
                      推算总股本 = {{ row._issueSizeRaw.toFixed(2) }}亿 × 10000 ÷ {{ row._perShareRaw.toFixed(4) }}
                      = <b>{{ (row._issueSizeRaw * 1e8 / row._perShareRaw / 1e8).toFixed(2) }}亿股</b>
                    </div>
                  </div>
                  <div class="ft-divider"></div>
                  <div class="ft-subtitle">配10张需股数</div>
                  <div class="ft-detail">公式：1000 ÷ 每股配售</div>
                  <div class="ft-detail" v-if="row._perShareRaw != null && row._sharesFor10Raw != null">
                    计算：1000 ÷ {{ row._perShareRaw.toFixed(4) }}
                    = <b>{{ row._sharesFor10Raw }}股</b>
                  </div>
                  <div class="ft-detail" v-if="row._sharesFor10Raw != null && row._stockPriceRaw != null">
                    成本：{{ row._sharesFor10Raw }}股 × {{ row._stockPriceRaw.toFixed(2) }}元
                    = <b>{{ Math.round(row._costFor10LotsRaw) }}元</b>
                  </div>
                  <div class="ft-divider"></div>
                  <div class="ft-subtitle">沪深配售规则</div>
                  <div class="ft-detail"><b>沪市：</b>按手配售，1手 = 10张</div>
                  <div class="ft-detail"><b>深市：</b>按张配售，最小1张</div>
                  <div class="ft-note">不足1手/1张部分按精确算法 rounding</div>
                  <template v-if="row.exchange === '沪' && row._oneHandMinShares > 0">
                    <div class="ft-divider"></div>
                    <div class="ft-subtitle">一手党（仅沪市）</div>
                    <div class="ft-detail">只申购1手，需正股数 ≈ 配10张股数 × 60%</div>
                    <div class="ft-detail" v-if="row._sharesFor10Raw != null">
                      计算：{{ row._sharesFor10Raw }} × 0.6
                      = <b>{{ row._oneHandMinShares }}股</b>
                    </div>
                    <div class="ft-detail" v-if="row._stockPriceRaw != null">
                      最低成本：{{ row._oneHandMinShares }} × {{ row._stockPriceRaw.toFixed(2) }}
                      = <b>{{ row._oneHandMinCostRaw }}元</b>
                    </div>
                    <div class="ft-note">资金占用约 {{ Math.round(row._oneHandMinCostRaw / row._costFor10LotsRaw * 100) }}%，中签率也相应降低</div>
                  </template>
                </div>
              </template>
              <div class="sub-info hover-value">每股 {{ row.perShare }}</div>
              <div class="sub-info hover-value">配1手 {{ row.sharesFor10 }} ≈ {{ row.costFor10Lots }}</div>
              <div class="sub-info onehand hover-value" v-if="row.oneHandMinCost">一手党最低≈{{ row.oneHandMinCost }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="百元含权" width="100" align="right">
          <template #default="{ row }">
            <el-tooltip placement="top" :show-after="300">
              <template #content>
                <div class="formula-tip">
                  <div class="ft-formula">百元含权 = 每股配售 ÷ 正股价 × 100</div>
                  <div class="ft-section" v-if="row._perShareRaw != null && row._stockPriceRaw != null">
                    <div class="ft-subtitle">计算过程</div>
                    <div class="ft-detail">每股配售 = <b>{{ row._perShareRaw.toFixed(4) }}元</b></div>
                    <div class="ft-detail">正股价 = <b>{{ row._stockPriceRaw.toFixed(2) }}元</b></div>
                    <div class="ft-detail">
                      百元含权 = {{ row._perShareRaw.toFixed(4) }} ÷ {{ row._stockPriceRaw.toFixed(2) }} × 100
                      = <b>{{ row._cashRatioRaw.toFixed(2) }}元</b>
                    </div>
                  </div>
                  <div class="ft-note">即每买100元正股可配售的转债金额</div>
                </div>
              </template>
              <span class="hl hover-value">{{ row.cashRatio }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="流通盘" width="130" align="right">
          <template #default="{ row }">
            <el-tooltip placement="top" :show-after="300">
              <template #content>
                <div class="formula-tip">
                  <div class="ft-formula">流通盘 = 发行规模 × (1 - 股东配售率)</div>
                  <div class="ft-section">
                    <div class="ft-subtitle">计算过程</div>
                    <div class="ft-detail" v-if="row._issueSizeRaw != null">
                      发行规模 = <b>{{ row._issueSizeRaw.toFixed(2) }}亿</b>
                    </div>
                    <div class="ft-detail" v-if="row._shareholderRatioRaw != null">
                      股东配售率 = <b>{{ row._shareholderRatioRaw.toFixed(1) }}%</b>
                    </div>
                    <div class="ft-detail" v-if="row._issueSizeRaw != null && row._shareholderRatioRaw != null">
                      流通盘 = {{ row._issueSizeRaw.toFixed(2) }} × (1 - {{ (row._shareholderRatioRaw / 100).toFixed(2) }})
                      = <b>{{ row._floatSharesRaw.toFixed(2) }}亿</b>
                    </div>
                    <div class="ft-detail" v-else-if="row._floatSharesRaw != null">
                      流通盘 = <b>{{ row._floatSharesRaw.toFixed(2) }}亿</b>
                    </div>
                  </div>
                  <div class="ft-note">流通盘越小，上市后弹性越大</div>
                </div>
              </template>
              <span class="hover-value">{{ row.floatShares }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <!-- 移动端卡片 -->
      <div class="mobile-cards">
        <el-card v-for="row in filteredPlacement" :key="row.stockCode" class="mobile-card" shadow="hover" @click="openPendingDetail(row)">
          <div class="mc-head">
            <span class="exchange-badge" :class="exchangeClass(row.exchange)" v-if="row.exchange">{{ row.exchange }}</span>
            <span class="bond-name">{{ row.stockName }}</span>
            <el-tag :class="`rating-tag rating-${row.strategyRatingClass}`" size="small">{{ row.strategyRating }}</el-tag>
            <el-tag v-if="row.regBadge" size="small" :type="row.regBadgeClass === 'hot' ? 'danger' : 'warning'" effect="dark">{{ row.regBadge }}</el-tag>
            <el-tag v-if="row.riskLevel" size="small" :type="riskTagType(row.riskClass)" effect="light">{{ row.riskLabel }}</el-tag>
          </div>
          <div class="mc-code">
            <span>{{ row.stockCode }}</span>
            <span class="code-price">{{ row.stockPrice }}</span>
            <span class="code-change" :class="row.stockChangeUp ? 'up' : 'down'">{{ row.stockChange }}</span>
            <span class="progress-tag" :class="row.progressClass">{{ row.progress }}</span>
          </div>
          <div class="mc-metrics">
            <div><span class="mc-label">含权</span><span class="hl">{{ row.cashRatio }}</span></div>
            <div><span class="mc-label">安全垫</span><span :class="safetyPadClass(row._safetyPadRaw)">{{ row.safetyPad }}</span></div>
            <div><span class="mc-label">收益</span><span class="hl">{{ row.expectedProfit }}</span></div>
            <div><span class="mc-label">规模</span>{{ row.issueSize }}</div>
            <div><span class="mc-label">流通盘</span>{{ row.floatShares }}</div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 信号 Tab（双低/强赎/折价/下修） -->
    <div v-else class="tab-content">
      <el-empty v-if="!signalList.length" description="暂无符合条件的标的" />

      <el-table
        v-else
        :data="signalList"
        class="desktop-table"
        stripe
        @row-click="(row) => goDetail(row.bondCode)"
      >
        <el-table-column label="转债" min-width="200">
          <template #default="{ row }">
            <div class="name-cell">
              <div class="name-line">
                <span class="exchange-badge" :class="exchangeClass(row.exchange)" v-if="row.exchange">{{ row.exchange }}</span>
                <span class="bond-name">{{ row.bondName }}</span>
                <el-icon class="fav-icon" :class="{ active: row.isFavorite }" @click.stop="toggleFav(row)">
                  <StarFilled v-if="row.isFavorite" /><Star v-else />
                </el-icon>
              </div>
              <div class="code-line">
                <span class="code-text">{{ row.bondCode }}</span>
                <span class="stock-name">{{ row.stockName }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="价格" width="110" align="right">
          <template #default="{ row }">
            <div>{{ row.price }}</div>
            <div class="price-sub">{{ row.stockPrice }}</div>
          </template>
        </el-table-column>
        <el-table-column width="110" align="right">
          <template #header>
            溢价率<FormulaInfo
              formula="(转债价格 - 转股价值) / 转股价值 × 100%"
              example="价格 110，转股价值 120 → 溢价率 = -8.33%"
              note="负溢价说明转债被低估"
            />
          </template>
          <template #default="{ row }">
            <span :class="['premium-value', row.premiumClass]">{{ row.premium }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="extraConfig.label" width="120" align="right">
          <template #default="{ row }">
            <span :class="extraConfig.cls(row)">{{ extraConfig.val(row) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 移动端卡片 -->
      <div class="mobile-cards">
        <el-card v-for="row in signalList" :key="row.bondCode" class="mobile-card" shadow="hover" @click="goDetail(row.bondCode)">
          <div class="mc-head">
            <span class="exchange-badge" :class="exchangeClass(row.exchange)" v-if="row.exchange">{{ row.exchange }}</span>
            <span class="bond-name">{{ row.bondName }}</span>
            <el-icon class="fav-icon" :class="{ active: row.isFavorite }" @click.stop="toggleFav(row)">
              <StarFilled v-if="row.isFavorite" /><Star v-else />
            </el-icon>
          </div>
          <div class="mc-code">
            <span>{{ row.bondCode }}</span>
            <span class="stock-name">{{ row.stockName }}</span>
          </div>
          <div class="mc-metrics">
            <div><span class="mc-label">价格</span>{{ row.price }}</div>
            <div><span class="mc-label">正股</span>{{ row.stockPrice }}</div>
            <div><span class="mc-label">溢价</span><span :class="row.premiumClass">{{ row.premium }}</span></div>
            <div><span class="mc-label">{{ extraConfig.label }}</span><span :class="extraConfig.cls(row)">{{ extraConfig.val(row) }}</span></div>
          </div>
        </el-card>
      </div>

      <div class="show-all-bar" v-if="needShowAll">
        <el-button text type="primary" @click="showAll = !showAll">
          {{ showAll ? '收起' : `查看全部 (${store.signals[activeTab].length})` }}
        </el-button>
      </div>
    </div>

    <!-- 待发配售详情弹窗 -->
    <el-dialog
      v-model="pendingDialogVisible"
      width="640px"
      :fullscreen="isMobile"
      class="pending-dialog"
    >
      <template #header>
        <div class="dialog-header-stock">
          <span class="dialog-stock-title" v-if="pendingDetail">
            {{ pendingDetail.stockName }} ({{ pendingDetail.stockCode }})
          </span>
          <a
            v-if="pendingDetail && pendingDetail.stockCode && pendingDetail.stockCode !== '--'"
            class="ext-link"
            :href="`https://finance.baidu.com/stock/ab-${pendingDetail.stockCode}?openFinScope=1`"
            target="_blank"
            rel="noopener noreferrer"
            title="百度财经行情"
            @click.stop
          >
            <el-icon><TopRight /></el-icon>
          </a>
        </div>
      </template>
      <template v-if="pendingDetail">
        <!-- 核心指标 -->
        <div class="detail-section">
          <div class="detail-section-title">核心指标</div>
          <div class="detail-grid">
            <div class="detail-item hl-box"><span class="detail-label">安全垫</span><span class="detail-value hl">{{ pendingDetail.safetyPad }}</span></div>
            <div class="detail-item hl-box"><span class="detail-label">百元含权</span><span class="detail-value hl">{{ pendingDetail.cashRatio }}</span></div>
            <div class="detail-item hl-box"><span class="detail-label">预估收益(10张)</span><span class="detail-value hl">{{ pendingDetail.expectedProfit }}</span></div>
            <div class="detail-item"><span class="detail-label">每股配售</span><span class="detail-value">{{ pendingDetail.perShare }}</span></div>
            <div class="detail-item"><span class="detail-label">配10张需</span><span class="detail-value">{{ pendingDetail.sharesFor10 }}</span></div>
            <div class="detail-item"><span class="detail-label">一手党最低</span><span class="detail-value">{{ pendingDetail.oneHandMinCost || '--' }}</span></div>
          </div>
        </div>

        <!-- 发行进度 -->
        <div class="detail-section">
          <div class="detail-section-title">发行进度</div>
          <!-- 当前节点 & 下一节点 -->
          <div class="stage-progress-info">
            <div class="stage-progress-item current">
              <span class="stage-progress-label">当前节点</span>
              <span class="stage-progress-value">
                {{ currentStage.name }}
                <span v-if="currentStage.date" class="stage-progress-date">{{ currentStage.date }}</span>
              </span>
            </div>
            <div v-if="hasFutureStages" class="stage-progress-item next">
              <span class="stage-progress-label">下一节点</span>
              <span class="stage-progress-value">
                {{ nextStage.name }}
                <span v-if="nextStage.date" class="stage-progress-date">{{ nextStage.date }}</span>
              </span>
            </div>
          </div>
          <el-steps :active="currentStageIndex" align-center finish-status="success" class="detail-timeline">
            <el-step v-for="(s, i) in visibleStageList" :key="i" :title="s.name">
              <template #description>
                <div v-if="s.date" class="stage-date">{{ s.date }}</div>
                <div v-if="s.status === 'current' && getStageDaysLabel(s._origIndex)" class="stage-days" :class="getStageDaysClass(s._origIndex)">{{ getStageDaysLabel(s._origIndex) }}</div>
                <div v-if="s.status === 'current' && getStageRegInfo(s._origIndex)" class="stage-reg-info">{{ getStageRegInfo(s._origIndex) }}</div>
              </template>
            </el-step>
          </el-steps>
        </div>

        <!-- 正股风险 -->
        <div class="detail-section">
          <div class="detail-section-title">正股风险</div>
          <div class="detail-grid">
            <div class="detail-item"><span class="detail-label">正股价</span><span class="detail-value">{{ pendingDetail.stockPrice }}</span></div>
            <div class="detail-item"><span class="detail-label">正股涨幅</span><span class="detail-value">{{ pendingDetail.stockChange }}</span></div>
            <div class="detail-item"><span class="detail-label">市净率PB</span><span class="detail-value">{{ pendingDetail.pb }}</span></div>
            <div class="detail-item"><span class="detail-label">vs20日均价</span><span class="detail-value" :class="trendClass(pendingDetail._stockTrendRaw)">{{ pendingDetail.stockTrend }}</span></div>
            <div class="detail-item"><span class="detail-label">20日均价</span><span class="detail-value">{{ pendingDetail.ma20Price }}</span></div>
            <div class="detail-item"><span class="detail-label">登记日基准价</span><span class="detail-value">{{ pendingDetail.recordPrice }}</span></div>
          </div>
        </div>

        <!-- 发行信息 -->
        <div class="detail-section">
          <div class="detail-section-title">发行信息</div>
          <div class="detail-grid">
            <div class="detail-item"><span class="detail-label">转债名称</span><span class="detail-value">{{ pendingDetail.bondName }}</span></div>
            <div class="detail-item"><span class="detail-label">转债代码</span><span class="detail-value">{{ pendingDetail.bondCode }}</span></div>
            <div class="detail-item"><span class="detail-label">发行规模</span><span class="detail-value">{{ pendingDetail.issueSize }}</span></div>
            <div class="detail-item" v-if="pendingDetail.rating !== '暂无'"><span class="detail-label">信用评级</span><span class="detail-value">{{ pendingDetail.rating }}</span></div>
            <div class="detail-item"><span class="detail-label">转股价</span><span class="detail-value">{{ pendingDetail.conversionPrice }}</span></div>
            <div class="detail-item"><span class="detail-label">方案进展</span><span class="detail-value">{{ pendingDetail.progress }}</span></div>
            <div class="detail-item"><span class="detail-label">股东配售率</span><span class="detail-value">{{ pendingDetail.shareholderRatio }}</span></div>
            <div class="detail-item"><span class="detail-label">股权登记日</span><span class="detail-value copyable" @click="copyText(pendingDetail.regDate)">{{ pendingDetail.regDate }}</span></div>
            <div class="detail-item" v-if="pendingDetail.onlineIssueSize !== '暂无'"><span class="detail-label">网上规模</span><span class="detail-value">{{ pendingDetail.onlineIssueSize }}</span></div>
            <div class="detail-item" v-if="pendingDetail.winRate !== '暂无'"><span class="detail-label">中签率</span><span class="detail-value">{{ pendingDetail.winRate }}</span></div>
          </div>
        </div>

        <!-- 所属板块 -->
        <div class="detail-section">
          <div class="detail-section-title">所属板块</div>
          <div class="sector-row">
            <el-tag v-if="pendingDetail.sectorTag !== '--'" :type="pendingDetail.isHotSector ? 'danger' : 'info'" effect="light">
              {{ pendingDetail.sectorTag }}<span v-if="pendingDetail.isHotSector">🔥</span>
            </el-tag>
            <span v-else>--</span>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 公式回忆（检索练习） -->
    <FormulaRecall :items="cbRecallItems" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Star, StarFilled, ArrowDown, TopRight } from '@element-plus/icons-vue'
import { useConvertibleStore } from '@/stores/convertible'
import { useUserStore } from '@/stores/user'
import TierBadge from '@/components/TierBadge.vue'
import TimeStamp from '@/components/TimeStamp.vue'
import FormulaInfo from '@/components/FormulaInfo.vue'
import SensitivitySlider from '@/components/SensitivitySlider.vue'
import FormulaRecall from '@/components/FormulaRecall.vue'

const router = useRouter()
const store = useConvertibleStore()
const userStore = useUserStore()

const tabs = [
  { key: 'placement', label: '配售' },
  { key: 'double_low', label: '双低' },
  { key: 'force_redeem', label: '强赎' },
  { key: 'discount', label: '折价' },
  { key: 'down_revised', label: '下修' }
]

// 策略沙盘
const sandboxOpen = ref(false)
const cbSandbox = ref({ price: 105, premium: 10, convPrice: 10 })
const cbDoubleLow = computed(() => cbSandbox.value.price + cbSandbox.value.premium)
const cbConvValue = computed(() => {
  const s = cbSandbox.value
  return s.convPrice > 0 ? (100 / s.convPrice * (s.price / (1 + s.premium / 100))).toFixed(2) * 1 : 0
})
const cbAdvice = computed(() => {
  const dl = cbDoubleLow.value
  if (dl < 120) return '双低值低，投资价值高'
  if (dl < 130) return '双低值较低，值得关注'
  if (dl < 140) return '双低值中等，谨慎参与'
  return '双低值偏高，建议回避'
})

// 公式回忆
const cbRecallItems = [
  { prompt: '转股价值 = 100 / ____ × 正股价', answer: '转股价', placeholder: '缺失的项' },
  { prompt: '溢价率 = (____ - 转股价值) / 转股价值 × 100%', answer: '转债价格', placeholder: '缺失的项' },
  { prompt: '双低值 = 转债价格 + ____', answer: '溢价率', placeholder: '缺失的项（数值）' },
  { prompt: '强赎线 = 转股价 × ____', answer: '130%', placeholder: '百分比' }
]

const guideMap = {
  placement: '抢权配售：提前买正股获配债权，百元含权越高越划算，安全垫越高越安全',
  double_low: '双低值越小投资价值越高，低于150可入场，低于170可关注',
  force_redeem: '溢价率低于10%且价格105-140，接近强赎触发线，关注转股套利机会',
  discount: '溢价率为负说明转债比转股便宜，可研究转股套利空间',
  down_revised: '高溢价+低价格+短剩余年限，公司下修转股价概率大'
}

const activeTab = ref('placement')
const placementSubTab = ref('all')
const placementSortBy = ref('composite')
const placementSortAsc = ref(false)
const searchKeyword = ref('')
const showAll = ref(false)
const pendingDialogVisible = ref(false)
const pendingDetail = ref(null)
const premiumRate = ref(20)
const isMobile = ref(false)

const placementSubs = [
  { key: 'all', label: '全部', stat: 'allCount' },
  { key: 'subscribing', label: '申购中', stat: 'subscribingCount' },
  { key: 'pending', label: '待上市', stat: 'pendingListCount' },
  { key: 'approved', label: '审批中', stat: 'approvedCount' }
]

const sortFields = [
  { field: 'safetyPad', label: '安全垫' },
  { field: 'cashRatio', label: '含权' },
  { field: 'floatShares', label: '流通盘' }
]

const marketTemp = computed(() => store.marketTemp)
const guideText = computed(() => guideMap[activeTab.value])

function tabCount(key) {
  // 直接从 store 的 signals / pendingList 取数量，不依赖 marketTemp
  if (key === 'placement') return store.pendingList.length
  if (key === 'double_low') return (store.signals.double_low || []).length
  if (key === 'force_redeem') return (store.signals.force_redeem || []).length
  if (key === 'discount') return (store.signals.discount || []).length
  if (key === 'down_revised') return (store.signals.down_revised || []).length
  return 0
}

const placementTabStats = computed(() => {
  const list = store.pendingList
  return {
    allCount: list.length,
    subscribingCount: list.filter(i => i._status === '申购中').length,
    pendingListCount: list.filter(i => i._status === '待上市').length,
    approvedCount: list.filter(i => i._status === '同意注册' || i._status === '上市委通过').length
  }
})

function filterPendingBySub(list, sub) {
  if (sub === 'subscribing') return list.filter(i => i._status === '申购中')
  if (sub === 'pending') return list.filter(i => i._status === '待上市')
  if (sub === 'approved') return list.filter(i => i._status === '同意注册' || i._status === '上市委通过')
  return list
}

function sortPendingBy(list, field, asc) {
  const sorted = [...list].sort((a, b) => {
    let va = 0, vb = 0
    if (field === 'cashRatio') { va = a._cashRatioRaw || 0; vb = b._cashRatioRaw || 0 }
    else if (field === 'safetyPad') { va = a._safetyPadRaw || 0; vb = b._safetyPadRaw || 0 }
    else if (field === 'issueSize') { va = a._issueSizeRaw || 0; vb = b._issueSizeRaw || 0 }
    else if (field === 'floatShares') { va = a._floatSharesRaw || 0; vb = b._floatSharesRaw || 0 }
    else if (field === 'stockChange') { va = a._stockChangeRaw || 0; vb = b._stockChangeRaw || 0 }
    else if (field === 'composite') { va = a._compositeRankRaw || 0; vb = b._compositeRankRaw || 0 }
    return asc ? va - vb : vb - va
  })
  return sorted
}

function matchSearch(list) {
  const kw = searchKeyword.value.trim().toLowerCase()
  if (!kw) return list
  return list.filter(item =>
    (item.bondName || '').toLowerCase().includes(kw) ||
    (item.bondCode || '').includes(kw) ||
    (item.stockName || '').toLowerCase().includes(kw) ||
    (item.stockCode || '').includes(kw)
  )
}

const filteredPlacement = computed(() => {
  let list = filterPendingBySub(store.pendingList, placementSubTab.value)
  list = sortPendingBy(list, placementSortBy.value, placementSortAsc.value)
  return matchSearch(list)
})

const extraConfig = computed(() => {
  if (activeTab.value === 'double_low') return { label: '双低值', val: r => r.doubleLow, cls: () => 'hl' }
  if (activeTab.value === 'force_redeem') return { label: '距强赎', val: r => r.forceRedemptionGap, cls: r => r.forceRedemptionClass }
  if (activeTab.value === 'discount') return { label: '折价空间', val: r => r.discountSpace, cls: r => r.discountClass }
  return { label: '距下修', val: r => r.downReviseGap, cls: r => r.downReviseClass }
})

const rawSignalList = computed(() => store.signals[activeTab.value] || [])
const needShowAll = computed(() => rawSignalList.value.length > 15)

// 视图层按 Tab 类型默认排序（覆盖 store 的 sortByBest）
// - 双低：double_low 升序（值越小越优）
// - 强赎：_forcePriceGap 降序（越接近/已触发强赎排前）
// - 折价：折价空间降序（折价越大排前）
// - 下修：_revisePriceGap 升序（最接近下修排前）
function discountRank(item) {
  const p = item.premiumNum
  // 仅当溢价为负（折价）时计算折价空间，无折价者排末尾
  return p != null && p < 0 ? Math.abs(p) : -1
}

const sortedSignalList = computed(() => {
  const list = rawSignalList.value
  const tab = activeTab.value
  if (!list || list.length <= 1) return list || []
  return [...list].sort((a, b) => {
    if (tab === 'double_low') return (a.doubleLowNum ?? 9999) - (b.doubleLowNum ?? 9999)
    if (tab === 'force_redeem') return (b._forcePriceGap ?? -9999) - (a._forcePriceGap ?? -9999)
    if (tab === 'discount') return discountRank(b) - discountRank(a)
    if (tab === 'down_revised') return (a._revisePriceGap ?? 9999) - (b._revisePriceGap ?? 9999)
    return 0
  })
})

const signalList = computed(() => {
  let list = sortedSignalList.value
  if (!showAll.value && needShowAll.value) list = list.slice(0, 15)
  return matchSearch(list)
})

const currentStageIndex = computed(() => {
  const list = pendingDetail.value?.stageList || []
  const idx = list.findIndex(s => s.status === 'current')
  return idx >= 0 ? idx : 0
})

// 只显示到当前节点（已完成 + 当前），隐藏未来节点
const visibleStageList = computed(() => {
  const list = pendingDetail.value?.stageList || []
  const curIdx = currentStageIndex.value
  return list.slice(0, curIdx + 1).map((s, i) => ({ ...s, _origIndex: i }))
})

const hasFutureStages = computed(() => {
  const list = pendingDetail.value?.stageList || []
  return currentStageIndex.value < list.length - 1
})

const nextStage = computed(() => {
  const list = pendingDetail.value?.stageList || []
  const idx = currentStageIndex.value + 1
  return list[idx] || { name: '--', date: '' }
})

const currentStage = computed(() => {
  const list = pendingDetail.value?.stageList || []
  return list[currentStageIndex.value] || { name: '--', date: '' }
})

// ALL_STAGES 索引：5=申购中、6=待上市
const STAGE_INDEX_APPLY = 5
const STAGE_INDEX_LIST = 6

function daysDiff(dateStr) {
  if (!dateStr) return null
  const today = new Date().toISOString().slice(0, 10)
  const diff = Math.ceil((new Date(dateStr) - new Date(today)) / 86400000)
  return Number.isFinite(diff) ? diff : null
}

function getStageDate(i) {
  const d = pendingDetail.value
  if (!d) return ''
  return d.stageList?.[i]?.date || ''
}

function getStageDaysLabel(i) {
  const dateStr = getStageDate(i)
  if (!dateStr) return ''
  const diff = daysDiff(dateStr)
  if (diff === null) return ''
  const label = i === STAGE_INDEX_APPLY ? '申购' : i === STAGE_INDEX_LIST ? '上市' : ''
  if (diff === 0) return `今日${label}`
  if (diff > 0) return `${label} +${diff}天`
  return `${label} ${diff}天`
}

function getStageDaysClass(i) {
  const dateStr = getStageDate(i)
  if (!dateStr) return ''
  const diff = daysDiff(dateStr)
  if (diff === null) return ''
  if (diff === 0) return 'today'
  if (diff > 0) return 'future'
  return 'past'
}

// 登记日信息（附在申购中节点下展示）
function getStageRegInfo(i) {
  const d = pendingDetail.value
  if (!d || i !== STAGE_INDEX_APPLY) return ''
  const regRaw = d.regDateRaw
  if (!regRaw) return ''
  const diff = daysDiff(regRaw)
  if (diff === null) return ''
  if (diff === 0) return '今日登记'
  if (diff > 0) return `登记日 +${diff}天`
  return `登记日 ${diff}天`
}

const liveSafetyPad = computed(() => {
  const sp = pendingDetail.value?._safetyPadRaw || 0
  if (sp <= 0) return '--'
  const newPad = sp * (premiumRate.value / 100 / 0.2)
  return newPad.toFixed(2) + '%'
})

const liveExpectedProfit = computed(() => {
  const profit = 1000 * (premiumRate.value / 100)
  return Math.round(profit) + '元'
})

function switchTab(key) {
  activeTab.value = key
  searchKeyword.value = ''
  showAll.value = false
  if (key !== 'placement') {
    placementSubTab.value = 'all'
  }
}

function switchPlacementSub(sub) {
  placementSubTab.value = sub
}

function toggleSort(field) {
  if (placementSortBy.value === field) {
    placementSortAsc.value = !placementSortAsc.value
  } else {
    placementSortBy.value = field
    placementSortAsc.value = false
  }
}

function openPendingDetail(row) {
  if (!row?.detail) return
  pendingDetail.value = { ...row.detail }
  premiumRate.value = 20
  pendingDialogVisible.value = true
}

function toggleFav(row) {
  userStore.toggleFavorite('convertible', row.bondCode, row.bondName)
  store.refreshFavorites()
  ElMessage.success(userStore.isFavorite('convertible', row.bondCode) ? '已添加自选' : '已取消自选')
}

function goDetail(code) {
  if (!code) return
  router.push(`/convertible/${code}`)
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } catch {
    ElMessage.warning('复制失败')
  }
}

function formatPremiumMedian(v) {
  if (v == null || v === '--') return '--'
  return v + '%'
}

function exchangeClass(ex) {
  return { '沪': 'ex-sh', '深': 'ex-sz', '京': 'ex-bj' }[ex] || ''
}

function riskTagType(cls) {
  return { high: 'danger', mid: 'warning', low: 'success' }[cls] || 'info'
}

function safetyPadClass(raw) {
  if (raw == null) return ''
  if (raw > 8) return 'positive'
  if (raw > 3) return 'warning'
  return 'negative'
}

function trendClass(raw) {
  if (raw > 0) return 'up'
  if (raw < 0) return 'down'
  return ''
}

let mql
function updateMobile(e) { isMobile.value = e.matches }

onMounted(() => {
  store.loadAll()
  mql = window.matchMedia('(max-width: 768px)')
  isMobile.value = mql.matches
  mql.addEventListener('change', updateMobile)
})

onActivated(() => {
  store.refreshFavorites()
})

onUnmounted(() => {
  if (mql) mql.removeEventListener('change', updateMobile)
})
</script>

<style lang="scss" scoped>
.convertible-page {
  .page-header-flex {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;

    .search-input {
      max-width: 280px;
    }
  }

  .market-overview {
    background: var(--el-fill-color-light);
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;

    .overview-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;

      .overview-title {
        font-size: 15px;
        font-weight: 600;
        color: var(--text-color);
      }
    }

    .overview-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
    }

    .overview-item {
      text-align: center;

      .overview-value {
        font-size: 24px;
        font-weight: 700;
        color: var(--text-color);
        line-height: 1.2;
      }

      .overview-label {
        font-size: 12px;
        color: var(--text-color-secondary);
        margin-top: 4px;
      }
    }
  }

  .tab-bar {
    display: flex;
    gap: 4px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    margin-bottom: 12px;
    flex-wrap: wrap;

    .tab-btn {
      position: relative;
      padding: 8px 16px;
      border: none;
      background: transparent;
      cursor: pointer;
      color: var(--text-color-secondary);
      font-size: 14px;
      border-bottom: 2px solid transparent;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      gap: 6px;

      &:hover { color: var(--el-color-primary); }

      &.active {
        color: var(--el-color-primary);
        border-bottom-color: var(--el-color-primary);
        font-weight: 600;
      }

      .tab-count {
        display: inline-block;
        min-width: 18px;
        padding: 0 6px;
        height: 18px;
        line-height: 18px;
        border-radius: 9px;
        background: var(--el-fill-color);
        color: var(--text-color-secondary);
        font-size: 11px;
        text-align: center;

        &.hot { background: var(--el-color-danger); color: #fff; }
      }
    }
  }

  .guide-alert {
    margin-bottom: 12px;
  }

  .sandbox-card {
    margin-bottom: 12px;

    .sandbox-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      cursor: pointer;
      user-select: none;

      .sandbox-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-color);
      }

      .sandbox-toggle {
        transition: transform 0.2s;
        color: var(--text-color-secondary);

        &.expanded {
          transform: rotate(180deg);
        }
      }
    }

    .sandbox-body {
      display: flex;
      gap: 24px;
      flex-wrap: wrap;

      .sandbox-sliders {
        flex: 1;
        min-width: 240px;
      }

      .sandbox-result {
        min-width: 200px;
        padding: 12px 16px;
        background: var(--bg-color);
        border-radius: 8px;

        .result-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 8px;

          .result-label {
            font-size: 13px;
            color: var(--text-color-secondary);
          }

          .result-value {
            font-size: 16px;
            font-weight: 700;
            color: var(--text-color);

            &.low {
              color: var(--el-color-success);
            }
          }
        }

        .result-tip {
          font-size: 12px;
          color: var(--el-color-success);

          &.warn {
            color: var(--el-color-warning);
          }
        }
      }
    }
  }

  .expand-enter-active, .expand-leave-active {
    transition: all 0.2s ease;
  }

  .expand-enter-from, .expand-leave-to {
    opacity: 0;
    max-height: 0;
  }

  .tab-content {
    .sub-toolbar {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 12px;

      .sub-tabs {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
      }

      .sub-btn {
        padding: 4px 12px;
        border: 1px solid var(--el-border-color);
        border-radius: 14px;
        background: transparent;
        cursor: pointer;
        font-size: 12px;
        color: var(--text-color-regular);

        .sub-count {
          margin-left: 4px;
          color: var(--text-color-secondary);
          &.hot { color: var(--el-color-danger); }
        }

        &.active {
          border-color: var(--el-color-primary);
          color: var(--el-color-primary);
          background: var(--el-color-primary-light-9);
        }
      }

      .sort-row {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
      }

      .sort-btn {
        padding: 4px 10px;
        border: none;
        background: transparent;
        cursor: pointer;
        font-size: 12px;
        color: var(--text-color-secondary);

        &:hover { color: var(--el-color-primary); }

        &.active {
          color: var(--el-color-primary);
          font-weight: 600;
        }
      }
    }
  }

  .name-cell {
    .name-line {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }

    .code-line {
      margin-top: 2px;
      font-size: 12px;
      color: var(--text-color-secondary);
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }

    .bond-name { font-weight: 600; color: var(--text-color); }
    .code-text { color: var(--text-color-secondary); }
    .stock-name { color: var(--text-color-secondary); }
    .code-price { color: var(--text-color-regular); }
    .code-change {
      &.up { color: var(--el-color-danger); }
      &.down { color: var(--el-color-success); }
    }
    .code-sep { color: var(--el-border-color); }
    .progress-tag {
      padding: 0 6px;
      border-radius: 3px;
      font-size: 11px;
      background: var(--el-fill-color);
      &.hot { background: rgba(245, 108, 108, 0.12); color: var(--el-color-danger); }
      &.warm { background: rgba(230, 162, 60, 0.12); color: var(--el-color-warning); }
    }
  }

  .exchange-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    font-size: 11px;
    color: #fff;

    &.ex-sh { background: #d4380d; }
    &.ex-sz { background: #0958d9; }
    &.ex-bj { background: #531dab; }
  }

  /* 评级 tag：推荐绿/可关注黄/谨慎红，兼容暗黑模式 */
  .rating-tag {
    border: none;

    &.rating-recommend {
      background-color: var(--el-color-success);
      color: #fff;
    }
    &.rating-watch {
      background-color: var(--el-color-warning);
      color: #fff;
    }
    &.rating-caution {
      background-color: var(--el-color-danger);
      color: #fff;
    }
  }

  .fav-icon {
    cursor: pointer;
    color: var(--el-border-color);
    font-size: 16px;
    &.active { color: #fadb14; }
    &:hover { color: #fadb14; }
  }

  .hl { color: var(--el-color-primary); font-weight: 600; }
  .price-sub { font-size: 12px; color: var(--text-color-secondary); }

  .premium-value {
    &.negative { color: var(--el-color-success); }
    &.high { color: var(--el-color-danger); }
  }

  .positive { color: var(--el-color-success); font-weight: 600; }
  .warning { color: var(--el-color-warning); font-weight: 600; }
  .negative { color: var(--el-color-danger); font-weight: 600; }
  .up { color: var(--el-color-danger); }
  .down { color: var(--el-color-success); }

  .sub-info {
    font-size: 12px;
    color: var(--text-color-secondary);
    &.onehand { color: var(--el-color-warning); }
  }

  .hover-value {
    cursor: help;
    border-bottom: 1px dashed var(--text-color-secondary);
    padding-bottom: 1px;
    transition: border-color 0.2s;
    &:hover {
      border-bottom-color: var(--el-color-primary);
    }
  }

  .show-all-bar {
    text-align: center;
    margin-top: 12px;
  }

  .mobile-cards {
    display: none;
  }

  /* 待发详情弹窗 */
  .detail-section {
    margin-bottom: 18px;

    .detail-section-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-color);
      margin-bottom: 8px;
      padding-left: 8px;
      border-left: 3px solid var(--el-color-primary);
    }

    .detail-label-section {
      font-size: 13px;
      color: var(--text-color-secondary);
    }
  }

  /* 发行时间轴节点描述 */
  .stage-date {
    font-size: 12px;
    color: var(--text-color-secondary);
    line-height: 1.4;
    white-space: nowrap;
  }

  .stage-days {
    font-size: 11px;
    font-weight: 600;
    line-height: 1.4;
    margin-top: 2px;

    &.today {
      color: var(--el-color-danger);
    }
    &.future {
      color: var(--el-color-warning);
    }
    &.past {
      color: var(--text-color-secondary);
    }
  }

  .stage-reg-info {
    font-size: 11px;
    line-height: 1.4;
    margin-top: 2px;
    color: var(--el-color-warning);
  }

  .stage-progress-info {
    display: flex;
    gap: 12px;
    margin-bottom: 14px;
    padding: 12px;
    background: var(--el-fill-color-light);
    border-radius: 8px;

    .stage-progress-item {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 0 8px;

      &.current {
        border-left: 3px solid var(--el-color-primary);

        .stage-progress-label {
          color: var(--el-color-primary);
        }
      }

      &.next {
        border-left: 3px solid var(--el-color-warning);

        .stage-progress-label {
          color: var(--el-color-warning);
        }

        .stage-progress-date {
          color: var(--el-color-warning);
        }
      }
    }

    .stage-progress-label {
      font-size: 11px;
      font-weight: 600;
      color: var(--text-color-secondary);
    }

    .stage-progress-value {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-color);
      line-height: 1.4;
    }

    .stage-progress-date {
      font-size: 12px;
      font-weight: 400;
      color: var(--el-color-primary);
      margin-left: 4px;
    }
  }

  .detail-timeline {
    padding-top: 4px;
  }

  .slider-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;

    .slider-value {
      font-size: 16px;
      font-weight: 700;
      color: var(--el-color-warning);
    }
  }

  .slider-hint {
    font-size: 12px;
    color: var(--text-color-secondary);
    margin-top: 4px;
  }

  .sector-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .detail-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;

    .detail-item {
      background: var(--el-fill-color-light);
      border-radius: 6px;
      padding: 8px 10px;

      &.hl-box {
        background: var(--el-color-primary-light-9);
      }

      .detail-label {
        display: block;
        font-size: 12px;
        color: var(--text-color-secondary);
        margin-bottom: 4px;
      }

      .detail-value {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-color);
        border-bottom: 1px dashed var(--text-color-secondary);
        padding-bottom: 1px;

        &.hl { color: var(--el-color-primary); }
        &.copyable { cursor: pointer; &:hover { color: var(--el-color-primary); } }
      }
    }
  }

  /* 响应式 */
  @media (max-width: 768px) {
    .page-header-flex {
      flex-direction: column;
      align-items: stretch;
      .search-input { max-width: 100%; }
    }

    .market-overview .overview-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .desktop-table { display: none; }
    .mobile-cards {
      display: block;

      .mobile-card {
        margin-bottom: 10px;
        cursor: pointer;
      }

      .mc-head {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
        .bond-name { font-weight: 600; }
      }

      .mc-code {
        margin-top: 4px;
        font-size: 12px;
        color: var(--text-color-secondary);
        display: flex;
        gap: 8px;
        align-items: center;
      }

      .mc-metrics {
        margin-top: 8px;
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 6px;
        font-size: 13px;

        .mc-label {
          display: inline-block;
          min-width: 40px;
          color: var(--text-color-secondary);
          margin-right: 4px;
        }
      }
    }

    .detail-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (min-width: 769px) and (max-width: 1199px) {
    .detail-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
}
</style>

<style lang="scss">
.dialog-header-stock {
  display: flex;
  align-items: center;
  gap: 8px;

  .dialog-stock-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  .ext-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 4px;
    color: var(--el-text-color-secondary);
    text-decoration: none;
    transition: all 0.2s;

    &:hover {
      color: var(--el-color-primary);
      background: var(--el-color-primary-light-9);
    }

    .el-icon {
      font-size: 14px;
    }
  }
}

.formula-tip {
  font-size: 12px;
  line-height: 1.7;
  min-width: 260px;
  max-width: 360px;

  .ft-formula {
    font-size: 13px;
    font-weight: 600;
    color: #409eff;
    margin-bottom: 8px;
    padding: 4px 8px;
    background: rgba(64, 158, 255, 0.1);
    border-radius: 4px;
    border-left: 3px solid #409eff;
  }

  .ft-section {
    margin-bottom: 4px;
  }

  .ft-detail {
    color: var(--el-text-color-secondary);
    padding: 1px 0;

    b {
      color: var(--el-text-color-primary);
      font-weight: 600;
    }
  }

  .ft-note {
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px dashed var(--el-border-color);
    color: var(--el-text-color-secondary);
    font-size: 11px;
    font-style: italic;
  }

  .ft-divider {
    height: 1px;
    background: var(--el-border-color-darker);
    margin: 8px 0;
    opacity: 0.4;
  }

  .ft-subtitle {
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin-bottom: 4px;
    font-size: 12px;
  }
}
</style>
