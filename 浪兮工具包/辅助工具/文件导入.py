# -*- coding: utf-8 -*-
"""
    浪兮 文件导入【AppID:20001】
    功能：维护文件路径JSON列表 | TK选择文件添加 | 删除/清空/确认退出
    修复：弹窗不弹出 + 路径按要求修改
    规范：目录构建 | 统一UI | 全自动目录创建 | 路径去重
    存储文件：{T_DIR}/文件助手/file_path.json
"""
import json
import os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

# ===================== 修复TK弹窗不弹出：强制置顶+刷新 =====================
root = tk.Tk()
root.withdraw()
# 关键修复：让弹窗置顶显示，解决不弹出问题
root.attributes('-topmost', True)
root.update()

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# ===================== 强制导入目录构建 =====================
try:
    import 浪兮工具包.辅助工具.目录构建 as lxpb
except ImportError:
    import 目录构建 as lxpb

# ===================== 【按你要求修改】全局路径配置 =====================
TOOL_NAME = "文件导入"
APP_ID = "20001"

# 你指定的正确路径
BASE_RES_DIR = lxpb.T_DIR
FILE_HELPER_DIR = os.path.join(BASE_RES_DIR, "文件助手")
JSON_PATH = os.path.join(FILE_HELPER_DIR, "file_path.json")


# ===================== 统一UI样式 =====================
class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


ICONS = {
    "success": "✅", "file": "📄", "add": "➕", "del": "➖",
    "clear": "🗑️", "exit": "✅", "warn": "⚠️", "error": "❌"
}


def print_divider(char="=", length=60):
    print(Colors.BLUE + char * length + Colors.RESET)


def print_title():
    print_divider()
    print(f"{Colors.GREEN}【{TOOL_NAME}】{Colors.RESET}")
    print(f"{Colors.BLUE}存储文件：{JSON_PATH}{Colors.RESET}")
    print_divider()


def log(msg, color=Colors.RESET):
    print(f"{color}{msg}{Colors.RESET}")


# ===================== 核心工具函数 =====================
def init_json_file():
    """初始化JSON文件与目录"""
    os.makedirs(FILE_HELPER_DIR, exist_ok=True)
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def load_file_paths():
    """加载路径列表"""
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def save_file_paths(path_list):
    """保存并去重"""
    unique_list = list(dict.fromkeys(path_list))
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(unique_list, f, ensure_ascii=False, indent=2)
    return unique_list


def show_file_list(path_list):
    """展示文件列表"""
    log(f"\n{ICONS['file']} 当前已选中文件路径（共{len(path_list)}个）：", Colors.BLUE)
    if not path_list:
        log("  暂无选中文件", Colors.YELLOW)
        return
    for i, path in enumerate(path_list, 1):
        log(f"  [{i}] {path}", Colors.GREEN)


# ===================== 功能操作 =====================
def add_file():
    """修复后：正常弹出文件选择窗口"""
    file_path = filedialog.askopenfilename(
        title="选择要添加的文件",
        parent=root  # 绑定主窗口，确保弹出
    )
    if not file_path:
        log(f"{ICONS['warn']} 未选择任何文件", Colors.YELLOW)
        return None

    abs_path = str(Path(file_path).absolute())
    log(f"{ICONS['add']} 已选择文件：{abs_path}", Colors.GREEN)
    return abs_path


def delete_file(path_list):
    """按序号删除"""
    if not path_list:
        log(f"{ICONS['warn']} 列表为空，无法删除", Colors.YELLOW)
        return path_list

    try:
        idx = int(input(f"\n{Colors.YELLOW}请输入要删除的序号：{Colors.RESET}")) - 1
        if 0 <= idx < len(path_list):
            deleted = path_list.pop(idx)
            log(f"{ICONS['del']} 删除成功：{deleted}", Colors.GREEN)
        else:
            log(f"{ICONS['error']} 序号无效", Colors.RED)
    except:
        log(f"{ICONS['error']} 输入错误", Colors.RED)
    return path_list


# ===================== 主循环 =====================
def file_helper_main():
    init_json_file()
    path_list = load_file_paths()

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print_title()
        show_file_list(path_list)

        print_divider()
        log(f"[1] {ICONS['add']} 添加文件", Colors.BLUE)
        log(f"[2] {ICONS['del']} 删除文件", Colors.BLUE)
        log(f"[3] {ICONS['clear']} 清空所有", Colors.BLUE)
        log(f"[0] {ICONS['exit']} 确认保存并退出", Colors.GREEN)
        print_divider()

        choice = input("请输入操作指令：").strip()

        if choice == "0":
            save_file_paths(path_list)
            log(f"\n{ICONS['exit']} 已保存所有路径，退出文件导入工具", Colors.GREEN)
            break

        elif choice == "1":
            new_path = add_file()
            if new_path:
                path_list.append(new_path)
                path_list = save_file_paths(path_list)

        elif choice == "2":
            path_list = delete_file(path_list)
            save_file_paths(path_list)

        elif choice == "3":
            path_list = []
            save_file_paths(path_list)
            log(f"{ICONS['clear']} 已清空所有文件路径", Colors.GREEN)

        else:
            log(f"{ICONS['error']} 无效指令", Colors.RED)

        input("\n按回车键继续...")


# ===================== 标准启动接口 =====================
def run_app(run_app_main, *info):
    file_helper_main()


if __name__ == "__main__":
    run_app(None)