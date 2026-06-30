# -*- coding: utf-8 -*-
"""
    浪兮 csv150528工具【AppID:110006】
    功能：CSV固定48x48像素数组 → 灰度图
    核心：CSV目录/导出目录 双自定义(p/P) | 兼容导入 | 固定尺寸
"""
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# 1. 按要求编写兼容导入
try:
    pass
    import 浪兮工具包.辅助工具.目录构建 as lxpb
except:
    try:
        import 目录构建 as lxpb
    except:
        pass

import csv
import numpy as np
from PIL import Image

# ===================== 全局配置 =====================
TOOL_ID = "110005"
TOOL_NAME = "csv150528工具"

# 默认路径（项目规范）
try:
    BASE_RES_DIR = lxpb.R_DIR
except:
    BASE_RES_DIR = os.path.dirname(os.path.abspath(__file__))
TOOL_ROOT = os.path.join(BASE_RES_DIR, "图片资源", TOOL_ID)
DEFAULT_CSV_FOLDER = os.path.join(TOOL_ROOT, "csv")
DEFAULT_EXPORT_ROOT = os.path.join(TOOL_ROOT, "灰度图")

# 自定义路径变量
CUSTOM_CSV_FOLDER = None
CUSTOM_EXPORT_ROOT = None

# 固定参数（48x48=2304像素）
FIXED_PIXEL = 2304
FIXED_SIZE = 48

# 自动创建默认目录
os.makedirs(DEFAULT_CSV_FOLDER, exist_ok=True)
os.makedirs(DEFAULT_EXPORT_ROOT, exist_ok=True)


# ===================== UI样式 =====================
class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


ICONS = {
    "success": "✅", "folder": "📂", "file": "📄",
    "exit": "🚪", "error": "❌", "path": "🗂️"
}


def print_divider(char="=", length=60):
    print(Colors.BLUE + char * length + Colors.RESET)


def print_menu_title(title, subtitle=""):
    print(f"\n{Colors.GREEN}{title}{Colors.RESET} | {subtitle}")
    print_divider("=")


def print_operation_bar():
    print_divider("=")
    print(f"[0] 退出 | [p]自定义双路径 | 输入数字选择CSV")
    print_divider("=")
    print("请输入指令：", end="")


def log(msg, color=Colors.RESET):
    print(f"{color}{msg}{Colors.RESET}")


# ===================== 核心：双路径自定义 =====================
def set_custom_path():
    global CUSTOM_CSV_FOLDER, CUSTOM_EXPORT_ROOT
    log("\n" + "=" * 55, Colors.BLUE)
    log(f"{ICONS['path']} 双路径自定义模式（请输入绝对路径）", Colors.YELLOW)
    log("💡 提示：直接回车 = 恢复项目默认路径", Colors.YELLOW)
    log("=" * 55, Colors.BLUE)

    # 自定义 CSV 源目录
    csv_path = input(f"\n请输入 CSV文件夹 绝对路径\n回车默认：{DEFAULT_CSV_FOLDER}\n> ").strip()
    if csv_path:
        if os.path.isabs(csv_path):
            CUSTOM_CSV_FOLDER = csv_path
            os.makedirs(CUSTOM_CSV_FOLDER, exist_ok=True)
            log(f"{ICONS['success']} CSV目录已自定义：{CUSTOM_CSV_FOLDER}", Colors.GREEN)
        else:
            log(f"{ICONS['error']} 非绝对路径，保持默认", Colors.RED)
    else:
        CUSTOM_CSV_FOLDER = None
        log(f"{ICONS['success']} CSV目录已恢复默认", Colors.GREEN)

    # 自定义 导出根目录
    export_path = input(f"\n请输入 灰度图导出 绝对路径\n回车默认：{DEFAULT_EXPORT_ROOT}\n> ").strip()
    if export_path:
        if os.path.isabs(export_path):
            CUSTOM_EXPORT_ROOT = export_path
            os.makedirs(CUSTOM_EXPORT_ROOT, exist_ok=True)
            log(f"{ICONS['success']} 导出目录已自定义：{CUSTOM_EXPORT_ROOT}", Colors.GREEN)
        else:
            log(f"{ICONS['error']} 非绝对路径，保持默认", Colors.RED)
    else:
        CUSTOM_EXPORT_ROOT = None
        log(f"{ICONS['success']} 导出目录已恢复默认", Colors.GREEN)

    input("\n按回车键返回菜单...")


# ===================== 获取当前生效路径 =====================
def get_active_paths():
    csv_dir = CUSTOM_CSV_FOLDER if CUSTOM_CSV_FOLDER else DEFAULT_CSV_FOLDER
    export_dir = CUSTOM_EXPORT_ROOT if CUSTOM_EXPORT_ROOT else DEFAULT_EXPORT_ROOT
    return csv_dir, export_dir


# ===================== 输出子文件夹（防重名） =====================
def get_output_dir(csv_filename):
    _, export_root = get_active_paths()
    base_name = os.path.splitext(csv_filename)[0]
    target_dir = os.path.join(export_root, base_name)
    count = 2
    while os.path.exists(target_dir):
        if "_" in base_name and base_name.split("_")[-1].isdigit():
            base_name = "_".join(base_name.split("_")[:-1])
        target_dir = os.path.join(export_root, f"{base_name}_{count}")
        count += 1
    os.makedirs(target_dir, exist_ok=True)
    return target_dir


# ===================== 原版核心转换逻辑 =====================
def process_csv(input_csv, output_dir):
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        first_row = next(reader, None)
        if first_row and not first_row[0].strip().isdigit():
            pass
        else:
            rows = [first_row] if first_row else []
            reader = rows + list(reader)

        success = 0
        fail = 0
        for idx, row in enumerate(reader, 1):
            try:
                if len(row) < 3:
                    fail += 1
                    continue
                num_str = row[0].strip()
                if not num_str.lstrip('-').isdigit():
                    fail += 1
                    continue
                pixels = list(map(int, row[1].strip().split()))
                suffix = row[2].strip()
                if len(pixels) != FIXED_PIXEL:
                    fail += 1
                    continue

                img = Image.fromarray(np.array(pixels, np.uint8).reshape(FIXED_SIZE, FIXED_SIZE), 'L')
                filename = f"{idx:05d}_{num_str}{suffix}.jpg"
                img.save(os.path.join(output_dir, filename), 'JPEG')
                success += 1
            except:
                fail += 1
                continue

    print_divider()
    log(f"📊 转换完成", Colors.BLUE)
    log(f"✅ 成功：{success} 张", Colors.GREEN)
    log(f"❌ 跳过：{fail} 行", Colors.RED)
    log(f"📂 保存位置：{output_dir}", Colors.BLUE)
    print_divider()


# ===================== 主菜单 =====================
def main_menu():
    while True:
        csv_dir, export_dir = get_active_paths()
        print_menu_title(f"{TOOL_NAME} (ID:{TOOL_ID})", "48x48 CSV转灰度图")
        log(f"📂 当前CSV目录：{csv_dir}", Colors.BLUE)
        log(f"📂 当前导出目录：{export_dir}", Colors.BLUE)

        # 扫描CSV文件
        csv_list = []
        if os.path.exists(csv_dir):
            csv_list = [f for f in os.listdir(csv_dir) if f.endswith(".csv")]

        if csv_list:
            log(f"\n{ICONS['file']} 可用文件：", Colors.YELLOW)
            for i, f in enumerate(csv_list, 1):
                log(f"[{i}] {f}")
        else:
            log(f"\n{ICONS['error']} 目录内无CSV文件！", Colors.RED)

        print_operation_bar()
        choice = input().strip().lower()

        # 退出
        if choice == "0":
            log(f"{ICONS['exit']} 已退出工具", Colors.YELLOW)
            break
        # 自定义路径
        if choice == "p":
            set_custom_path()
            continue
        # 选择文件转换
        if choice.isdigit() and csv_list:
            idx = int(choice) - 1
            if 0 <= idx < len(csv_list):
                file_path = os.path.join(csv_dir, csv_list[idx])
                out_path = get_output_dir(csv_list[idx])
                process_csv(file_path, out_path)
            else:
                log(f"{ICONS['error']} 序号无效", Colors.RED)
        else:
            log(f"{ICONS['error']} 指令无效", Colors.RED)

        input("\n按回车继续...")


# ===================== 项目启动接口 =====================
def run_app(run_app_main, *info):
    #print(f"\033[1;36m【软件启动器：App_ID[{TOOL_ID}]{TOOL_NAME}】\033[0m ")
    csv_dir, _ = get_active_paths()

    # 接口模式
    if len(info) >= 1 and info[0]:
        log("✅ 接口模式运行", Colors.GREEN)
        csv_path = info[0]
        if os.path.exists(csv_path):
            out_path = get_output_dir(os.path.basename(csv_path))
            process_csv(csv_path, out_path)
        else:
            log(f"{ICONS['error']} 文件不存在", Colors.RED)
        return

    # 菜单模式
    log("⚠️ 无接口输入，进入配置", Colors.YELLOW)
    main_menu()


if __name__ == "__main__":
    run_app(None)