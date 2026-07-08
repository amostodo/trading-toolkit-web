"""深入分析 valid 数据的 premium_rate 分布"""
import urllib.request
import json

# 1. overview
r = urllib.request.urlopen('http://localhost:8080/api/v1/market/overview', timeout=10)
d = json.loads(r.read())
cb = d.get('data', {}).get('convertible_bond', {})
print("=== Market Overview ===")
print(f"  count: {cb.get('count')}")
print(f"  premium_median: {cb.get('premium_median')}  <- 仍偏高（正常 10-40%）")
print(f"  double_low_median: {cb.get('double_low_median')}  <- 仍偏高（正常 130-160）")
print(f"  price_median: {cb.get('price_median')}  <- 正常")
print(f"  price_max: {cb.get('price_max')}  <- 异常（正常 <500）")

# 2. signals 中的 down_revised（高溢价转债）
r = urllib.request.urlopen('http://localhost:8080/api/v1/convertible/signals', timeout=10)
d = json.loads(r.read())
data = d.get('data', {})

print("\n=== down_revised signals (高溢价) ===")
for b in data.get('down_revised', []):
    print(f"  {b['bond_code']} {b['bond_name']}: price={b['price']}, cv={b['conversion_value']}, "
          f"premium={b['premium_rate']:.2f}%, dl={b['double_low']}")

# 3. 分析问题
print("\n=== 分析 ===")
print("premium_median=214.14 仍然偏高，可能原因:")
print("  1. EM 数据中部分转债的 conversion_value 错误（如刚下修未更新）")
print("  2. price_max=1069 说明有高价转债，如果 cv 也低，premium 会很高")
print()
print("  当前过滤: cv >= 10 且 -100 <= premium <= 500")
print("  但 214 仍在合理范围内（< 500），所以没被过滤")
print()
print("  需要更严格的过滤：")
print("  - 方案A: cv >= 30（正常转股价值 50-300）")
print("  - 方案B: price <= 500（过滤高价转债）")
print("  - 方案C: 使用 premium_rate 的分位数过滤（如 5%-95%）")
print()
print("  验证: 如果 price=200, cv=30, premium=(200-30)/30*100=566.67%")
print("        如果 price=300, cv=50, premium=(300-50)/50*100=500%")
print("  这些都是异常数据（转债价格 200+ 且 cv 50- 说明 EM 数据错误）")

# 4. 检查前端如何使用
print("\n=== 前端使用 ===")
print("前端 applyMarketTemp:")
print("  counts.premiumMedian = cb.premium_median !== undefined ? cb.premium_median : '--'")
print("  counts.doubleLowMedian = cb.double_low_median ?? '--'")
print("前端直接显示后端返回的值，无额外计算")
