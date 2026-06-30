# -*- coding: utf-8 -*-
"""
    翻译训练配置器【AppID: 310001】
    通用版 | 支持语料方向配置 | 手动配置实时刷新
    JSON配置(共10项)：
    [源词表, 目标词表, 平行语料, 语料方向(bool), 学习率, 训练轮数, 批次大小, 词向量维度, 源词表词数, 目标词表词数]
"""
import os
import json

# ===================== 系统固定路径 =====================
BASE_ROOT = os.path.abspath(".")
APP_CONFIG_DIR = os.path.join(BASE_ROOT, "数据库", "用户数据", "310001")
CONFIG_PATH = os.path.join(APP_CONFIG_DIR, "config.json")
VOCAB_FILE_PATH = os.path.join(BASE_ROOT, "数据库", "资源文件", "词表数据", "active_vocab.txt")
CORPUS_DIR = os.path.join(BASE_ROOT, "数据库", "资源文件", "平行语料")
VOCAB_ROOT_DIR = os.path.join(BASE_ROOT, "数据库", "资源文件", "成品词表")

os.makedirs(APP_CONFIG_DIR, exist_ok=True)
os.makedirs(CORPUS_DIR, exist_ok=True)

# ===================== UI 样式 =====================
HIGHLIGHT = "\033[1;32m"
NORMAL = "\033[0m"
BLUE = "\033[94m"
DOUBLE_LINE = BLUE + "=" * 70 + NORMAL


# ===================== JSON 配置管理（10项 + 兼容旧配置） =====================
def init_config():
    # 初始化10项配置：新增语料方向(bool)
    if not os.path.exists(CONFIG_PATH):
        default = [None, None, None, None, None, None, None, None, None, None]
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)


def load_config():
    init_config()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # 自动补全缺失项
        while len(cfg) < 10:
            cfg.append(None)
        return cfg
    except:
        return [None] * 10


def save_config(src=None, tgt=None, corpus=None, corpus_dir=None, lr=None, epoch=None, batch=None, dim=None,
                src_num=None, tgt_num=None):
    cfg = load_config()
    if src is not None: cfg[0] = str(src).strip()
    if tgt is not None: cfg[1] = str(tgt).strip()
    if corpus is not None: cfg[2] = str(corpus).strip()
    if corpus_dir is not None: cfg[3] = corpus_dir  # 语料方向：True=正向 False=反向
    if lr is not None: cfg[4] = str(lr).strip()
    if epoch is not None: cfg[5] = str(epoch).strip()
    if batch is not None: cfg[6] = str(batch).strip()
    if dim is not None: cfg[7] = str(dim).strip()
    if src_num is not None: cfg[8] = str(src_num).strip()
    if tgt_num is not None: cfg[9] = str(tgt_num).strip()

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ===================== 基础工具 =====================
def get_current_vocab():
    try:
        with open(VOCAB_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read().strip() or None
    except:
        return None


def list_corpus_files():
    try:
        return [f for f in os.listdir(CORPUS_DIR) if os.path.isfile(os.path.join(CORPUS_DIR, f))]
    except:
        return []


# ===================== 自动扫描词表信息（真·扫描 · 严格匹配你的路径规则） =====================
def scan_vocab_info():
    """
    真实扫描词表信息（严格遵循指定路径）
    词表路径规则：数据库/资源文件/词表数据/[词表名]/[词表名].txt
    功能：1. 提取词向量维度 2. 统计文件有效行数（真实词数）
    """
    # 读取配置中的源词表、目标词表名称
    config_data = load_config()
    src_name = config_data[0]
    tgt_name = config_data[1]

    # 未配置词表则退出
    if not src_name or not tgt_name:
        print(f"{BLUE}❌ 请先配置【源词表】和【目标词表】再扫描！{NORMAL}")
        return None, None, None

    try:
        # ===================== 核心：严格按你的规则拼接词表路径 =====================
        # 基础词表根路径
        VOCAB_DATA_DIR = os.path.join(BASE_ROOT, "数据库", "资源文件", "词表数据")
        # 源词表完整路径：词表数据/X/X.txt
        src_file_path = os.path.join(VOCAB_DATA_DIR, src_name, f"{src_name}.txt")
        # 目标词表完整路径
        tgt_file_path = os.path.join(VOCAB_DATA_DIR, tgt_name, f"{tgt_name}.txt")

        # ===================== 从文件名提取词向量维度 =====================
        dim = None
        # 规则：从词表名中提取数字维度（支持 cc.zh.300 / dolma_300 格式）
        import re
        # 正则提取所有数字段，优先取3位/2位（100/200/300）
        dim_list = re.findall(r'\d+', src_name)
        for d in dim_list:
            if len(d) in (2, 3):
                dim = d
                break
        # 兜底默认值
        dim = dim if dim else "300"

        # ===================== 真实统计源词表行数（有效词数） =====================
        src_count = 0
        with open(src_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:  # 跳过空行，只统计有效词汇
                    src_count += 1

        # ===================== 真实统计目标词表行数 =====================
        tgt_count = 0
        with open(tgt_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    tgt_count += 1

        # ===================== 输出扫描结果 =====================
        print(f"\n{HIGHLIGHT}✅ 扫描完成！{NORMAL}")
        print(f"词向量维度：{dim}")
        print(f"源词表总词数：{src_count}")
        print(f"目标词表总词数：{tgt_count}")

        # 返回字符串格式，适配JSON存储
        return str(dim), str(src_count), str(tgt_count)

    # 异常提示
    except FileNotFoundError as e:
        print(f"{BLUE}❌ 扫描失败：未找到词表文件 → {e.filename}{NORMAL}")
    except Exception as e:
        print(f"{BLUE}❌ 扫描失败：{str(e)}{NORMAL}")

    return None, None, None


# ===================== 手动配置词表属性（BUG修复：实时刷新） =====================
def manual_vocab_setting():
    while True:  # 循环+实时加载配置，解决显示不刷新BUG
        cfg = load_config()
        dim, src_num, tgt_num = cfg[7], cfg[8], cfg[9]

        print("\n" + DOUBLE_LINE)
        print(f"        {HIGHLIGHT}【手动配置词表属性】{NORMAL}")
        print(DOUBLE_LINE)
        print(f"1 → 词向量维度：{dim if dim else '未配置'}")
        print(f"2 → 源词表总词数：{src_num if src_num else '未配置'}")
        print(f"3 → 目标词表总词数：{tgt_num if tgt_num else '未配置'}")
        print(DOUBLE_LINE)
        print("0 → 返回主菜单")
        print(DOUBLE_LINE)

        cmd = input("请选择：").strip()
        if cmd == "0":
            break
        elif cmd == "1":
            val = input("输入词向量维度：").strip()
            save_config(dim=val)
        elif cmd == "2":
            val = input("输入源词表总词数：").strip()
            save_config(src_num=val)
        elif cmd == "3":
            val = input("输入目标词表总词数：").strip()
            save_config(tgt_num=val)
        print(f"{HIGHLIGHT}✅ 修改完成！{NORMAL}")


# ===================== 主界面（新增语料方向配置） =====================
def show_main():
    cfg = load_config()
    src, tgt, corpus, corpus_dir, lr, epoch, batch, dim, src_num, tgt_num = cfg

    def show(val): return val if val is not None else "未配置"

    # 语料方向布尔值转文字显示
    dir_show = "正向" if corpus_dir is True else "反向" if corpus_dir is False else "未配置"

    print("\n" + DOUBLE_LINE)
    print(f"        {HIGHLIGHT}【翻译训练配置器】{NORMAL}")
    print(DOUBLE_LINE)
    print(f"[1] 源词表：{show(src)}")
    print(f"[2] 目标词表：{show(tgt)}")
    print(f"[3] 平行语料文件：{show(corpus)}")
    print(f"[4] 语料库使用方向：{dir_show}")  # 新增配置展示
    print(f"[5] learning rate：{show(lr)}")
    print(f"[6] epoch：{show(epoch)}")
    print(f"[7] batch size：{show(batch)}")
    print(f"[8] 词向量维度：{show(dim)}")
    print(f"[9] 源词表词数：{show(src_num)}")
    print(f"[10] 目标词表词数：{show(tgt_num)}")
    print(DOUBLE_LINE)
    print("1 → 配置源词表        2 → 配置目标词表")
    print("3 → 配置平行语料      4 → 配置语料方向")
    print("5 → 设置学习率        6 → 设置训练轮数")
    print("7 → 设置批次大小      8 → 自动更新词表信息")
    print("9 → 手动配置词表属性  0 → 确认")
    print(DOUBLE_LINE)


# ===================== 核心启动 =====================
def start_configurator(run_app):
    while True:
        show_main()
        cmd = input("指令：").strip()

        if cmd == "0":
            break
        # 1 源词表
        elif cmd == "1":
            run_app("110004")
            save_config(src=get_current_vocab())
            print(f"{HIGHLIGHT}✅ 配置完成{NORMAL}")
            input("回车继续")
        # 2 目标词表
        elif cmd == "2":
            run_app("110004")
            save_config(tgt=get_current_vocab())
            print(f"{HIGHLIGHT}✅ 配置完成{NORMAL}")
            input("回车继续")
        # 3 平行语料
        elif cmd == "3":
            files = list_corpus_files()
            if not files:
                print(f"{BLUE}❌ 未找到语料文件{NORMAL}")
                input("回车继续")
                continue
            for i, f in enumerate(files, 1): print(f"[{i}] {f}")
            c = input("选择序号：").strip()
            if c.isdigit() and 1 <= int(c) <= len(files):
                save_config(corpus=files[int(c) - 1])
            input("回车继续")
        # 4 【新增】语料库使用方向（正向=True/反向=False）
        elif cmd == "4":
            print("\n[1] 正向  [2] 反向")
            c = input("选择方向：").strip()
            if c == "1":
                save_config(corpus_dir=True)
            elif c == "2":
                save_config(corpus_dir=False)
            input("回车继续")
        # 5 学习率
        elif cmd == "5":
            val = input("输入学习率：").strip()
            save_config(lr=val)
            input("回车继续")
        # 6 训练轮数
        elif cmd == "6":
            val = input("输入轮数：").strip()
            save_config(epoch=val)
            input("回车继续")
        # 7 批次大小
        elif cmd == "7":
            val = input("输入批次：").strip()
            save_config(batch=val)
            input("回车继续")
        # 8 自动扫描
        elif cmd == "8":
            dim, src_n, tgt_n = scan_vocab_info()
            if dim: save_config(dim=dim, src_num=src_n, tgt_num=tgt_n)
            input("回车继续")
        # 9 手动配置
        elif cmd == "9":
            manual_vocab_setting()


if __name__ == "__main__":
    start_configurator(None)