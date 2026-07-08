#!/usr/bin/env python3
"""
修复可转债中位数计算 BUG（v2 - 更严格的过滤）
问题:
  1. 当 conversion_value 极小（如 3.17, 14.45, 17.82）时，premium_rate 会异常大（如 2250%, 680%）
  2. price_max=1069 说明有异常高价转债（妖债/退市债）
  3. 这些异常值污染了中位数计算，导致 premium_median=560.81（修复后仍 214.14）
修复:
  - valid 过滤增加 conversion_value >= 50（正常转股价值 50-300）
  - valid 过滤增加 price <= 500（过滤异常高价转债）
  - price_median 也从 valid 计算（而非全量 df），确保一致性
"""
import re
from pathlib import Path

BACKEND_FILE = r"d:\Develop\GitHub\trading-toolkit\cloudrun\services\convertible_bond.py"

def apply_patch():
    f = Path(BACKEND_FILE)
    if not f.exists():
        print(f"[ERROR] 后端文件不存在: {BACKEND_FILE}")
        return False

    content = f.read_text(encoding="utf-8")
    original = content

    # 查找并替换 valid 过滤和中位数计算
    # 匹配从 "valid = df[" 到 "double_low_median = float(" 之后的整段
    old_block = """        # 过滤无效数据：premium_rate=0（无转股数据）或 conversion_value<10（EM 数据异常）
        # 当 cv 极小时（如 3.17），premium_rate 会异常大（如 2250%），污染中位数
        valid = df[(df['premium_rate'] != 0) & (df['conversion_value'] >= 10)]
        if valid.empty:
            return None

        price_median = float(df['price'].median())
        # 额外过滤 premium_rate 异常值（合理范围 -100% 到 500%）
        valid_premium = valid[(valid['premium_rate'] >= -100) & (valid['premium_rate'] <= 500)]
        if valid_premium.empty:
            valid_premium = valid
        premium_median = float(valid_premium['premium_rate'].median())
        double_low_median = float(valid_premium['double_low'].median())"""

    new_block = """        # 过滤无效数据，避免异常值污染中位数：
        # - premium_rate=0：无转股数据
        # - conversion_value<50：EM 数据异常（正常转股价值 50-300，低于 50 说明数据错误或"妖债"）
        # - price>500：异常高价转债（如退市债、妖债），不代表市场整体温度
        valid = df[(df['premium_rate'] != 0) & (df['conversion_value'] >= 50) & (df['price'] <= 500)]
        if valid.empty:
            return None

        price_median = float(valid['price'].median())
        premium_median = float(valid['premium_rate'].median())
        double_low_median = float(valid['double_low'].median())"""

    if old_block in content:
        content = content.replace(old_block, new_block)
        print("[OK] 修复 valid 过滤（cv>=50 且 price<=500）+ 中位数计算（统一从 valid 计算）")
    else:
        # 尝试匹配 v1 修复前的原始代码
        old_block_v0 = """        valid = df[df['premium_rate'] != 0]
        if valid.empty:
            return None

        price_median = float(df['price'].median())
        premium_median = float(valid['premium_rate'].median())
        double_low_median = float(valid['double_low'].median())"""

        new_block_v0 = """        # 过滤无效数据，避免异常值污染中位数：
        # - premium_rate=0：无转股数据
        # - conversion_value<50：EM 数据异常（正常转股价值 50-300，低于 50 说明数据错误或"妖债"）
        # - price>500：异常高价转债（如退市债、妖债），不代表市场整体温度
        valid = df[(df['premium_rate'] != 0) & (df['conversion_value'] >= 50) & (df['price'] <= 500)]
        if valid.empty:
            return None

        price_median = float(valid['price'].median())
        premium_median = float(valid['premium_rate'].median())
        double_low_median = float(valid['double_low'].median())"""

        if old_block_v0 in content:
            content = content.replace(old_block_v0, new_block_v0)
            print("[OK] 修复 valid 过滤（v0→v2）")
        else:
            print("[WARN] 未找到匹配的代码块，可能已修复或代码已变更")
            # 打印当前内容以便调试
            import re
            match = re.search(r'valid = df\[.*?\n.*?double_low_median.*?\n', content)
            if match:
                print(f"  当前代码:\n{match.group(0)}")

    if content != original:
        f.write_text(content, encoding="utf-8")
        print(f"\n[SUCCESS] 补丁已应用到: {BACKEND_FILE}")
        return True
    else:
        print("\n[INFO] 无变更（可能已修复）")
        return False


if __name__ == "__main__":
    apply_patch()
