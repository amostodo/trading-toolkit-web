# 全局工作任务自动化记录计划

## 1. 需求理解

用户需要一个自动化任务，能够：
- 从 TRAE 内存系统（session_memory、topics.md、project_memory.md）收集工作记录
- 将数据格式化为 Obsidian 友好的 Markdown 格式
- 通过 Obsidian CLI 写入到 defNote vault
- 持续更新，保持与最新工作进度同步

## 2. 数据来源分析

| 数据源 | 路径 | 内容描述 |
|--------|------|----------|
| session_memory | `c:\Users\Administrator\.trae-cn\memory\projects\-d-Develop-GitHub-trading-toolkit-web\YYYYMMDD\session_memory_*.jsonl` | 每次会话的完整记录（intent/actions/outcome/learned） |
| topics.md | `c:\Users\Administrator\.trae-cn\memory\projects\-d-Develop-GitHub-trading-toolkit-web\YYYYMMDD\topics.md` | 每日主题汇总 |
| project_memory.md | `c:\Users\Administrator\.trae-cn\memory\projects\-d-Develop-GitHub-trading-toolkit-web\project_memory.md` | 项目级规则、约束、约定 |

## 3. 输出目标

### 3.1 每日工作记录（追加到日记）
- 文件路径：`wiki/diary/YYYY-MM-DD.md`
- 内容结构：在现有日记末尾追加 `## 🤖 TRAE 工作记录` section
- **符合仓库约束**：`.gitignore` 未忽略 `wiki/diary/`，daily-notes 插件已启用，符合 vault 结构

### 3.2 项目工作汇总（独立文件）
- 文件路径：`wiki/projects/trading-toolkit-worklog.md`
- 内容结构：项目级工作汇总，包含所有会话记录的聚合视图
- **符合仓库约束**：`wiki/projects/` 目录已存在，包含多个项目相关 markdown 文件（如 `2021-618-总结.md`、`tgang.md`、`维权资料.md` 等），`.gitignore` 未忽略该目录

## 4. 实现方案

### 4.1 创建核心脚本

**文件：** `d:\Develop\GitHub\trading-toolkit-web\.trae\scripts\trae-worklog.py`

功能：
- 读取指定日期范围的 session_memory JSONL 文件
- 解析 topics.md 和 project_memory.md
- 生成 Obsidian 格式的 Markdown 内容
- 通过 Obsidian CLI (`C:\Program Files\Obsidian\Obsidian.com`) 写入 vault

### 4.2 创建调度任务

使用 TRAE Schedule 工具创建每日定时任务：
- **执行时间**：每天晚上 23:30（收集当天数据）
- **任务内容**：运行 `trae-worklog.py` 生成并写入当日工作记录

### 4.3 脚本核心逻辑

```python
# 1. 读取 session_memory 数据
def read_session_memory(date_str):
    # 读取 YYYYMMDD 目录下所有 session_memory_*.jsonl
    
# 2. 读取 topics.md
def read_topics(date_str):
    # 读取当日 topics.md
    
# 3. 生成每日工作记录
def generate_daily_log(date_str, sessions, topics):
    # 格式化为 Obsidian Callout 格式
    
# 4. 写入 Obsidian
def write_to_obsidian(content, vault="defnote", path="wiki/diary/YYYY-MM-DD.md"):
    # 使用 obsidian-cli 写入，带 try-catch 重试机制
```

## 5. 文件和模块修改

| 文件 | 操作 | 说明 |
|------|------|------|
| `.trae/scripts/trae-worklog.py` | 新建 | 核心脚本，收集数据并写入 Obsidian |
| `.trae/scripts/__init__.py` | 新建 | 模块初始化文件 |

## 6. 步骤

### 步骤 1：创建脚本目录和核心脚本
- 创建 `.trae/scripts/` 目录
- 编写 `trae-worklog.py` 脚本

### 步骤 2：测试脚本
- 手动运行脚本测试数据收集和写入功能
- 验证 Obsidian 中内容是否正确显示

### 步骤 3：创建定时任务
- 使用 Schedule 工具创建每日 23:30 执行的任务

### 步骤 4：验证自动化
- 等待任务自动执行，检查结果

## 7. 潜在依赖和注意事项

### 7.1 依赖
- **Obsidian CLI**：已启用（用户确认）
- **Python**：系统已有（`where python` 验证）
- **Obsidian 运行中**：CLI 需要 Obsidian 保持打开状态

### 7.2 风险与处理（增强 try-catch）

| 风险 | 影响 | 处理方案 |
|------|------|----------|
| **Obsidian 关闭** | CLI 无法工作，任务失败 | **try-catch + 重试机制**：检测 CLI 失败后重试 3 次，每次间隔 10 秒；全部失败则写入本地日志文件，等待下次执行 |
| **数据路径变更** | TRAE 内存路径可能随版本变更 | **路径配置化**：在脚本开头使用配置变量，便于维护；异常时捕获 FileNotFoundError |
| **并发写入** | 多个任务同时写入可能冲突 | **时间戳锁定**：写入前检查文件修改时间，避免同一分钟多次写入；加文件锁 |
| **CLI 命令超时** | 命令执行时间过长 | **超时控制**：使用 subprocess 带 timeout 参数，超时后重试 |
| **内容截断** | PowerShell here-string 转义问题导致内容截断 | **文件中转**：先写入临时文件，再通过 CLI 读取文件内容写入，避免命令行参数长度限制 |

### 7.3 脚本错误处理结构

```python
def main():
    try:
        # 1. 读取数据
        sessions = read_session_memory(date_str)
        topics = read_topics(date_str)
        
        # 2. 生成内容
        content = generate_daily_log(date_str, sessions, topics)
        
        # 3. 写入 Obsidian（带重试）
        for attempt in range(3):
            try:
                write_to_obsidian(content, vault="defnote", path=diary_path)
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(10)
                else:
                    # 记录失败日志
                    log_error(f"写入失败: {e}")
                    # 保存到本地备份
                    save_backup(content, date_str)
                    
    except Exception as e:
        # 全局异常捕获
        log_error(f"脚本执行失败: {e}")
        save_backup(content, date_str)
```

## 8. 安全考虑

- 脚本仅读取 TRAE 内存目录（只读）
- 写入操作仅针对 Obsidian vault
- 不涉及敏感数据处理

## 9. 验证标准

- ✅ 脚本能够正确读取 session_memory 和 topics.md
- ✅ 生成的 Markdown 符合 Obsidian Callout 格式
- ✅ 通过 Obsidian CLI 成功写入 vault
- ✅ 定时任务能够自动执行并更新内容
- ✅ 无控制台错误
- ✅ 异常情况有完善的 try-catch 和重试机制