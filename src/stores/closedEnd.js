import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { closedEndApi } from '@/api/closedEnd'
import { useAppStore } from '@/stores/app'

function safeNum(val, def = 0) {
  return typeof val === 'number' && !isNaN(val) ? val : def
}

function normalizeFundItem(raw) {
  if (!raw || typeof raw !== 'object') return null
  const nav = safeNum(raw.nav)
  const price = safeNum(raw.price)
  // 后端已计算 discount，避免重复计算
  const discount = raw.discount != null ? safeNum(raw.discount)
    : (nav > 0 ? ((nav - price) / nav * 100) : 0)
  const maturityDate = raw.maturity_date || ''
  const today = new Date()
  const maturity = new Date(maturityDate)
  const yearsToMaturity = maturityDate && !isNaN(maturity)
    ? Math.max(0, (maturity - today) / (365.25 * 24 * 3600 * 1000))
    : 0
  const annualizedDiscount = yearsToMaturity > 0 ? discount / yearsToMaturity : 0

  const changePct = safeNum(raw.change_pct)
  const amount = safeNum(raw.amount)

  return {
    code: raw.code || '',
    name: raw.name || '--',
    exchange: raw.exchange || '',
    nav: nav ? nav.toFixed(4) : '--',
    navRaw: nav,
    navDate: raw.nav_date || '',
    price: price ? price.toFixed(3) : '--',
    priceRaw: price,
    changePct: changePct != null ? (changePct >= 0 ? '+' : '') + changePct.toFixed(2) + '%' : '--',
    changePctRaw: changePct,
    changeClass: changePct > 0 ? 'up' : changePct < 0 ? 'down' : '',
    amount: amount >= 1e8 ? (amount / 1e8).toFixed(2) + ' 亿'
      : amount >= 1e4 ? (amount / 1e4).toFixed(0) + ' 万'
      : amount > 0 ? amount.toFixed(0) : '--',
    amountRaw: amount,
    discount: discount != null ? (discount > 0 ? '+' : '') + discount.toFixed(2) + '%' : '--',
    discountRaw: discount,
    discountClass: discount >= 15 ? 'high' : discount >= 5 ? 'mid' : discount < 0 ? 'premium' : '',
    annualizedDiscount: yearsToMaturity > 0 ? annualizedDiscount.toFixed(2) + '%' : '--',
    annualizedRaw: annualizedDiscount,
    maturityDate,
    yearsToMaturity: yearsToMaturity ? yearsToMaturity.toFixed(2) + ' 年' : '--',
    yearsRaw: yearsToMaturity,
    size: raw.size ? raw.size.toFixed(2) + ' 亿' : '--',
    sizeRaw: safeNum(raw.size),
    topHoldings: raw.top_holdings || [],
    type: raw.type || '封闭式基金',
    isFavorite: false
  }
}

function computeSummary(list) {
  if (!list.length) return null
  // 仅对有净值的基金计算折价统计（discountRaw 可能是 0 表示无折溢价，需用 navRaw>0 判断有效性）
  const withNav = list.filter(i => i.navRaw > 0)
  const discounts = withNav.map(i => i.discountRaw)
  const avgDiscount = discounts.length
    ? discounts.reduce((a, b) => a + b, 0) / discounts.length
    : 0
  const highDiscountCount = withNav.filter(i => i.discountRaw >= 5).length
  const premiumCount = withNav.filter(i => i.discountRaw < 0).length
  const nearMaturityCount = list.filter(i => i.yearsRaw > 0 && i.yearsRaw <= 1).length
  return {
    count: list.length,
    avg_discount: avgDiscount.toFixed(2),
    high_discount_count: highDiscountCount,
    premium_count: premiumCount,
    near_maturity_count: nearMaturityCount
  }
}

export const useClosedEndStore = defineStore('closedEnd', () => {
  const fundList = ref([])
  const summary = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const tier = 'beginner'
  const threshold = 10000
  const lastUpdated = ref(null)

  // Mock 数据（后端 API 未就绪时的兜底）
  const mockData = [
    { code: '505888', name: '科创50ETF封闭', nav: 1.0234, price: 0.952, maturity_date: '2027-06-30', size: 28.5, top_holdings: ['中芯国际', '海光信息', '中微公司'] },
    { code: '505999', name: '创新药封闭', nav: 1.1567, price: 0.985, maturity_date: '2026-12-15', size: 15.2, top_holdings: ['恒瑞医药', '药明康德', '百济神州'] },
    { code: '506000', name: '新能源封闭', nav: 0.8945, price: 0.721, maturity_date: '2025-09-30', size: 12.8, top_holdings: ['宁德时代', '隆基绿能', '通威股份'] },
    { code: '506111', name: '消费封闭', nav: 1.3456, price: 1.198, maturity_date: '2028-03-15', size: 8.6, top_holdings: ['贵州茅台', '五粮液', '伊利股份'] },
    { code: '506222', name: '半导体封闭', nav: 1.5678, price: 1.235, maturity_date: '2026-06-30', size: 10.3, top_holdings: ['北方华创', '韦尔股份', '兆易创新'] },
    { code: '506333', name: '军工封闭', nav: 1.0892, price: 0.912, maturity_date: '2027-01-15', size: 6.5, top_holdings: ['中航沈飞', '航发动力', '中航光电'] },
    { code: '506444', name: '金融封闭', nav: 1.2345, price: 1.089, maturity_date: '2025-12-31', size: 22.1, top_holdings: ['招商银行', '中信证券', '中国平安'] },
    { code: '506555', name: '科技封闭', nav: 1.4567, price: 1.312, maturity_date: '2028-09-30', size: 18.7, top_holdings: ['海康威视', '科大讯飞', '立讯精密'] }
  ]

  async function loadAll() {
    loading.value = true
    error.value = null
    try {
      let raw = []
      try {
        const data = await closedEndApi.list()
        raw = Array.isArray(data) ? data : (data.items || [])
      } catch {
        // 后端 API 未就绪，使用 mock 数据
        raw = mockData
      }
      const normalized = raw.map(normalizeFundItem).filter(Boolean)
      fundList.value = normalized
      summary.value = computeSummary(normalized)
      lastUpdated.value = new Date().toISOString()
      useAppStore().setLastUpdated()
    } catch (err) {
      error.value = err?.message || '加载失败'
    } finally {
      loading.value = false
    }
  }

  return {
    fundList, summary, loading, error,
    tier, threshold, lastUpdated,
    loadAll
  }
})
