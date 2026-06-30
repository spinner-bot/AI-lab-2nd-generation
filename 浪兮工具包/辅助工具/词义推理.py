# -*- coding: utf-8 -*-
"""
    浪兮AI-lab | 词义推理【AppID:120001】
    兼容词表管理3级架构 | 全局激活词表联动 | 词义逻辑推理
    【已修复NumPy数组报错】| 统一UI界面 | 分表自动保存
"""
import os
import numpy as np

# ===================== 【全局路径配置】对接词表管理 =====================
BASE_ROOT = os.path.abspath(".")
VOCAB_ROOT = os.path.join(BASE_ROOT, "数据库", "资源文件", "词表数据")
ACTIVE_VOCAB_FILE = os.path.join(VOCAB_ROOT, "active_vocab.txt")


# ===================== 【UI统一风格】复刻词表管理视觉 =====================
class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


ICONS = {
    "success": "✅", "scan": "🔍", "brain": "🧠", "match": "🎯", "search": "🔍",
    "analyze": "📊", "exit": "👋", "warn": "⚠️", "file": "📄", "active": "⭐"
}


def print_divider(char="=", length=70):
    print(Colors.BLUE + char * length + Colors.RESET)


def print_menu_title(title, subtitle=""):
    print(f"\n{Colors.GREEN}{title}{Colors.RESET} | {subtitle}")
    print_divider("=")


def log(msg, color=Colors.RESET):
    print(f"{color}{msg}{Colors.RESET}")


# ===================== 【Vocab类】完全复用词表管理核心 =====================
class Vocab:
    _TABLE_REGISTRY = {}

    def __init__(self, name, parent_vocab=None, keep_words: tuple = None):
        self.name = name
        if name != "core_vocab": self._TABLE_REGISTRY[self.name] = self
        self.word2idx, self.word2vec, self.word2count = {}, {}, {}
        self.u_word2idx, self.u_word2vec, self.u_word2count = {}, {}, {}
        if parent_vocab and keep_words:
            for w in keep_words:
                if w in parent_vocab.word2idx:
                    self.word2idx[w] = parent_vocab.word2idx[w]
                    self.word2vec[w] = parent_vocab.word2vec[w]
                    self.word2count[w] = parent_vocab.word2count[w]

    def add(self, word, idx, vec, count, available=True):
        if available:
            self.word2idx[word] = idx
            self.word2vec[word] = vec
            self.word2count[word] = count
        else:
            self.u_word2idx[word] = idx
            self.u_word2vec[word] = vec
            self.u_word2count[word] = count
        return idx

    def get_vec(self, word, available_only=True):
        return self.word2vec.get(word) if available_only else self.word2vec.get(word, self.u_word2vec.get(word))

    def similarity(self, w1, w2, target_vec=None):
        # 🔥 修复点1：严格判断向量非空（修复NumPy报错）
        v1 = self.get_vec(w1)
        v2 = target_vec if target_vec is not None else self.get_vec(w2)
        if v1 is None or v2 is None:
            return 0.0
        if v1.shape != v2.shape:
            return 0.0

        dot = np.dot(v1, v2)
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        return dot / (n1 * n2) if (n1 != 0 and n2 != 0) else 0.0

    def import_from_file(self, path):
        """从txt主表加载词向量（修复原json报错）"""
        self.clear()
        idx = 0
        if not os.path.exists(path): return
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                parts = line.split()
                if len(parts) < 2: continue
                word, vec_str = parts[0], parts[1:-1]
                try:
                    vec = np.array(vec_str, dtype=np.float32)
                    self.add(word, idx, vec, 1, True)
                    idx += 1
                except:
                    continue

    def export_to_file(self, path):
        with open(path, "w", encoding="utf-8") as f:
            for w in self.word2idx:
                f.write(f"{w} {' '.join(map(str, self.word2vec[w]))} {self.word2count[w]}\n")

    def clear(self):
        self.word2idx.clear();
        self.word2vec.clear();
        self.word2count.clear()
        self.u_word2idx.clear();
        self.u_word2vec.clear();
        self.u_word2count.clear()


# ===================== 【激活词表管理】对接词表管理 =====================
class ActiveVocabManager:
    @staticmethod
    def get_active_vocab():
        """获取全局使用中的词表"""
        if not os.path.exists(ACTIVE_VOCAB_FILE):
            return "main_core"
        with open(ACTIVE_VOCAB_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()

    @staticmethod
    def get_main_vocab_path(vocab_name):
        """获取词表主表路径"""
        return os.path.join(VOCAB_ROOT, vocab_name, f"{vocab_name}.txt")

    @staticmethod
    def get_sub_dir(vocab_name):
        """获取分表存储路径"""
        sub_dir = os.path.join(VOCAB_ROOT, vocab_name, "sub_vocabs")
        os.makedirs(sub_dir, exist_ok=True)
        return sub_dir


# ===================== 【核心功能】词义推理模式（优化版） =====================
def run_reasoning_mode():
    """
    词义推理主程序
    1. 自动加载全局激活词表
    2. 逻辑匹配/组合推理
    3. 分表自动存入词表管理
    """
    # 1. 加载全局激活词表（修复核心报错）
    active_vocab_name = ActiveVocabManager.get_active_vocab()
    main_vocab_path = ActiveVocabManager.get_main_vocab_path(active_vocab_name)
    main_vocab = Vocab(active_vocab_name)
    main_vocab.import_from_file(main_vocab_path)

    if not main_vocab.word2idx:
        log(f"{ICONS['warn']} 词表【{active_vocab_name}】无有效词汇！", Colors.RED)
        return

    # 2. 创建推理分表（自动存入词表管理分表文件夹）
    reasoning_vocab = Vocab(name=f"{main_vocab.name}_reasoning")
    sub_dir = ActiveVocabManager.get_sub_dir(active_vocab_name)
    reasoning_save_path = os.path.join(sub_dir, f"{reasoning_vocab.name}.txt")

    # 启动欢迎界面
    print_menu_title("词义推理中心", f"当前加载：{active_vocab_name} | 全局激活词表")
    log(f"{ICONS['brain']} 推理分表：{reasoning_vocab.name}", Colors.YELLOW)
    log(f"{ICONS['file']} 存储路径：{sub_dir}", Colors.BLUE)
    print_divider()

    # ===================== 内部加权组合输入函数 =====================
    def _input_weighted_combo():
        log(f"\n{ICONS['search']} 逐行输入【词 权重】，输入 END 结束", Colors.GREEN)
        log("示例：king 1.0  |  man -1.0  |  woman 1.0")
        combo_parts = []
        combo_vec = None

        while True:
            line = input(">> ").strip()
            if line.upper() == "END":
                break
            if not line:
                continue

            parts = line.split()
            if len(parts) != 2:
                log(f"{ICONS['warn']} 格式错误：词 权重", Colors.RED)
                continue

            word, w_str = parts
            try:
                weight = float(w_str)
            except ValueError:
                log(f"{ICONS['warn']} 权重必须为数字", Colors.RED)
                continue

            if word not in main_vocab.word2idx:
                log(f"{ICONS['warn']} 词表无此词汇：{word}", Colors.RED)
                continue

            vec = main_vocab.get_vec(word)
            # 🔥 修复点2：判断向量有效
            if vec is None or vec.size == 0:
                log(f"{ICONS['warn']} 词汇向量无效：{word}", Colors.RED)
                continue

            if combo_vec is None:
                combo_vec = np.zeros_like(vec, dtype=np.float32)

            combo_vec += weight * vec
            sign = "+" if weight >= 0 else ""
            combo_parts.append(f"{sign}{weight}*{word}")

        # 🔥 修复点3：严格判断组合结果
        if not combo_parts or (combo_vec is None or combo_vec.size == 0):
            log(f"{ICONS['warn']} 未输入有效组合", Colors.RED)
            return None, "", ""

        expr = "".join(combo_parts)
        display_expr = expr if len(expr) <= 40 else f"...{expr[-40:]}"
        log(f"{ICONS['success']} 组合表达式：{display_expr}", Colors.GREEN)
        mix_name = f"mix_{len(reasoning_vocab.word2idx)}"
        return combo_vec, expr, mix_name

    # ===================== 推理主菜单 =====================
    while True:
        print_menu_title("词义推理菜单", f"词表：{active_vocab_name}")
        log("[1] 逻辑匹配（组合向量 → 查找相似词）")
        log("[2] 逻辑分析（两组组合 → 计算相似度）")
        log("[0] 退出词义推理")
        print_divider()
        choice = input(">> 请选择功能：").strip()

        # 退出 + 保存推理分表
        if choice == "0":
            reasoning_vocab.export_to_file(reasoning_save_path)
            log(f"\n{ICONS['exit']} 已退出 | 推理分表已保存：{reasoning_vocab.name}", Colors.GREEN)
            break

        # 1. 逻辑匹配
        elif choice == "1":
            combo_res = _input_weighted_combo()
            if combo_res[0] is None:
                continue
            combo_vec, expr, mix_name = combo_res

            # 存入推理分表
            max_idx = max(reasoning_vocab.word2idx.values()) + 1 if reasoning_vocab.word2idx else 0
            reasoning_vocab.add(mix_name, max_idx, combo_vec, 1, True)

            # 相似度阈值
            threshold_str = input(">> 相似度阈值(0~1，默认0.5)：").strip()
            threshold = float(threshold_str) if threshold_str else 0.5
            threshold = max(0.0, min(1.0, threshold))

            # 匹配结果
            match_results = []
            for word in main_vocab.word2idx:
                sim = main_vocab.similarity(word, mix_name, target_vec=combo_vec)
                if sim >= threshold:
                    match_results.append((word, sim))

            # 输出结果
            match_results.sort(key=lambda x: -x[1])
            print_divider("-")
            log(f"{ICONS['match']} 匹配结果（阈值≥{threshold}）：", Colors.BLUE)
            if match_results:
                for i, (word, sim) in enumerate(match_results, 1):
                    log(f"[{i:2d}] {word:<15} 相似度：{sim:.4f}")
            else:
                log("    未找到匹配词汇")
            print_divider("-")

        # 2. 逻辑分析
        elif choice == "2":
            log(f"\n{ICONS['analyze']} 第一组逻辑组合", Colors.GREEN)
            vec1, expr1, _ = _input_weighted_combo()
            if vec1 is None or vec1.size == 0:
                continue

            log(f"\n{ICONS['analyze']} 第二组逻辑组合", Colors.GREEN)
            vec2, expr2, _ = _input_weighted_combo()
            if vec2 is None or vec2.size == 0:
                continue

            # 计算相似度
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            sim = np.dot(vec1, vec2) / (norm1 * norm2) if (norm1 != 0 and norm2 != 0) else 0.0

            # 输出结果
            print_divider("=")
            log(f"组合1：{expr1[:60]}{'...' if len(expr1) > 60 else ''}")
            log(f"组合2：{expr2[:60]}{'...' if len(expr2) > 60 else ''}")
            log(f"{ICONS['match']} 逻辑相似度 = {sim:.4f}", Colors.GREEN)
            print_divider("=")

        else:
            log(f"{ICONS['warn']} 无效选项", Colors.RED)


# ===================== 应用启动入口 =====================
def start_logic_matcher():
    """词义推理启动器（对接浪兮AI-lab启动器）"""
    try:
        run_reasoning_mode()
    except Exception as e:
        log(f"{ICONS['warn']} 程序异常：{str(e)}", Colors.RED)


# 独立运行测试
if __name__ == "__main__":
    start_logic_matcher()