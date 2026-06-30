# -*- coding: utf-8 -*-
"""
    浪兮 i2Rv支流B清洗【AppID:110011】
    功能：循环选择数据包 → 清除所有CSV的feature B列 → 还原原始状态
    规范：基于目录构建 | 全路径可迁移 | 循环菜单 | 原地修改
    路径：110005/i2Rv整合数据包
"""
import os
import csv
from pathlib import Path
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# ===================== 强制兼容导入：目录构建（项目可迁移核心） =====================
try:
    import 浪兮工具包.辅助工具.目录构建 as lxpb
except ImportError:
    import 目录构建 as lxpb

# ===================== 全局配置（严格基于目录构建） =====================
TOOL_NAME = "i2Rv支流B清洗"
SHARE_TOOL_ID = "110005"
# 核心：所有路径从 目录构建 获取根目录，支持项目任意迁移
BASE_RES_DIR = lxpb.R_DIR
SHARE_TOOL_ROOT = os.path.join(BASE_RES_DIR, "图片资源", SHARE_TOOL_ID)
# 最终工作目录：整合数据包
PACKAGE_ROOT = os.path.join(SHARE_TOOL_ROOT, "i2Rv整合数据包")

# ===================== 统一UI样式 =====================
class Colors:
    GREEN = "\033[92m"
    BLUE  = "\033[94m"
    YELLOW= "\033[93m"
    RED   = "\033[91m"
    RESET = "\033[0m"

ICONS = {
    "success": "✅", "folder": "📂", "file": "📄",
    "exit": "🚪", "error": "❌", "warn": "⚠️", "start": "🚀"
}

def print_divider(char="=", length=60):
    print(Colors.BLUE + char * length + Colors.RESET)

def print_menu_title(title, subtitle=""):
    print(f"\n{Colors.GREEN}{title}{Colors.RESET} | {subtitle}")
    print_divider()

def log(msg, color=Colors.RESET):
    print(f"{color}{msg}{Colors.RESET}")

# ===================== 核心功能：移除 feature B 列 =====================
def remove_feature_b(csv_filepath):
    """删除单列：feature B，原地覆盖保存；无该列则直接跳过"""
    try:
        rows = []
        header = []
        del_idx = -1

        # 读取文件并定位列
        with open(csv_filepath, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            if "feature B" in header:
                del_idx = header.index("feature B")
                header.pop(del_idx)
            else:
                return True  # 无列，跳过

            # 移除数据行对应列
            for row in reader:
                if del_idx < len(row):
                    row.pop(del_idx)
                rows.append(row)

        # 安全覆盖写入
        tmp_path = f"{csv_filepath}.tmp"
        with open(tmp_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

        os.remove(csv_filepath)
        os.rename(tmp_path, csv_filepath)
        return True

    except Exception as e:
        return False

def clean_package(package_path):
    """批量清洗单个数据包内所有CSV"""
    pkg_name = os.path.basename(package_path)
    log(f"\n{ICONS['start']} 正在清洗数据包：{pkg_name}", Colors.BLUE)

    # 递归扫描所有CSV
    csv_list = list(Path(package_path).rglob("*.csv"))
    if not csv_list:
        log(f"{ICONS['warn']} 该数据包内无CSV文件", Colors.YELLOW)
        return

    total = len(csv_list)
    success = 0
    failed = 0

    for csv_path in csv_list:
        if remove_feature_b(str(csv_path)):
            success += 1
        else:
            failed += 1

    log(f"✅ 清洗完成 | 总数：{total} | 成功：{success} | 失败：{failed}", Colors.GREEN)

# ===================== 循环菜单：用户选择数据包 =====================
def loop_clean_menu():
    # 自动创建目录
    os.makedirs(PACKAGE_ROOT, exist_ok=True)

    while True:
        print_menu_title(TOOL_NAME, "清除feature B列 · 还原原始状态")
        log(f"📂 工作目录：{PACKAGE_ROOT}", Colors.BLUE)

        # 扫描所有数据包
        package_list = []
        if os.path.exists(PACKAGE_ROOT):
            package_list = [
                f for f in os.listdir(PACKAGE_ROOT)
                if os.path.isdir(os.path.join(PACKAGE_ROOT, f))
            ]

        # 显示数据包列表
        if package_list:
            log(f"\n{ICONS['folder']} 可选择的数据包：", Colors.YELLOW)
            for i, pkg in enumerate(package_list, 1):
                log(f"[{i}] {pkg}")
        else:
            log(f"\n{ICONS['warn']} 未检测到任何数据包", Colors.YELLOW)

        # 操作栏
        print_divider()
        log("[0] 退出工具 | 输入数字选择要清洗的数据包", Colors.BLUE)
        print_divider()
        choice = input("请输入指令：").strip()

        # 退出
        if choice == "0":
            log(f"{ICONS['exit']} 已退出支流B清洗工具", Colors.YELLOW)
            break

        # 选择数据包
        if choice.isdigit() and package_list:
            idx = int(choice) - 1
            if 0 <= idx < len(package_list):
                target_pkg = package_list[idx]
                target_path = os.path.join(PACKAGE_ROOT, target_pkg)
                clean_package(target_path)
            else:
                log(f"{ICONS['error']} 序号无效", Colors.RED)
        else:
            log(f"{ICONS['error']} 输入无效", Colors.RED)

        input("\n按回车键返回菜单...")

# ===================== 标准启动接口 =====================
def run_app(run_app_main, *info):
    loop_clean_menu()

if __name__ == "__main__":
    run_app(None)