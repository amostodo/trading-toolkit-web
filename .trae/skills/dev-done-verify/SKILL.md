---
name: "dev-done-verify"
description: "Enforces runtime verification before claiming development complete. Invoke after implementing features/fixes and BEFORE reporting done/completed/tested to user. Prevents false completion claims by requiring real runtime evidence (process, API, rendered content, interactions, zero errors)."
---

# Development Done Verification

**强制性运行时验证协议 — 在向用户报告"完成/done/已实现/已测试"之前必须执行。**

## 何时触发（MANDATORY）

出现以下任一情况必须立即调用本 skill：
- 即将向用户报告"完成" / "done" / "已实现" / "已测试" / "通过"
- 标记 todo 为 `completed`
- 完成功能或修复的实现阶段
- 撰写工作总结 / 完成报告

**核心原则：实现完成 ≠ 验证完成 ≠ 功能可用。三者必须全部通过才能报告"完成"。**

## 本 skill 解决的问题

过往错误的"完成"判定模式：

| 错误判定 | 真实含义 |
|---------|---------|
| ❌ Build 通过 → 完成 | 只是代码能编译，不代表能跑 |
| ❌ HTTP 200 → 可用 | 只是 HTML 加载，不代表 API 通 |
| ❌ Mock 兜底有数据 → 链路通 | 假数据掩盖了集成失败 |
| ❌ 元素数量 > 0 → 渲染正确 | 有行不代表数据正确 |
| ❌ 静态分析 → 通过 | 没做运行时验证 |

**正确判定：必须看到真实运行的进程、真实返回的 API 数据、真实渲染的页面文本内容、零错误日志。**

## 验证协议（5 层全部必过）

### Layer 1: 服务运行时检查

**后端服务**：
```
netstat -ano | findstr :8080 | findstr LISTENING
```
- 必须返回 LISTENING 行
- 记录 PID，不能只说"已启动"

**前端 dev server**：
- HTTP 请求返回 200
- 响应体包含实际 HTML（不是错误页）

### Layer 2: API 真实数据检查

对功能依赖的每个 API 端点：
```powershell
$r = Invoke-WebRequest -Uri 'http://localhost:8080/api/v1/xxx' -UseBasicParsing
$j = $r.Content | ConvertFrom-Json
# 验证 source 字段（区分 akshare/cache/mock/none）
# 验证 data 数组/对象有实际内容
# 输出第一项的实际字段值（不是字段名）
```

**强制要求**：
- `source` 字段不能是 `mock` / `none`（如果是必须在 UI 标注「示例数据」）
- `data` 不能为空数组
- 必须输出第一行的实际文本值

### Layer 3: 前端运行时渲染

使用 Playwright（优先）或浏览器检查：
```python
page.goto("http://localhost:5173/xxx")
page.wait_for_load_state("networkidle", timeout=30000)
page.wait_for_timeout(2000)
page.screenshot(path="evidence.png", full_page=True)

# 验证具体文本内容，不是元素数量
first_row = page.locator(".el-table__row").first
text = first_row.inner_text()
# 必须输出实际文本，不能只说"有行"
```

**禁止**：用 `count() > 0` 作为通过标准。

### Layer 4: 交互验证

对交互式功能（按钮、滑块、Tab、拖拽）：
- 实际点击 / 拖动
- 验证点击后状态发生变化
- 验证计算值实时更新
- 截图 before/after 作为证据

### Layer 5: 错误扫描

```python
page.on("console", lambda msg: errors.append(msg) if msg.type in ("error","warning") else None)
page.on("pageerror", lambda err: page_errors.append(err))
page.on("requestfailed", lambda req: failed.append(req))
```

**强制要求**（全部必须满足）：
- 0 console 错误
- 0 页面 JS 异常
- 0 失败网络请求（404 / 500 / CORS / Network Error）
- 0 mock 兜底指示器出现在 UI

## 完成报告必须包含的证据

每次"完成"报告必须包含以下 5 项实际证据，缺一不可：

1. **后端**：PID + 监听端口 + curl 响应中的 `source` 字段值
2. **前端**：实际页面 URL + Playwright 截图路径
3. **数据样本**：第一行的实际文本内容（如 `180901 - 润泽REIT`，不是"有数据"）
4. **错误统计**：console 错误数 + 失败请求数（两者必须为 0）
5. **交互证据**（如有交互功能）：before/after 状态差异

## Todo 状态纪律

- `in_progress`：正在做
- `pending`：未开始
- `completed`：**仅当 5 层验证全部通过后**才能标记
- 禁止用 `completed` 表示"实现完成但未验证"
- 如需中间态，用「实现完成,待验证」文字描述，状态保持 `in_progress`

## Mock 数据处理规则

如果功能依赖 mock 兜底：
1. UI **必须**显示「示例数据」徽章
2. 完成报告**必须**明确说明 mock 在使用
3. 用户**必须**被告知"当前是 mock 数据，非真实链路"
4. 后端集成不算完成，todo 不得标记 completed

## 禁止模式（Anti-Patterns）

❌ "Build 通过 → 完成"
❌ "HTTP 200 → 可用"
❌ "元素数量 > 0 → 渲染正确"
❌ "Mock 兜底 → 可接受"（必须标注示例数据）
❌ 验证前标记 todo completed
❌ 无 Playwright/浏览器证据就报告"已测试"
❌ 用"应该"、"理论上"、"代码逻辑上"作为通过依据
❌ 跳过任何一层验证就报告完成

## 正确模式

✅ 看到真实进程 PID
✅ 看到真实 API JSON 响应（含 source 字段）
✅ 看到页面第一行实际文本内容
✅ 看到 0 错误的 console 日志
✅ 看到交互前后的状态变化截图

## 执行顺序

1. 实现完成 → 标记 todo 为「实现完成,待验证」（保持 in_progress）
2. 启动后端 → Layer 1 验证
3. curl API → Layer 2 验证
4. 启动 Playwright → Layer 3 验证
5. 执行交互 → Layer 4 验证
6. 扫描错误 → Layer 5 验证
7. 全部通过 → 标记 todo completed
8. 撰写完成报告（含 5 项证据）
9. 报告用户
