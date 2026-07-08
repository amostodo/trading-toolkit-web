/**
 * 策略分级常量
 * 不绑定具体策略，纯工具级常量
 */

// 分级颜色映射
export const TIER_COLORS = {
  beginner: '#52c41a',
  advanced: '#faad14',
  professional: '#ff4d4f'
}

// 分级标签文本
export const TIER_LABELS = {
  beginner: '入门',
  advanced: '进阶',
  professional: '专业'
}

// 分级门槛描述
export const TIER_THRESHOLDS = {
  beginner: '≤1万',
  advanced: '1-50万',
  professional: '≥50万'
}

// 分级完整说明（hover tooltip 用）
export const TIER_DESCRIPTIONS = {
  beginner: '低风险、低门槛，适合新手投资者',
  advanced: '中等风险、有一定门槛，适合有经验投资者',
  professional: '高风险、高门槛，适合机构或专业投资者'
}

/**
 * 根据 tier 获取完整的展示信息
 * @param {string} tier - 'beginner' | 'advanced' | 'professional'
 * @returns {{ color: string, label: string, threshold: string, description: string }}
 */
export function getTierInfo(tier) {
  return {
    color: TIER_COLORS[tier] || '#999',
    label: TIER_LABELS[tier] || '未知',
    threshold: TIER_THRESHOLDS[tier] || '',
    description: TIER_DESCRIPTIONS[tier] || ''
  }
}
