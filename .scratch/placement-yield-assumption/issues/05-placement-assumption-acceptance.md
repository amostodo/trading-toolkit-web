# 05 - 配债收益假设验收与说明

**Parent:** 01 - Global Placement Yield Assumption

**What to build:** 用户获得可验证、可解释的配债收益假设体验，且该假设不会影响双低、强赎、折价、下修或 LOF 等其他策略。

**Blocked by:** 02 - 默认收益假设的配债指标; 03 - 可调整且持久化的收益假设; 04 - 配债详情与移动端假设一致性

**Status:** resolved

- [x] 确定性浏览器验证覆盖默认值、边界、缓存、重置、排序、详情和移动端一致性。
- [x] 验证非配债可转债策略与 LOF 的数据、排序和展示不受影响。
- [x] 更新配债评分与成本说明，明确收益假设不是市场行情、已验证收益或可执行结果。
- [x] 运行 OpenSpec 校验、格式检查、生产构建和桌面/移动端检查。

## Answer

The deterministic Playwright script now verifies calculation boundaries, persistence, reset, ranking, open-detail and mobile consistency, and strategy isolation. Placement documentation now identifies the value as a scenario assumption rather than a market or execution result.

## Comments

- 2026-07-22: Browser verification, production build, OpenSpec validation, diff whitespace check, and targeted Prettier check were run. Prettier reports legacy formatting differences in the touched historical documents and test; no bulk rewrite was applied.
