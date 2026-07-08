# 策略分级基础设施 Spec

## Why

A/H 股套利策略存在天然的资金门槛和风险差异，从 LOF 基金套利（≤1万）到股指期货基差套利（≥50万），新手和专业投资者需要不同的策略。当前项目缺乏统一的分级标注系统，用户无法快速判断策略的适用性。

## What Changes

### 新增：TierBadge 通用组件

- **新增** `src/components/TierBadge.vue`：极简细线胶囊标签，接收 `tier`、`threshold`、`showLabel` 三个 prop
- **新增** `src/data/strategyTiers.js`：分级常量定义（颜色映射、阈值范围、标签文本）

### 修改：各 Store 暴露分级信息

- **修改** `src/stores/lof.js`：在 state/getter 中暴露 `tier: 'beginner'`、`threshold: 10000`
- **修改** `src/stores/convertible.js`：在 state/getter 中暴露 `tier: 'beginner'`、`threshold: 10000`
- **修改** `src/stores/hkipo.js`：在 state/getter 中暴露 `tier: 'beginner'`、`threshold: 10000`

### 修改：视图层接入标签

- **修改** `src/views/Convertible.vue`：列表卡片标题行右侧添加 TierBadge
- **修改** `src/views/Lof.vue`：列表卡片标题行右侧添加 TierBadge
- **修改** `src/views/Hkipo.vue`：列表卡片标题行右侧添加 TierBadge
- **修改** `src/views/BondDetail.vue`：详情页头部添加 TierBadge
- **修改** `src/views/HkipoDetail.vue`：详情页头部添加 TierBadge

## Impact

- Affected code:
  - 新增：`src/components/TierBadge.vue`、`src/data/strategyTiers.js`
  - 修改：`src/stores/lof.js`、`src/stores/convertible.js`、`src/stores/hkipo.js`
  - 修改：`src/views/Convertible.vue`、`src/views/Lof.vue`、`src/views/Hkipo.vue`、`src/views/BondDetail.vue`、`src/views/HkipoDetail.vue`

## Requirements

### Requirement: TierBadge 组件

`TierBadge.vue` SHALL 渲染一个细线胶囊标签，以极简风格展示策略分级。

#### Scenario: 入门级标签

- **WHEN** `tier='beginner'`、`threshold=10000`
- **THEN** 渲染绿色细线胶囊 `入门 · ≤1万`
- **AND** 边框颜色 `#52c41a`，文字颜色 `#52c41a`

#### Scenario: 进阶级标签

- **WHEN** `tier='advanced'`、`threshold=10000`
- **THEN** 渲染黄色细线胶囊 `进阶 · 1-50万`
- **AND** 边框颜色 `#faad14`，文字颜色 `#faad14`

#### Scenario: 专业级标签

- **WHEN** `tier='professional'`、`threshold=500000`
- **THEN** 渲染红色细线胶囊 `专业 · ≥50万`
- **AND** 边框颜色 `#ff4d4f`，文字颜色 `#ff4d4f`

#### Scenario: 不显示门槛

- **WHEN** `threshold` 未传入或为 0
- **THEN** 仅显示级别文字（如 `入门`），不显示门槛金额

#### Scenario: 纯图标模式

- **WHEN** `showLabel=false`
- **THEN** 仅显示彩色圆点（8px），不显示文字，适合空间受限场景

### Requirement: 分级常量定义

`strategyTiers.js` SHALL 定义分级相关的纯常量，不绑定具体策略。

#### Scenario: 颜色映射

- **WHEN** 需要获取分级颜色
- **THEN** `TIER_COLORS = { beginner: '#52c41a', advanced: '#faad14', professional: '#ff4d4f' }`

#### Scenario: 标签映射

- **WHEN** 需要获取分级文本
- **THEN** `TIER_LABELS = { beginner: '入门', advanced: '进阶', professional: '专业' }`

#### Scenario: 阈值范围

- **WHEN** 需要获取门槛描述
- **THEN** `TIER_THRESHOLDS = { beginner: '≤1万', advanced: '1-50万', professional: '≥50万' }`

### Requirement: Store 分级信息暴露

各策略 Store SHALL 在 state 或 getter 中暴露 `tier` 和 `threshold` 字段。

#### Scenario: LOF store

- **WHEN** 访问 `lofStore.tier`
- **THEN** 返回 `'beginner'`
- **AND** `lofStore.threshold` 返回 `10000`

#### Scenario: Convertible store

- **WHEN** 访问 `convertibleStore.tier`
- **THEN** 返回 `'beginner'`
- **AND** `convertibleStore.threshold` 返回 `10000`

#### Scenario: HKIPO store

- **WHEN** 访问 `hkipoStore.tier`
- **THEN** 返回 `'beginner'`
- **AND** `hkipoStore.threshold` 返回 `10000`

### Requirement: 视图层标签接入

各策略页面 SHALL 在合适位置展示 TierBadge 组件。

#### Scenario: 列表页卡片

- **WHEN** 渲染策略列表卡片
- **THEN** 卡片标题行右侧展示 TierBadge
- **AND** 标签不遮挡主要数据，仅作为辅助标注

#### Scenario: 详情页头部

- **WHEN** 渲染策略详情页
- **THEN** 页面头部（策略名称旁）展示 TierBadge
- **AND** hover 时显示完整门槛说明

## Design Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| 标签角色 | 轻量标签，非导航骨架 | 用户偏好极简风格，辅助信息应低调 |
| 视觉风格 | 细线胶囊（border + 文字） | 包含门槛金额，信息量适中，极简不抢眼 |
| 分级配置 | 分散在各 Store 中维护 | 每个策略独立管理，灵活扩展 |
| 颜色方案 | 绿/黄/红三色 | 符合直觉：绿=安全低门槛，黄=注意，红=高风险 |

## Out of Scope

- 策略分级筛选/过滤功能（后续迭代）
- 按分级组织的侧边栏导航（用户明确拒绝）
- 新策略的 Store 和 API（属于其他子系统）