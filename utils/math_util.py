from decimal import Decimal, ROUND_DOWN

def data_percent(part, total):
    """
    计算 part 占 total 的百分比，结果保留 2 位小数，截断不进位。
    """
    if total == 0:
        raise ValueError("除数不能为 0")
    # 转成字符串再 Decimal，避免二进制浮点误差
    percent = (Decimal(str(part)) / Decimal(str(total))) * 100
    # 保留 2 位小数并直接截断
    percent = percent.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    return percent