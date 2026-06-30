# -*- coding: utf-8 -*-
"""
    浪兮AI-lab 文库管理系统【AppID:110002】
    1.删除功能=二次确认
    2.新增JSON文件支持 + 调用主程序run_app打开JSON阅读器
    3.原版预览/搜索/动态行长度/目录切换 完整保留
"""
import os
import re

# ===================== 核心配置 =====================
BASE_ROOT = "数据库"
GLOBAL_WIDTH = 80
CURRENT_PATH = BASE_ROOT

# 子应用配置（JSON阅读器APP_ID，与应用桌面注册一致）
APP_ID_JSON_READER = 110003

# 原版核心常量
PREVIEW_LINE_LIMIT = 20
PREVIEW_CHAR_LIMIT = 1800
SNIPPET_AROUND = 80
MAX_EXPAND_CHAR = 10


# ===================== UI 样式 =====================
class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


def print_divider(char="="):
    print(Colors.BLUE + char * GLOBAL_WIDTH + Colors.RESET)


def log(msg, color=Colors.RESET):
    print(f"{color}{msg}{Colors.RESET}")


# ==============================================================================
# ====================== 原版核心工具函数 =====================
# ==============================================================================
def format_file_size(size_bytes):
    if size_bytes <= 0:
        return "0.0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = size_bytes
    unit_idx = 0
    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024
        unit_idx += 1
    return f"{size:.1f} {units[unit_idx]}"


def expand_to_full_word(text, pos, left=True):
    current = pos
    expanded = 0
    boundaries = ' \n\t\r.,;!?()[]{}<>"\'/:\\-=+'
    while expanded < MAX_EXPAND_CHAR:
        if current < 0 or current >= len(text):
            break
        if text[current] in boundaries:
            break
        current += -1 if left else 1
        expanded += 1
    return current + 1 if left else current - 1


def split_long_word(word, width):
    parts = []
    max_part = width - 1
    i = 0
    while i < len(word):
        if i + max_part < len(word):
            part = word[i:i + max_part] + "-"
            parts.append(part)
            i += max_part
        else:
            parts.append(word[i:])
            break
    return parts


def wrap_for_preview(text, width):
    if width <= 0:
        return text
    raw_lines = text.splitlines()
    final_lines = []
    for line in raw_lines:
        if not line.strip():
            final_lines.append("")
            continue
        words = line.split()
        current_line = ""
        for word in words:
            word_len = len(word)
            if word_len > width:
                if current_line:
                    final_lines.append(current_line.rstrip())
                    current_line = ""
                word_parts = split_long_word(word, width)
                final_lines.extend(word_parts)
                continue
            test_line = current_line + word + " "
            if len(test_line.rstrip()) <= width:
                current_line = test_line
            else:
                final_lines.append(current_line.rstrip())
                current_line = word + " "
        if current_line:
            final_lines.append(current_line.rstrip())
    return "\n".join(final_lines)


# ==============================================================================
# ====================== 动态调整自动换行最大行长度 ======================
# ==============================================================================
def adjust_line_length():
    global GLOBAL_WIDTH
    try:
        new_len = input("请输入新的最大行长度（建议50-200，0=不换行）：").strip()
        if new_len == "0":
            GLOBAL_WIDTH = 0
            log("✅ 已设置：不自动换行", Colors.GREEN)
        elif new_len.isdigit() and int(new_len) >= 20:
            GLOBAL_WIDTH = int(new_len)
            log(f"✅ 已设置：最大行长度 {GLOBAL_WIDTH}", Colors.GREEN)
        else:
            log("❌ 输入无效（需≥20或0）", Colors.RED)
    except:
        log("❌ 设置失败", Colors.RED)
    input("回车返回...")


# ==============================================================================
# ====================== TXT文件操作（原版功能）======================
# ==============================================================================
def txt_file_operation(file_path, run_app_func):
    file_name = os.path.basename(file_path)
    try:
        size = format_file_size(os.path.getsize(file_path))
        with open(file_path, "r", encoding="utf-8") as f:
            c = f.read()
        lines = f"{len(c.splitlines())}行"
        chars = f"{len(c.replace('\n', '').replace(' ', ''))}字"
        words = f"{len(c.split())}词"
    except:
        size = lines = chars = words = "异常"

    while True:
        print_divider()
        log(f"📄 {file_name}", Colors.GREEN)
        log(f"{size} | {lines} | {chars} | {words}", Colors.BLUE)
        print_divider()
        log("[0] 返回 | [1] 预览 | [2] 删除 | [3] 搜索")
        print_divider()
        choice = input("选择操作：").strip()

        if choice == "0":
            break
        elif choice == "1":
            file_preview(file_path)
        elif choice == "2":
            # 二次确认删除
            if input("⚠️ 确认删除？(y/n)：").strip().lower() == "y":
                if input("⚠️ 最终确认：确定删除？(y/n)：").strip().lower() == "y":
                    os.remove(file_path)
                    log("✅ 删除成功", Colors.GREEN)
                    break
            log("✅ 已取消", Colors.GREEN)
        elif choice == "3":
            file_search(file_path)
        else:
            log("❌ 无效指令", Colors.RED)
            input("回车返回...")


# ==============================================================================
# ====================== 【新增】JSON文件操作 =====================
# ==============================================================================
def json_file_operation(file_path, run_app_func):
    file_name = os.path.basename(file_path)
    try:
        size = format_file_size(os.path.getsize(file_path))
        with open(file_path, "r", encoding="utf-8") as f:
            c = f.read()
        lines = f"{len(c.splitlines())}行"
        chars = f"{len(c.replace('\n', '').replace(' ', ''))}字"
        words = f"{len(c.split())}词"
    except:
        size = lines = chars = words = "异常"

    while True:
        print_divider()
        log(f"📄 {file_name}", Colors.GREEN)
        log(f"{size} | {lines} | {chars} | {words}", Colors.BLUE)
        print_divider()
        log("[0] 返回 | [1] 打开 | [2] 删除")  # 无搜索功能
        print_divider()
        choice = input("选择操作：").strip()

        if choice == "0":
            break
        elif choice == "1":
            # 调用主程序run_app，打开JSON阅读器并传递文件路径
            log("✅ 正在打开JSON阅读器...", Colors.GREEN)
            run_app_func(APP_ID_JSON_READER, False, file_path)
            break
        elif choice == "2":
            # 二次确认删除
            if input("⚠️ 确认删除？(y/n)：").strip().lower() == "y":
                if input("⚠️ 最终确认：确定删除？(y/n)：").strip().lower() == "y":
                    os.remove(file_path)
                    log("✅ 删除成功", Colors.GREEN)
                    break
            log("✅ 已取消", Colors.GREEN)
        else:
            log("❌ 无效指令", Colors.RED)
            input("回车返回...")


# ==============================================================================
# ====================== 原版预览 + 搜索功能 ======================
# ==============================================================================
def file_preview(file_path):
    if not os.path.isfile(file_path):
        log("❌ 文件不存在", Colors.RED)
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.splitlines()
        total_chars = len(content.replace("\n", "").replace(" ", ""))
        need_fold = len(lines) > PREVIEW_LINE_LIMIT or total_chars > PREVIEW_CHAR_LIMIT

        print_divider("=")
        log(f"📄 预览：{os.path.basename(file_path)}", Colors.GREEN)
        print_divider("-")

        if need_fold:
            c = input("内容较长，是否折叠预览？(y/n)：").strip().lower()
            if c == "y":
                head = wrap_for_preview("\n".join(lines[:10]), GLOBAL_WIDTH)
                tail = wrap_for_preview("\n".join(lines[-10:]), GLOBAL_WIDTH)
                log(head)
                log(f"\n... 省略 {len(lines) - 20} 行 ...\n")
                log(tail)
            else:
                log(wrap_for_preview(content, GLOBAL_WIDTH), Colors.YELLOW)
        else:
            log(wrap_for_preview(content, GLOBAL_WIDTH), Colors.YELLOW)
        print_divider("=")
    except Exception as e:
        log(f"❌ 预览失败：{str(e)}", Colors.RED)
    input("\n回车返回...")


def file_search(file_path):
    if not os.path.isfile(file_path):
        log("❌ 文件不存在", Colors.RED)
        return
    raw_key = input("请输入搜索内容：").strip()
    if not raw_key:
        log("❌ 搜索词不能为空", Colors.RED)
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            full_text = f.read()
    except:
        log("❌ 读取文件失败", Colors.RED)
        return

    positions = []
    start = 0
    while True:
        idx = full_text.find(raw_key, start)
        if idx == -1:
            break
        positions.append(idx)
        start = idx + len(raw_key)

    if not positions:
        log(f"🔍 未找到内容：{raw_key}", Colors.RED)
        input("\n回车返回...")
        return

    while True:
        log(f"\n🔍 共找到 {len(positions)} 处匹配", Colors.BLUE)
        print_divider("-")
        res_map = {}
        for i, pos in enumerate(positions, 1):
            pre_start = max(0, pos - SNIPPET_AROUND)
            post_end = min(len(full_text), pos + len(raw_key) + SNIPPET_AROUND)
            pre_start = expand_to_full_word(full_text, pre_start, left=True)
            post_end = expand_to_full_word(full_text, post_end, left=False)

            pre = full_text[pre_start:pos].replace("\n", "  ")
            match = full_text[pos:pos + len(raw_key)].replace("\n", "  ")
            post = full_text[pos + len(raw_key):post_end].replace("\n", "  ")
            log(f"[{i:2d}] ...{pre}【{match}】{post}...", Colors.YELLOW)
            res_map[i] = pos

        sel = input("选择结果序号查看详情（0=返回）：").strip()
        if sel == "0":
            break
        if not sel.isdigit() or int(sel) not in res_map:
            log("❌ 无效序号", Colors.RED)
            continue

        ctx = input("设置上下文字符数（如100）：").strip()
        if not ctx.isdigit():
            log("❌ 请输入数字", Colors.RED)
            continue
        pos = res_map[int(sel)]
        s = max(0, pos - int(ctx))
        e = min(len(full_text), pos + len(raw_key) + int(ctx))
        detail = f"...{full_text[s:pos]}【{full_text[pos:pos + len(raw_key)]}】{full_text[pos + len(raw_key):e]}..."
        log(wrap_for_preview(detail, GLOBAL_WIDTH), Colors.BLUE)
    input("\n回车返回...")


# ===================== 目录工具 =====================
def get_dir_list(path):
    dirs, files = [], []
    for name in os.listdir(path):
        full = os.path.join(path, name)
        if os.path.isdir(full):
            dirs.append(name)
        else:
            files.append(name)
    return dirs, files


def dir_switch():
    global CURRENT_PATH
    while True:
        print_divider()
        log(f"当前路径：{CURRENT_PATH}", Colors.YELLOW)
        print_divider()
        log("[0]返回 [1]下级 [2]上级 [3]恢复根目录")
        opt = input("选择：")
        if opt == "0":
            break
        elif opt == "1":
            sub = input("目录名：")
            new_p = os.path.join(CURRENT_PATH, sub)
            if os.path.isdir(new_p): CURRENT_PATH = new_p
        elif opt == "2":
            parent = os.path.dirname(CURRENT_PATH)
            if parent != CURRENT_PATH: CURRENT_PATH = parent
        elif opt == "3":
            CURRENT_PATH = BASE_ROOT
        input("回车...")


# ===================== 主程序 =====================
def start_library(run_app_func=None):
    global CURRENT_PATH
    print_divider()
    log("浪兮AI-lab 文库管理系统", Colors.GREEN)
    print_divider()

    while True:
        dirs, files = get_dir_list(CURRENT_PATH)
        all_items = dirs + files

        print_divider()
        log(f"📂 当前目录：{CURRENT_PATH} | 文件夹：{len(dirs)} | 文件：{len(files)}", Colors.GREEN)
        print_divider()

        for i, name in enumerate(dirs, 1):
            log(f"[{i:2d}] 📂 {name}")
        for i, name in enumerate(files, len(dirs) + 1):
            log(f"[{i:2d}] 📄 {name}")

        print_divider()
        log("[0]返回 [+]新建 [d]删除 [r]重命名 [s]刷新 [x]目录切换 [l]行长度")
        print_divider()
        cmd = input(">> 指令：").strip()

        # 根目录返回判断
        if cmd == "0":
            if CURRENT_PATH == BASE_ROOT:
                return()
            else:
                CURRENT_PATH = os.path.dirname(CURRENT_PATH)

        elif cmd == "+":
            name = input("文件夹名：")
            new_p = os.path.join(CURRENT_PATH, name)
            if not os.path.exists(new_p):
                os.mkdir(new_p)
        elif cmd == "d":
            try:
                idx = int(input("序号：")) - 1
                target = os.path.join(CURRENT_PATH, all_items[idx])
                # 文件夹/文件 删除 二次确认
                if input("⚠️ 确认删除？(y/n)：").lower() == "y":
                    if input("⚠️ 最终确认：确定删除？(y/n)：").lower() == "y":
                        if os.path.isfile(target):
                            os.remove(target)
                        else:
                            import shutil
                            shutil.rmtree(target)
                        log("✅ 删除成功", Colors.GREEN)
            except:
                pass
        elif cmd == "r":
            try:
                idx = int(input("序号：")) - 1
                new = input("新名称：")
                os.rename(os.path.join(CURRENT_PATH, all_items[idx]), os.path.join(CURRENT_PATH, new))
            except:
                pass
        elif cmd == "s":
            pass
        elif cmd == "x":
            dir_switch()
        elif cmd == "l":
            adjust_line_length()
        elif cmd.isdigit():
            idx = int(cmd) - 1
            if 0 <= idx < len(all_items):
                target = os.path.join(CURRENT_PATH, all_items[idx])
                if os.path.isdir(target):
                    CURRENT_PATH = target
                else:
                    # 支持 TXT / JSON 文件
                    if target.lower().endswith(".txt"):
                        txt_file_operation(target, run_app_func)
                    elif target.lower().endswith(".json"):
                        json_file_operation(target, run_app_func)


if __name__ == "__main__":
    start_library()