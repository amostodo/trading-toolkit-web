#!/usr/bin/env python3
"""
TRAE 工作记录自动化脚本 v2
从 TRAE 内存系统收集工作记录，生成高可读性 Markdown，写入 defNote vault
- 项目工作汇总：时间线 + 任务详情 + 项目概况
- 每日日记：当天任务时间线 + 教训提炼
"""

import os
import sys
import json
import glob
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# 配置常量
# ============================================================
MEMORY_BASE_DIR = r"C:\Users\Administrator\.trae-cn\memory\projects\-d-Develop-GitHub-trading-toolkit-web"
VAULT_BASE_DIR = r"D:\ObsVault\defnote"
DIARY_PATH_PREFIX = "wiki/diary"
PROJECT_WORKLOG_PATH = "wiki/projects/trading-toolkit-worklog.md"
LOG_FILE = r"d:\Develop\GitHub\trading-toolkit-web\.trae\scripts\trae-worklog.log"
BACKUP_DIR = r"d:\Develop\GitHub\trading-toolkit-web\.trae\scripts\backups"

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# 数据读取
# ============================================================

def read_session_memory(date_str):
    """读取指定日期的 session_memory 数据"""
    session_data = []
    date_dir = os.path.join(MEMORY_BASE_DIR, date_str)
    if not os.path.exists(date_dir):
        return session_data

    jsonl_files = glob.glob(os.path.join(date_dir, "session_memory_*.jsonl"))
    for jsonl_file in jsonl_files:
        try:
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            session_data.append(record)
                        except json.JSONDecodeError as e:
                            logger.warning(f"解析 JSONL 失败: {jsonl_file} - {e}")
        except Exception as e:
            logger.error(f"读取文件失败: {jsonl_file} - {e}")

    logger.info(f"[{date_str}] 读取到 {len(session_data)} 条会话记录")
    return session_data


def read_topics(date_str):
    """读取指定日期的 topics.md"""
    topics_path = os.path.join(MEMORY_BASE_DIR, date_str, "topics.md")
    if not os.path.exists(topics_path):
        return ""
    try:
        with open(topics_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取 topics.md 失败: {e}")
        return ""


def read_project_memory():
    """读取 project_memory.md"""
    path = os.path.join(MEMORY_BASE_DIR, "project_memory.md")
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取 project_memory.md 失败: {e}")
        return ""


def collect_all_sessions(days_back=30):
    """收集最近 N 天的所有会话记录"""
    all_sessions = []
    today = datetime.now()
    for i in range(days_back):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y%m%d")
        sessions = read_session_memory(date_str)
        all_sessions.extend(sessions)
    logger.info(f"共收集到 {len(all_sessions)} 条会话记录（最近 {days_back} 天）")
    return all_sessions


def collect_all_topics(days_back=30):
    """收集最近 N 天的 topics.md"""
    all_topics = {}
    today = datetime.now()
    for i in range(days_back):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y%m%d")
        topics = read_topics(date_str)
        if topics:
            all_topics[date_str] = topics
    return all_topics


# ============================================================
# 数据解析辅助
# ============================================================

def parse_time(record):
    """从记录中解析时间"""
    t = record.get("message_summary_time", "")
    if t:
        try:
            return datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
        except:
            pass
    return None


def format_time_short(dt):
    """格式化为 HH:MM"""
    if dt:
        return dt.strftime("%H:%M")
    return "??:??"


def format_time_full(dt):
    """格式化为完整时间"""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M")
    return "未知时间"


def is_weekend(date_str):
    """判断 YYYYMMDD 是否周末"""
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        return dt.weekday() >= 5
    except:
        return False


def parse_project_memory_sections(content):
    """解析 project_memory.md 为各 section"""
    if not content:
        return {}
    sections = {}
    current_title = None
    current_lines = []
    for line in content.split("\n"):
        if line.startswith("## "):
            if current_title:
                sections[current_title] = "\n".join(current_lines).strip()
            current_title = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_title:
        sections[current_title] = "\n".join(current_lines).strip()
    return sections


# ============================================================
# 项目工作汇总生成（独立文件）
# ============================================================

def format_project_worklog(all_sessions, project_memory_content, all_topics):
    """
    生成项目工作汇总 - 高可读性版本
    结构：
    1. YAML front matter + 元信息
    2. 项目概况（仓库架构、技术栈）
    3. 工作统计（总天数、总会话数、各日分布）
    4. 按日期分组的时间线
    5. 每条任务带时间、意图、步骤、结果、教训
    """
    parts = []

    # --- YAML front matter ---
    now = datetime.now()
    parts.append("---")
    parts.append("title: trading-toolkit-web 工作记录")
    parts.append("tags: [project, trading-toolkit, worklog]")
    parts.append("category: project")
    parts.append(f"updated: {now.strftime('%Y-%m-%d')}")
    parts.append(f"total_sessions: {len(all_sessions)}")
    parts.append("---")
    parts.append("")

    # --- 标题 ---
    parts.append("# 📊 trading-toolkit-web 项目工作记录")
    parts.append("")
    parts.append(f"> [!info] 自动生成于 {now.strftime('%Y-%m-%d %H:%M')}")
    parts.append(f"> 汇聚 TRAE 辅助编程的全部会话记录，按日期倒序排列，含时间线、任务详情和教训提炼。")
    parts.append(f"> 数据源：`session_memory_*.jsonl` + `topics.md` + `project_memory.md`")
    parts.append("")

    # --- 项目概况 ---
    pm_sections = parse_project_memory_sections(project_memory_content)
    parts.append("## 📋 项目概况")
    parts.append("")

    hard_constraints = pm_sections.get("Hard Constraints", "")
    if hard_constraints:
        parts.append("### 仓库架构")
        parts.append("")
        for line in hard_constraints.split("\n"):
            line = line.strip()
            if line.startswith("-"):
                parts.append(line)
        parts.append("")

    # 技术栈从 user_profile 或 project_memory 中提取
    parts.append("### 技术栈")
    parts.append("")
    parts.append("- **前端**：Vue 3 + Vite + Pinia + Element Plus + SCSS")
    parts.append("- **后端**：Python Flask（端口 8080）+ AkShare 数据源")
    parts.append("- **小程序**：独立仓库 `trading-toolkit-mp`")
    parts.append("- **笔记**：Obsidian vault `defNote`")
    parts.append("")

    # --- 工作统计 ---
    sessions_by_date = {}
    for session in all_sessions:
        dt = parse_time(session)
        if dt:
            date_key = dt.strftime("%Y%m%d")
        else:
            date_key = "00000000"
        if date_key not in sessions_by_date:
            sessions_by_date[date_key] = []
        sessions_by_date[date_key].append(session)

    sorted_dates = sorted(sessions_by_date.keys(), reverse=True)

    parts.append("## 📈 工作统计")
    parts.append("")
    parts.append(f"| 指标 | 数值 |")
    parts.append(f"|------|------|")
    parts.append(f"| 总会话数 | {len(all_sessions)} |")
    parts.append(f"| 活跃天数 | {len(sessions_by_date)} |")
    parts.append(f"| 统计范围 | 最近 30 天 |")
    parts.append("")

    # 各日分布表
    parts.append("### 各日会话分布")
    parts.append("")
    parts.append("| 日期 | 会话数 |")
    parts.append("|------|--------|")
    for date_key in sorted_dates:
        if date_key == "00000000":
            continue
        date_display = f"{date_key[:4]}-{date_key[4:6]}-{date_key[6:]}"
        weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
        dt = datetime.strptime(date_key, "%Y%m%d")
        weekday = weekday_names[dt.weekday()]
        weekend_tag = " 🕳️" if is_weekend(date_key) else ""
        parts.append(f"| {date_display} 周{weekday}{weekend_tag} | {len(sessions_by_date[date_key])} |")
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- 按日期分组的时间线 ---
    parts.append("## 🗓 工作时间线")
    parts.append("")

    for date_key in sorted_dates:
        if date_key == "00000000":
            continue

        sessions = sessions_by_date[date_key]
        # 按时间排序
        sessions.sort(key=lambda s: parse_time(s) or datetime.min)

        date_display = f"{date_key[:4]}-{date_key[4:6]}-{date_key[6:]}"
        dt = datetime.strptime(date_key, "%Y%m%d")
        weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
        weekday = weekday_names[dt.weekday()]

        parts.append(f"### 📅 {date_display} 周{weekday}")
        parts.append("")
        parts.append(f"> [!summary]+ 当日 {len(sessions)} 个会话")
        # 时间线条目
        for s in sessions:
            t = format_time_short(parse_time(s))
            intent = s.get("intent", "")
            # 截断过长的 intent
            short_intent = intent[:50] + "..." if len(intent) > 50 else intent
            parts.append(f"> - `{t}` {short_intent}")
        parts.append("")

        # 每条任务详情
        for idx, session in enumerate(sessions, 1):
            t_full = format_time_full(parse_time(session))
            t_short = format_time_short(parse_time(session))
            intent = session.get("intent", "")
            actions = session.get("actions", [])
            outcome = session.get("outcome", "")
            learned = session.get("learned", [])

            # 任务标题（带序号和时间）
            parts.append(f"#### {idx}. {intent}")
            parts.append("")
            parts.append(f"`{t_short}` · {t_full}")
            parts.append("")

            # 实施步骤
            if actions:
                parts.append("**🔧 实施步骤**")
                parts.append("")
                for a in actions:
                    parts.append(f"- {a}")
                parts.append("")

            # 结果
            if outcome:
                parts.append("**✅ 结果**")
                parts.append("")
                parts.append(f"> {outcome}")
                parts.append("")

            # 教训
            if learned:
                if isinstance(learned, list):
                    parts.append("**💡 教训提炼**")
                    parts.append("")
                    for l in learned:
                        parts.append(f"- {l}")
                    parts.append("")
                elif isinstance(learned, str):
                    parts.append("**💡 教训提炼**")
                    parts.append("")
                    parts.append(f"- {learned}")
                    parts.append("")

            parts.append("---")
            parts.append("")

    # --- 项目记忆摘要 ---
    if project_memory_content:
        parts.append("## 📌 项目记忆摘要")
        parts.append("")
        parts.append("> [!note] 以下为项目级规则、约束和经验教训，从 `project_memory.md` 自动提取")
        parts.append("")

        for section_name, section_content in pm_sections.items():
            if section_content.strip():
                parts.append(f"### {section_name}")
                parts.append("")
                parts.append(section_content)
                parts.append("")

    parts.append("")
    parts.append("---")
    parts.append(f"*本文件由 `trae-worklog.py` 自动生成，最后更新: {now.strftime('%Y-%m-%d %H:%M')}*")

    return "\n".join(parts)


# ============================================================
# 每日工作记录生成（追加到日记）
# ============================================================

def format_daily_log(date_str, sessions, topics):
    """
    生成每日工作记录内容 - 高可读性版本
    结构：
    1. 概览 callout
    2. 时间线（紧凑列表）
    3. 任务详情（可折叠）
    4. 教训汇总
    5. topics 摘要
    """
    now = datetime.now()
    dt_date = datetime.strptime(date_str, "%Y%m%d")
    weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
    weekday = weekday_names[dt_date.weekday()]
    date_display = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

    # 按时间排序
    sessions.sort(key=lambda s: parse_time(s) or datetime.min)

    parts = []

    # 标记区域
    parts.append(f"## 🤖 TRAE 工作记录")
    parts.append("")
    parts.append(f"> [!info] {date_display} 周{weekday} · {len(sessions)} 个会话 · 自动生成于 {now.strftime('%H:%M')}")
    parts.append(f"> 数据源：session_memory + topics.md")
    parts.append("")

    parts.append("<!-- TRAE-AUTO-START -->")
    parts.append("")

    # --- 时间线 ---
    parts.append("### ⏱ 时间线")
    parts.append("")
    for s in sessions:
        t = format_time_short(parse_time(s))
        intent = s.get("intent", "")
        short = intent[:60] + "..." if len(intent) > 60 else intent
        parts.append(f"- `{t}` {short}")
    parts.append("")

    # --- 任务详情（可折叠） ---
    if sessions:
        parts.append("### 🛠 任务详情")
        parts.append("")

        for idx, session in enumerate(sessions, 1):
            t_full = format_time_full(parse_time(session))
            t_short = format_time_short(parse_time(session))
            intent = session.get("intent", "")
            actions = session.get("actions", [])
            outcome = session.get("outcome", "")
            learned = session.get("learned", [])

            # 可折叠标题
            parts.append(f"#### {idx}. {intent}")
            parts.append("")
            parts.append(f"`{t_short}` · {t_full}")
            parts.append("")

            if actions:
                parts.append("**🔧 步骤**")
                parts.append("")
                for a in actions:
                    parts.append(f"- {a}")
                parts.append("")

            if outcome:
                parts.append(f"> [!success]+ 结果")
                parts.append(f"> {outcome}")
                parts.append("")

            if learned:
                if isinstance(learned, list):
                    parts.append("**💡 教训**")
                    parts.append("")
                    for l in learned:
                        parts.append(f"- {l}")
                    parts.append("")
                elif isinstance(learned, str):
                    parts.append("**💡 教训**")
                    parts.append("")
                    parts.append(f"- {learned}")
                    parts.append("")

            parts.append("---")
            parts.append("")

    # --- topics 摘要 ---
    if topics:
        parts.append("### 📌 主题摘要")
        parts.append("")
        for line in topics.split("\n"):
            if line.startswith("[session_id"):
                if "]" in line:
                    content = line.split("]", 1)[1].strip()
                    if content:
                        parts.append(f"- {content}")
        parts.append("")

    parts.append("<!-- TRAE-AUTO-END -->")
    parts.append("")

    return "\n".join(parts)


# ============================================================
# 写入 Obsidian vault
# ============================================================

def write_to_obsidian_daily(date_str, content):
    """写入每日日记（直接文件写入，支持更新替换）"""
    date_display = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    diary_path = os.path.join(VAULT_BASE_DIR, DIARY_PATH_PREFIX, f"{date_display}.md")

    try:
        os.makedirs(os.path.dirname(diary_path), exist_ok=True)

        if os.path.exists(diary_path):
            with open(diary_path, "r", encoding="utf-8") as f:
                existing_content = f.read()

            section_title = "## 🤖 TRAE 工作记录"
            end_marker = "\n<!-- TRAE-AUTO-END -->"

            if section_title in existing_content and "<!-- TRAE-AUTO-START -->" in existing_content:
                title_idx = existing_content.find(section_title)
                end_idx = existing_content.find(end_marker, title_idx)

                if title_idx >= 0 and end_idx > title_idx:
                    end_idx += len(end_marker)
                    prefix = existing_content[:title_idx]
                    prefix = prefix.rstrip("\n") + "\n\n"
                    new_content = prefix + content
                    with open(diary_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    logger.info(f"更新日记 {date_display} 中的 TRAE 工作记录")
                    return True

            # 追加到末尾
            with open(diary_path, "a", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"追加 TRAE 工作记录到日记 {date_display}")
            return True
        else:
            with open(diary_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"创建新日记 {date_display}")
            return True

    except Exception as e:
        logger.error(f"写入每日日记失败: {e}")
        return False


def write_to_obsidian_project(content):
    """写入项目工作汇总（覆盖式）"""
    project_path = os.path.join(VAULT_BASE_DIR, PROJECT_WORKLOG_PATH)
    try:
        os.makedirs(os.path.dirname(project_path), exist_ok=True)
        with open(project_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"成功写入项目工作汇总: {project_path}")
        return True
    except Exception as e:
        logger.error(f"写入项目工作汇总失败: {e}")
        return False


# ============================================================
# 备份
# ============================================================

def save_backup(content, date_str):
    """保存到本地备份"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = os.path.join(BACKUP_DIR, f"worklog-{date_str}.md")
    try:
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"备份已保存: {backup_path}")
    except Exception as e:
        logger.error(f"保存备份失败: {e}")


# ============================================================
# 主函数
# ============================================================

def main(date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")

    logger.info(f"=== TRAE 工作记录自动化脚本 v2 启动 ===")
    logger.info(f"目标日期: {date_str}")

    try:
        # 1. 读取当日数据
        sessions = read_session_memory(date_str)
        topics = read_topics(date_str)

        if not sessions and not topics:
            logger.info("当日无数据，跳过")
            return

        # 2. 生成并写入每日工作记录
        daily_content = format_daily_log(date_str, sessions, topics)
        daily_success = False
        for attempt in range(3):
            try:
                daily_success = write_to_obsidian_daily(date_str, daily_content)
                if daily_success:
                    break
            except Exception as e:
                logger.error(f"写入每日日记异常: {e}")
            if attempt < 2:
                logger.warning(f"重试 {attempt + 2}/3")
                time.sleep(10)

        if not daily_success:
            save_backup(daily_content, date_str)

        # 3. 生成并写入项目工作汇总
        all_sessions = collect_all_sessions(days_back=30)
        project_memory_content = read_project_memory()
        all_topics = collect_all_topics(days_back=30)

        project_content = format_project_worklog(all_sessions, project_memory_content, all_topics)
        project_success = False
        for attempt in range(3):
            try:
                project_success = write_to_obsidian_project(project_content)
                if project_success:
                    break
            except Exception as e:
                logger.error(f"写入项目汇总异常: {e}")
            if attempt < 2:
                logger.warning(f"重试 {attempt + 2}/3")
                time.sleep(10)

        if not project_success:
            save_backup(project_content, date_str)

        logger.info(f"=== 完成 ===")
        logger.info(f"每日日记: {'成功' if daily_success else '失败'}")
        logger.info(f"项目汇总: {'成功' if project_success else '失败'}")

    except Exception as e:
        logger.error(f"脚本执行失败: {e}", exc_info=True)
        if 'daily_content' in locals():
            save_backup(daily_content, date_str)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        date_arg = sys.argv[1]
        if len(date_arg) == 10 and date_arg[4] == '-':
            date_str = date_arg.replace('-', '')
        elif len(date_arg) == 8:
            date_str = date_arg
        else:
            logger.error(f"无效日期格式: {date_arg}")
            sys.exit(1)
        main(date_str)
    else:
        main()
