#!/usr/bin/env python3
"""
修复可转债中位数计算 BUG
问题: 当 conversion_value 极小（如 3.17）时，premium_rate 会异常大（如 2250%），污染中位数
修复: get_market_temperature 中 valid 过滤增加 conversion_value >= 10 的判断
     （正常转股价值不会低于 10 元，低于 10 说明 EM 数据异常）
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

    # 修复 1: get_market_temperature 中 valid 过滤
    # 旧: valid = df[df['premium_rate'] != 0]
    # 新: valid = df[(df['premium_rate'] != 0) & (df['conversion_value'] >= 10)]
    old_valid = "        valid = df[df['premium_rate'] != 0]"
    new_valid = """        # 过滤无效数据：premium_rate=0（无转股数据）或 conversion_value<10（EM 数据异常）
        # 当 cv 极小时（如 3.17），premium_rate 会异常大（如 2250%），污染中位数
        valid = df[(df['premium_rate'] != 0) & (df['conversion_value'] >= 10)]"""

    if old_valid in content:
        content = content.replace(old_valid, new_valid)
        print("[OK] 修复 get_market_temperature valid 过滤")
    else:
        print("[WARN] 未找到 valid 过滤行，可能已修复或代码已变更")

    # 修复 2: 增加异常值上限保护（防止极端值污染中位数）
    # 在 premium_median 计算前增加过滤
    old_median_calc = """        price_median = float(df['price'].median())
        premium_median = float(valid['premium_rate'].median())
        double_low_median = float(valid['double_low'].median())"""

    new_median_calc = """        price_median = float(df['price'].median())
        # 额外过滤 premium_rate 异常值（合理范围 -100% 到 500%）
        valid_premium = valid[(valid['premium_rate'] >= -100) & (valid['premium_rate'] <= 500)]
        if valid_premium.empty:
            valid_premium = valid
        premium_median = float(valid_premium['premium_rate'].median())
        double_low_median = float(valid_premium['double_low'].median())"""

    if old_median_calc in content:
        content = content.replace(old_median_calc, new_median_calc)
        print("[OK] 修复中位数计算（增加异常值过滤）")
    else:
        print("[WARN] 未找到中位数计算行，可能已修复或代码已变更")

    if content != original:
        f.write_text(content, encoding="utf-8")
        print(f"\n[SUCCESS] 补丁已应用到: {BACKEND_FILE}")
        return True
    else:
        print("\n[INFO] 无变更（可能已修复）")
        return False


if __name__ == "__main__":
    apply_patch()
