"""深入分析可转债 premium_rate 异常值"""
import urllib.request
import json

# 1. market overview
r = urllib.request.urlopen('http://localhost:8080/api/v1/market/overview', timeout=10)
d = json.loads(r.read())
cb = d.get('data', {}).get('convertible_bond', {})
print("=== Market Overview ===")
print(f"  count: {cb.get('count')}")
print(f"  price_median: {cb.get('price_median')}")
print(f"  premium_median: {cb.get('premium_median')}  <- 异常")
print(f"  double_low_median: {cb.get('double_low_median')}  <- 异常")
print(f"  price_max: {cb.get('price_max')}  <- 异常（正常<500）")

# 2. signals 各类
r = urllib.request.urlopen('http://localhost:8080/api/v1/convertible/signals', timeout=10)
d = json.loads(r.read())
data = d.get('data', {})
for key in ['double_low', 'force_redeem', 'discount', 'down_revised']:
    items = data.get(key, [])
    print(f"\n=== {key} signals ({len(items)}) ===")
    if items:
        premiums = [b.get('premium_rate', 0) for b in items]
        double_lows = [b.get('double_low', 0) for b in items]
        prices = [b.get('price', 0) for b in items]
        cvs = [b.get('conversion_value', 0) for b in items]
        print(f"  premium_rate: min={min(premiums)}, max={max(premiums)}")
        print(f"  double_low: min={min(double_lows)}, max={max(double_lows)}")
        print(f"  price: min={min(prices)}, max={max(prices)}")
        print(f"  cv: min={min(cvs)}, max={max(cvs)}")

# 3. 检查 temperature API
try:
    r = urllib.request.urlopen('http://localhost:8080/api/v1/convertible/temperature', timeout=10)
    d = json.loads(r.read())
    temp = d.get('data', {})
    print(f"\n=== Temperature API ===")
    print(json.dumps(temp, ensure_ascii=False, indent=2))
except Exception as e:
    print(f"\n[Temperature API]: {e}")

# 4. 分析问题根源
print("\n=== 问题分析 ===")
print("double_low_median = price_median + premium_median")
print(f"  131.39 + 560.81 = {131.39 + 560.81} ≈ 727.3 ✓ (吻合)")
print()
print("premium_median=560.81 异常原因:")
print("  公式: premium_rate = (price - cv) / cv * 100")
print("  当 cv 极小（如 0.1）时，premium_rate 会非常大")
print("  例如: price=130, cv=0.1 → premium_rate = (130-0.1)/0.1*100 = 129900%")
print()
print("  后端过滤: valid = df[df['premium_rate'] != 0]")
print("  问题: 只过滤了 premium_rate=0，没过滤 cv<=0 或 premium_rate 异常大的数据")
print()
print("  修复建议:")
print("  1. valid 应增加 cv > 0 的过滤: df[(df['premium_rate'] != 0) & (df['conversion_value'] > 0)]")
print("  2. 或对 premium_rate 设置合理上限（如 < 500%）")
print("  3. 或在计算 premium_rate 时跳过 cv < 1 的转债（无效转股数据）")
