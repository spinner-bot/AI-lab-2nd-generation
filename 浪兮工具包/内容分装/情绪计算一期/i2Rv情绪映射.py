# -*- coding: utf-8 -*-
"""
    浪兮 i2Rv情绪映射【AppID:110010】
    功能：全自动将CSV第一列情绪值映射为VA向量 | 处理后删除原文件 | 极简日志
    路径：仅操作 110005/i2Rv整合数据包 | 全自动流程
"""
import os
import csv
from pathlib import Path

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# 规范：兼容导入目录构建模块
try:
    import 浪兮工具包.辅助工具.目录构建 as lxpb
except:
    import 目录构建 as lxpb

# ===================== 【全局配置】严格遵守项目规范 =====================
TOOL_NAME = "i2Rv情绪映射"
SHARE_TOOL_ID = "110005"
BASE_RES_DIR = lxpb.R_DIR
SHARE_TOOL_ROOT = os.path.join(BASE_RES_DIR, "图片资源", SHARE_TOOL_ID)
# 唯一工作目录（整合后的数据包）
PACKAGE_ROOT = os.path.join(SHARE_TOOL_ROOT, "i2Rv整合数据包")

# 原始代码核心映射表
VEC_MAP = [(-0.6, 0.6), (-0.7, 0.2), (-0.5, 0.8),
           (0.8, 0.2), (-0.8, -0.4), (0.2, 0.8), (0.0, 0.0)]


# ===================== 【UI样式】项目统一风格 =====================
class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


ICONS = {
    "success": "✅", "start": "🚀", "done": "🎉", "warn": "⚠️"
}


def print_divider(char="=", length=60):
    print(Colors.BLUE + char * length + Colors.RESET)


def log(msg, color=Colors.RESET):
    print(f"{color}{msg}{Colors.RESET}")


# ===================== 【核心转换逻辑】 =====================
def getVec2(n):
    return VEC_MAP[n]


def transform_csv(csv_path, out_path):
    """处理单个CSV文件：第一列情绪值转VA向量"""
    try:
        with open(csv_path, newline='', encoding='utf-8') as fin, \
                open(out_path, 'w', newline='', encoding='utf-8') as fout:

            reader = csv.reader(fin)
            writer = csv.writer(fout)

            for i, row in enumerate(reader):
                if i == 0:
                    writer.writerow(row)
                    continue
                if row:
                    try:
                        n = int(row[0])
                        if 0 <= n <= 6:
                            x, y = getVec2(n)
                            row[0] = f"{x} {y}"
                    except (ValueError, IndexError):
                        pass
                writer.writerow(row)
        return True
    except Exception:
        return False


# ===================== 【全自动处理流程】 =====================
def auto_emotion_to_va():
    log(f"{ICONS['start']} 开始执行 i2Rv情绪VA映射", Colors.BLUE)
    print_divider()

    # 1. 校验目录
    log("[1/3] 校验数据包目录", Colors.BLUE)
    if not os.path.exists(PACKAGE_ROOT):
        log(f"{ICONS['warn']} 未找到 i2Rv整合数据包 目录！", Colors.RED)
        input("\n按回车键继续...")
        return
    log(f"{ICONS['success']} 目录校验完成", Colors.GREEN)

    # 2. 扫描文件
    log("[2/3] 扫描所有CSV文件", Colors.BLUE)
    package_dir = Path(PACKAGE_ROOT)
    all_csv_files = list(package_dir.rglob("*.csv"))
    target_csv_files = [f for f in all_csv_files if "_transformed" not in str(f)]

    if not target_csv_files:
        log(f"{ICONS['warn']} 无待处理的CSV文件", Colors.YELLOW)
        print_divider()
        input("\n按回车键继续...")
        return
    log(f"{ICONS['success']} 共扫描到 {len(target_csv_files)} 个文件待处理", Colors.GREEN)

    # 3. 批量转换 + 删除原文件
    log("[3/3] 批量转换中，请稍候...", Colors.BLUE)
    success_count = 0
    fail_count = 0

    for csv_path in target_csv_files:
        out_path = csv_path.with_name(f"{csv_path.stem}_transformed{csv_path.suffix}")
        # 执行转换
        if transform_csv(csv_path, out_path):
            # 转换成功 → 删除原文件
            os.remove(csv_path)
            success_count += 1
        else:
            fail_count += 1

    # 完成总结
    print_divider()
    log(f"{ICONS['done']} 转换全部完成", Colors.GREEN)
    log(f"✅ 成功处理：{success_count} 个", Colors.GREEN)
    log(f"❌ 处理失败：{fail_count} 个", Colors.RED)
    log(f"🗑️ 原始文件已自动删除", Colors.YELLOW)
    log(f"📄 保留文件：*_transformed.csv", Colors.BLUE)
    print_divider()

    # 暂停防止信息覆盖
    input("\n按 回车键 继续...")


# ===================== 【项目启动接口】 =====================
def run_app(run_app_main, *info):
    auto_emotion_to_va()


if __name__ == "__main__":
    run_app(None)