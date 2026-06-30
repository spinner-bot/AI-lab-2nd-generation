# -*- coding: utf-8 -*-
"""
    平行语料清洗【AppID:210001】
    适配 Tatoeba/cmn-eng 原生三列带版权格式
    自动切掉尾部版权多余信息，只保留 英文\t中文 标准句对
"""
import os
import shutil

# ===================== 系统固定路径配置 =====================
BASE_ROOT = os.path.abspath(".")
CORPUS_DIR = os.path.join(BASE_ROOT, "数据库", "资源文件", "平行语料")
IMPORT_SOURCE_DIR = os.path.join(BASE_ROOT, "数据库", "资源文件", "成品词表")
os.makedirs(CORPUS_DIR, exist_ok=True)
os.makedirs(IMPORT_SOURCE_DIR, exist_ok=True)

# ===================== 统一UI配置 =====================
HIGHLIGHT_TOP = "\033[1;32m"
NORMAL = "\033[0m"
BLUE = "\033[94m"
BLUE_DIVIDER = BLUE + "-" * 70 + NORMAL
DOUBLE_DIVIDER = BLUE + "=" * 70 + NORMAL


# ===================== 语料自动清洗核心函数【已适配三列带版权格式】 =====================
def clean_parallel_corpus(raw_lines):
    """
    专门适配：英文	中文	版权备注 三列格式
    自动切掉后面多余版权信息，只保留前两列标准句对
    """
    clean_lines = []
    seen_pairs = set()

    for line in raw_lines:
        line = line.strip()
        if not line:
            continue

        # 按制表符分割
        parts = line.split("\t")
        # 必须至少有两列：英文 + 中文
        if len(parts) < 2:
            continue

        # 只取前两列，直接丢弃后面所有版权、来源、备注
        en_text = parts[0].strip()
        zh_text = parts[1].strip()

        # 过滤单边为空
        if not en_text or not zh_text:
            continue

        # 去重复句对
        pair_key = f"{en_text}|{zh_text}"
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            clean_lines.append(f"{en_text}\t{zh_text}")

    return clean_lines


def import_file_auto_clean(src_filename):
    """导入 + 自动清洗 + 切掉尾部版权信息 + 格式标准化"""
    src_path = os.path.join(IMPORT_SOURCE_DIR, src_filename)
    dst_name = os.path.splitext(src_filename)[0] + "_clean.txt"
    dst_path = os.path.join(CORPUS_DIR, dst_name)

    if os.path.exists(dst_path):
        print(f"{HIGHLIGHT_TOP}⚠️  已存在同名清洗文件，无需重复导入{NORMAL}")
        return

    # 兼容多编码读取
    raw_lines = []
    try:
        with open(src_path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
    except:
        with open(src_path, "r", encoding="gbk", errors="ignore") as f:
            raw_lines = f.readlines()

    # 执行清洗
    clean_lines = clean_parallel_corpus(raw_lines)
    if not clean_lines:
        print(f"{HIGHLIGHT_TOP}❌ 未解析到有效中英句对{NORMAL}")
        return

    # 保存纯净标准语料
    with open(dst_path, "w", encoding="utf-8") as f:
        for line in clean_lines:
            f.write(line + "\n")

    print(f"{HIGHLIGHT_TOP}✅ 导入+自动清洗完成{NORMAL}")
    print(f"原始总行数：{len(raw_lines)} → 有效干净句对：{len(clean_lines)}")
    print(f"输出文件：{dst_name}")


# ===================== 工具函数 =====================
def get_corpus_files():
    files = []
    for f in os.listdir(CORPUS_DIR):
        f_path = os.path.join(CORPUS_DIR, f)
        if os.path.isfile(f_path):
            files.append(f)
    return sorted(files)


def get_importable_files():
    files = []
    for f in os.listdir(IMPORT_SOURCE_DIR):
        f_path = os.path.join(IMPORT_SOURCE_DIR, f)
        if os.path.isfile(f_path):
            files.append(f)
    return sorted(files)


def format_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def get_file_stats(filename):
    f_path = os.path.join(CORPUS_DIR, filename)
    if not os.path.exists(f_path):
        return "文件不存在"
    f_size = os.path.getsize(f_path)
    size_str = format_file_size(f_size)
    total_lines = 0
    valid_lines = 0
    try:
        with open(f_path, "r", encoding="utf-8") as f:
            for line in f:
                total_lines += 1
                if line.strip():
                    valid_lines += 1
    except:
        return "文件编码错误（非UTF-8）"
    return f"大小：{size_str} | 总行数：{total_lines} | 有效句对：{valid_lines}"


# ===================== UI展示函数 =====================
def show_main_menu():
    files = get_corpus_files()
    print("\n" + DOUBLE_DIVIDER)
    print(f"        {HIGHLIGHT_TOP}【平行语料清洗】{NORMAL}")
    print(DOUBLE_DIVIDER)
    if not files:
        print("📂 暂无平行语料文件，请先导入！")
    else:
        print(f"{HIGHLIGHT_TOP}📋 平行语料文件列表{NORMAL}")
        for idx, filename in enumerate(files, 1):
            print(f"{HIGHLIGHT_TOP}[{idx:2d}]{NORMAL} {filename}")
    print(DOUBLE_DIVIDER)
    print("📌 操作指令：")
    print("  数字 → 预览文件/重命名/删除")
    print("   I   → 导入成品词表文件(自动剔除版权多余信息)")
    print("   0   → 返回上一级")
    print(DOUBLE_DIVIDER)
    return files


def show_file_detail(filename):
    f_path = os.path.join(CORPUS_DIR, filename)
    stats = get_file_stats(filename)
    while True:
        print("\n" + DOUBLE_DIVIDER)
        print(f"        {HIGHLIGHT_TOP}文件详情{NORMAL}")
        print(DOUBLE_DIVIDER)
        print(f"文件名：{filename}")
        print(f"统计：{stats}")
        print(DOUBLE_DIVIDER)
        print("1. 重命名  |  2. 删除文件  |  0. 返回")
        print(DOUBLE_DIVIDER)
        cmd = input("请选择操作：").strip()
        if cmd == "0":
            break
        elif cmd == "1":
            new_name = input("输入新文件名（保留后缀）：").strip()
            if new_name:
                new_path = os.path.join(CORPUS_DIR, new_name)
                os.rename(f_path, new_path)
                print(f"{HIGHLIGHT_TOP}✅ 重命名成功！{NORMAL}")
                break
        elif cmd == "2":
            print(f"\n{HIGHLIGHT_TOP}⚠️  首次确认：确定删除【{filename}】？(y/n){NORMAL}")
            c1 = input().strip().lower()
            if c1 != "y":
                print("已取消删除")
                continue
            print(f"{HIGHLIGHT_TOP}⚠️  二次确认：永久删除【{filename}】？(y/n){NORMAL}")
            c2 = input().strip().lower()
            if c2 == "y":
                os.remove(f_path)
                print(f"{HIGHLIGHT_TOP}✅ 文件已删除{NORMAL}")
                break
        else:
            print("无效指令！")


def show_import_menu():
    files = get_importable_files()
    print("\n" + DOUBLE_DIVIDER)
    print(f"        {HIGHLIGHT_TOP}导入成品词表（自动清洗剔除版权）{NORMAL}")
    print(DOUBLE_DIVIDER)
    if not files:
        print("📂 成品词表目录无可用文件")
    else:
        for idx, filename in enumerate(files, 1):
            print(f"{HIGHLIGHT_TOP}[{idx:2d}]{NORMAL} {filename}")
    print(DOUBLE_DIVIDER)
    print("数字选择导入 | 0 返回")
    print(DOUBLE_DIVIDER)
    cmd = input("请选择：").strip()
    if cmd == "0":
        return
    if cmd.isdigit():
        idx = int(cmd) - 1
        files = get_importable_files()
        if 0 <= idx < len(files):
            import_file_auto_clean(files[idx])


# ===================== 主程序入口 =====================
def run():
    while True:
        file_list = show_main_menu()
        cmd = input("请输入指令：").strip()
        if cmd == "0":
            print(f"\n{HIGHLIGHT_TOP}👋 返回{NORMAL}")
            break
        elif cmd.lower() == "i":
            show_import_menu()
            input("\n按回车继续...")
            continue
        elif cmd.isdigit():
            idx = int(cmd) - 1
            if 0 <= idx < len(file_list):
                show_file_detail(file_list[idx])
            else:
                print("无效序号！")
            input("\n按回车继续...")


if __name__ == "__main__":
    run()