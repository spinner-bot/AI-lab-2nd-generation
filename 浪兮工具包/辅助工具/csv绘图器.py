# -*- coding: utf-8 -*-
"""
    浪兮 csv绘图器【AppID:110005】
    功能：CSV像素数据 → 自动识别尺寸正方形灰度图
    规范：灰度图/CSV文件名/1.jpg | 详细错误统计 | 无代码压缩
"""
import csv
import os
import math
import numpy as np
from PIL import Image
import 浪兮工具包.辅助工具.目录构建 as lxpb

# ===================== 【全局路径配置】严格遵守项目规范 =====================
TOOL_ID = "110005"
TOOL_NAME = "csv绘图器"
BASE_RES_DIR = lxpb.R_DIR
TOOL_ROOT = os.path.join(BASE_RES_DIR, "图片资源", TOOL_ID)
CSV_FOLDER = os.path.join(TOOL_ROOT, "csv")
EXPORT_ROOT = os.path.join(TOOL_ROOT, "灰度图")

# 自动创建目录
os.makedirs(CSV_FOLDER, exist_ok=True)
os.makedirs(EXPORT_ROOT, exist_ok=True)

# 图片固定参数
IMAGE_SIZE = 48
PIXEL_COUNT = IMAGE_SIZE * IMAGE_SIZE


# ===================== 【UI辅助函数】照搬词表管理风格 =====================
class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


ICONS = {
    "success": "✅",
    "folder": "📂",
    "file": "📄",
    "exit": "🚪",
    "error": "❌",
    "warn": "⚠️"
}


def print_divider(char="=", length=60):
    print(Colors.BLUE + char * length + Colors.RESET)


def print_menu_title(title, subtitle=""):
    print(f"\n{Colors.GREEN}{title}{Colors.RESET} | {subtitle}")
    print_divider("=")


def print_operation_bar():
    print_divider("=")
    print(f"[0] 退出工具 | 输入文件序号 直接转换")
    print_divider("=")
    print("请输入指令：", end="")


def log(msg, color=Colors.RESET):
    print(f"{color}{msg}{Colors.RESET}")


# ===================== 【工具函数】重名文件夹处理 =====================
def get_csv_output_dir(csv_filename):
    base_name = os.path.splitext(csv_filename)[0]
    target_dir = os.path.join(EXPORT_ROOT, base_name)
    counter = 2
    while os.path.exists(target_dir):
        if "_" in base_name and base_name.split("_")[-1].isdigit():
            base_name = "_".join(base_name.split("_")[:-1])
        target_dir = os.path.join(EXPORT_ROOT, f"{base_name}_{counter}")
        counter += 1
    os.makedirs(target_dir, exist_ok=True)
    return target_dir


# ===================== 【核心转换函数：无压缩·全功能】 =====================
def convert_csv_to_images(csv_path):
    # 获取CSV文件名和输出文件夹
    csv_filename = os.path.basename(csv_path)
    output_dir = get_csv_output_dir(csv_filename)

    # 详细错误统计
    count_success = 0
    count_err_format = 0
    count_err_empty = 0
    count_err_square = 0
    count_err_parse = 0

    try:
        # 打开CSV文件
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

            # 遍历每一行数据
            for idx, row in enumerate(rows, 1):
                try:
                    # 校验：列数不足
                    if len(row) < 2:
                        count_err_format += 1
                        continue

                    # 获取像素字符串
                    pixel_str = row[1].strip()

                    # 校验：空数据
                    if not pixel_str:
                        count_err_empty += 1
                        continue

                    # 分割像素数据
                    pixel_values = pixel_str.split()

                    # 转换为浮点数数组
                    pixels = np.array([float(x) for x in pixel_values])
                    pixel_total = len(pixels)

                    # 自动计算正方形尺寸
                    size = int(math.sqrt(pixel_total))

                    # 校验：不是正方形
                    if size * size != pixel_total:
                        count_err_square += 1
                        continue

                    # 修复全黑问题：0~1转0~255
                    pixels = np.clip(pixels, 0, 1) * 255
                    pixels = pixels.astype(np.uint8)

                    # 生成灰度图
                    img_array = pixels.reshape(size, size)
                    img = Image.fromarray(img_array, 'L')

                    # 保存图片：行号命名
                    img_path = os.path.join(output_dir, f"{idx}.jpg")
                    img.save(img_path, 'JPEG')

                    # 成功计数
                    count_success += 1

                # 解析异常
                except Exception:
                    count_err_parse += 1
                    continue

        # 打印完整统计结果
        print_divider()
        log(f"📊 转换结果统计", Colors.BLUE)
        log(f"✅ 成功生成：{count_success} 张", Colors.GREEN)
        log(f"❌ 格式错误(列数不足)：{count_err_format} 行", Colors.RED)
        log(f"❌ 像素数据为空：{count_err_empty} 行", Colors.RED)
        log(f"❌ 非正方形图片：{count_err_square} 行", Colors.RED)
        log(f"❌ 像素解析失败：{count_err_parse} 行", Colors.RED)
        log(f"📂 保存目录：{output_dir}", Colors.BLUE)
        print_divider()

    except Exception as e:
        log(f"{ICONS['error']} 转换失败：{str(e)}", Colors.RED)


# ===================== 【常驻菜单函数】 =====================
def csv_drawer_menu():
    while True:
        # 打印菜单标题
        print_menu_title(f"{TOOL_NAME} (AppID:{TOOL_ID})", "自动识别尺寸 · CSV转灰度图")

        # 打印路径信息
        log(f"{ICONS['folder']} CSV文件目录：{CSV_FOLDER}", Colors.BLUE)
        log(f"{ICONS['folder']} 导出根目录：{EXPORT_ROOT}", Colors.BLUE)

        # 扫描CSV文件
        csv_files = [f for f in os.listdir(CSV_FOLDER) if f.endswith(".csv")]

        # 显示CSV文件列表
        if csv_files:
            log(f"\n{ICONS['file']} 可用CSV文件列表：", Colors.YELLOW)
            for i, file in enumerate(csv_files, 1):
                log(f"[{i}] {file}")
        else:
            log(f"\n{ICONS['error']} 当前目录中没有CSV文件！", Colors.RED)

        # 打印操作栏
        print_operation_bar()
        choice = input().strip()

        # 0：退出工具
        if choice == "0":
            log(f"{ICONS['exit']} 已退出{TOOL_NAME}，返回主程序", Colors.YELLOW)
            break

        # 数字：选择文件转换
        if choice.isdigit() and csv_files:
            file_index = int(choice) - 1
            if 0 <= file_index < len(csv_files):
                target_csv_path = os.path.join(CSV_FOLDER, csv_files[file_index])
                convert_csv_to_images(target_csv_path)
            else:
                log(f"{ICONS['error']} 输入的文件序号无效！", Colors.RED)
        else:
            log(f"{ICONS['error']} 输入的指令无效！", Colors.RED)

        # 暂停
        input("\n按回车键继续操作...")


# ===================== 【应用启动入口】 =====================
def start_csv_drawer():
    csv_drawer_menu()


# ===================== 【主程序启动接口】 =====================
def run_app(run_app_main, *info):
    # 打印启动信息
    print(f"\033[1;36m【软件启动器：App_ID[{TOOL_ID}]{TOOL_NAME}】\033[0m ")

    # 接口传参模式
    if len(info) >= 1 and info[0]:
        log("✅ 接口参数模式：执行转换", Colors.GREEN)
        csv_path = info[0]
        if os.path.exists(csv_path):
            convert_csv_to_images(csv_path)
        else:
            log(f"{ICONS['error']} 指定的CSV文件不存在！", Colors.RED)
        return

    # 无参数：菜单模式
    log("⚠️ 无接口输入，进入配置菜单", Colors.YELLOW)
    start_csv_drawer()


# 独立运行测试
if __name__ == "__main__":
    run_app(None)