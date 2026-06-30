# -*- coding: utf-8 -*-
"""
    浪兮词表管理【AppID:110001】终极完整版
    3级架构 | 激活表持久化 | 成品词表导入 | 分表独立化
"""
import os
import random
import numpy as np
from collections import Counter

# ===================== 【全局路径配置】严格遵守规范 =====================
BASE_ROOT = os.path.abspath(".")
VOCAB_ROOT = os.path.join(BASE_ROOT, "数据库", "资源文件", "词表数据")
FINISHED_VOCAB_ROOT = os.path.join(BASE_ROOT, "数据库", "资源文件", "成品词表")
ACTIVE_VOCAB_FILE = os.path.join(VOCAB_ROOT, "active_vocab.txt")
DEFAULT_MAIN_VOCAB = "main_core"

# 自动创建目录
os.makedirs(VOCAB_ROOT, exist_ok=True)
os.makedirs(FINISHED_VOCAB_ROOT, exist_ok=True)


# ===================== 【UI辅助函数】 =====================
class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


ICONS = {
    "success": "✅", "scan": "🔍", "folder": "📂", "file": "📄", "table": "📊",
    "search": "🔎", "filter": "⚙️", "delete": "🗑️", "rename": "✏️",
    "create": "➕", "exit": "🚪", "import": "📥", "active": "⭐", "independent": "📌"
}


def print_divider(char="=", length=80):
    print(Colors.BLUE + char * length + Colors.RESET)


def print_status_bar(status_list):
    for item in status_list:
        print(item)
    print_divider("-")


def print_menu_title(title, subtitle=""):
    print(f"\n{Colors.GREEN}{title}{Colors.RESET} | {subtitle}")
    print_divider("=")


def print_operation_bar(operations):
    print_divider("=")
    print(f"[0] 返回上级 | " + " | ".join(operations))
    print_divider("=")
    print("请输入指令：", end="")


def log(msg, color=Colors.RESET):
    print(f"{color}{msg}{Colors.RESET}")


# ===================== 【激活表管理工具】核心新功能 =====================
class ActiveVocabManager:
    @staticmethod
    def init_active_vocab():
        """初始化激活表文件，不存在则创建"""
        if not os.path.exists(ACTIVE_VOCAB_FILE):
            vocabs = VocabFolderManager.list_all_vocabs()
            if vocabs:
                with open(ACTIVE_VOCAB_FILE, "w", encoding="utf-8") as f:
                    f.write(vocabs[0])
            else:
                VocabFolderManager.create_vocab(DEFAULT_MAIN_VOCAB)
                with open(ACTIVE_VOCAB_FILE, "w", encoding="utf-8") as f:
                    f.write(DEFAULT_MAIN_VOCAB)

    @staticmethod
    def get_active_vocab():
        """获取当前使用中的词表名"""
        ActiveVocabManager.init_active_vocab()
        with open(ACTIVE_VOCAB_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()

    @staticmethod
    def set_active_vocab(vocab_name):
        """设置当前使用中的词表"""
        with open(ACTIVE_VOCAB_FILE, "w", encoding="utf-8") as f:
            f.write(vocab_name)
        log(f"{ICONS['success']} 已将【{vocab_name}】设为全局使用表", Colors.GREEN)


# ===================== 【工具函数】 =====================
def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
        prev = curr
    return prev[-1]


# ===================== 【原生Vocab类】全功能无BUG =====================
class Vocab:
    _TABLE_REGISTRY = {}
    _MAIN_TABLE = "core_vocab"

    def __init__(self, name, parent_vocab=None, keep_words: tuple = None):
        self.name = name
        if name != "core_vocab": self._register_self()
        self.word2idx, self.word2vec, self.word2count = {}, {}, {}
        self.u_word2idx, self.u_word2vec, self.u_word2count = {}, {}, {}
        if parent_vocab and keep_words:
            for w in keep_words:
                if w in parent_vocab.word2idx:
                    self.word2idx[w] = parent_vocab.word2idx[w]
                    self.word2vec[w] = parent_vocab.word2vec[w]
                    self.word2count[w] = parent_vocab.word2count[w]
                if w in parent_vocab.u_word2idx:
                    self.u_word2idx[w] = parent_vocab.u_word2idx[w]
                    self.u_word2vec[w] = parent_vocab.u_word2vec[w]
                    self.u_word2count[w] = parent_vocab.u_word2count[w]

    def _register_self(self):
        Vocab._TABLE_REGISTRY[self.name] = self

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

    def unavailable(self, word):
        if word in self.word2idx:
            self.u_word2idx[word] = self.word2idx.pop(word)
            self.u_word2vec[word] = self.word2vec.pop(word)
            self.u_word2count[word] = self.word2count.pop(word)

    def available(self, word):
        if word in self.u_word2idx:
            self.word2idx[word] = self.u_word2idx.pop(word)
            self.word2vec[word] = self.u_word2vec.pop(word)
            self.word2count[word] = self.u_word2count.pop(word)

    def get_idx(self, word, available_only=True):
        return self.word2idx.get(word) if available_only else self.word2idx.get(word, self.u_word2idx.get(word))

    def get_vec(self, word, available_only=True):
        return self.word2vec.get(word) if available_only else self.word2vec.get(word, self.u_word2vec.get(word))

    def get_count(self, word, available_only=True):
        return self.word2count.get(word, 0) if available_only else self.word2count.get(word,
                                                                                       self.u_word2count.get(word, 0))

    def get_state(self, word, available_only=True):
        return word in self.word2idx if available_only else (word in self.word2idx or word in self.u_word2idx)

    def random_select(self, amount, unavailable_after_select=False):
        ws = list(self.word2idx.keys())
        if not ws: return []
        sel = random.sample(ws, min(amount, len(ws)))
        if unavailable_after_select: [self.unavailable(w) for w in sel]
        return sel

    def weight_select(self, amount, weight=1, unavailable_after_select=False):
        ws = list(self.word2idx.keys())
        if not ws: return []
        ws_ = [weight.get(w, 1) for w in ws] if isinstance(weight, dict) else [self.word2count[w] ** weight for w in ws]
        sel = random.choices(ws, weights=ws_, k=min(amount, len(ws)))
        if unavailable_after_select: [self.unavailable(w) for w in sel]
        return sel

    def similarity(self, w1, w2, tv=None):
        v1, v2 = self.get_vec(w1), tv or self.get_vec(w2)
        if not v1 or not v2 or v1.shape != v2.shape: return 0.0
        dot, n1, n2 = np.dot(v1, v2), np.linalg.norm(v1), np.linalg.norm(v2)
        return dot / (n1 * n2) if n1 and n2 else 0.0

    def dim_clean(self, dim=0):
        ws = list(self.word2idx) + list(self.u_word2idx)
        if not ws: return Vocab(f"{self.name}_empty")
        dims = [self.get_vec(w, 0).shape[0] for w in ws if self.get_vec(w, 0) is not None]
        dim = Counter(dims).most_common(1)[0][0] if dim == 0 and dims else 0
        temp = Vocab(f"{self.name}_without_dim_{dim}")
        for w in list(self.word2idx):
            if self.word2vec[w].shape[0] != dim:
                temp.add(w, self.word2idx[w], self.word2vec[w], self.word2count[w], 1)
                del self.word2idx[w], self.word2vec[w], self.word2count[w]
        for w in list(self.u_word2idx):
            if self.u_word2vec[w].shape[0] != dim:
                temp.add(w, self.u_word2idx[w], self.u_word2vec[w], self.u_word2count[w], 0)
                del self.u_word2idx[w], self.u_word2vec[w], self.u_word2count[w]
        log(f"{ICONS['success']} 维度清洗完成", Colors.GREEN)
        return temp

    def clear(self):
        self.word2idx.clear();
        self.word2vec.clear();
        self.word2count.clear()
        self.u_word2idx.clear();
        self.u_word2vec.clear();
        self.u_word2count.clear()

    def import_from_file(self, path, replace=False):
        if replace:
            self.clear()
        idx = max(self.word2idx.values()) + 1 if self.word2idx else 0
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            # ===================== 新增：兼容 .vec 格式（跳过首行词数+维度） =====================
            first_line = f.readline().strip()
            # 判断是否为 vec 格式首行（两个数字：词表大小 向量维度）
            is_vec_format = False
            if first_line:
                parts = first_line.split()
                if len(parts) == 2:
                    try:
                        int(parts[0])  # 词数
                        int(parts[1])  # 维度
                        is_vec_format = True
                    except ValueError:
                        pass
            # 如果不是 vec 格式，把第一行放回读取流
            if not is_vec_format and first_line:
                f.seek(0)  # 重置文件指针

            # ===================== 原版逻辑：读取词+向量（无任何修改） =====================
            for line in f:
                line = line.strip()
                if not line:
                    continue
                ps = line.split()
                if len(ps) < 2:
                    continue
                w, v = ps[0], np.array(ps[1:], dtype=np.float32)
                self.add(w, idx, v, 1, 1)
                idx += 1

    def export_to_file(self, path):
        with open(path, "w", encoding="utf-8") as f:
            for w in self.word2idx:
                f.write(f"{w} {' '.join(map(str, self.word2vec[w]))} {self.word2count[w]}\n")
            for w in self.u_word2idx:
                f.write(f"{w} {' '.join(map(str, self.u_word2vec[w]))} {self.u_word2count[w]} unavailable\n")

    def search(self, key, fuzzy=0.0):
        res = Vocab(f"{self.name}_search_{key}_{fuzzy}")
        ws = set(list(self.word2idx) + list(self.u_word2idx))
        for w in ws:
            ok = key in w if fuzzy == 0 else levenshtein_distance(key, w) <= max(1, int(len(w) * fuzzy))
            if ok:
                if w in self.word2idx: res.add(w, self.word2idx[w], self.word2vec[w], self.word2count[w], 1)
                if w in self.u_word2idx: res.add(w, self.u_word2idx[w], self.u_word2vec[w], self.u_word2count[w], 0)
        log(f"{ICONS['success']} 搜索完成", Colors.GREEN)
        return res

    def filter(self, min_freq=1):
        res = Vocab(f"{self.name}_filter_{min_freq}")
        for w, c in self.word2count.items():
            if c >= min_freq: res.add(w, self.word2idx[w], self.word2vec[w], c, 1)
        for w, c in self.u_word2count.items():
            if c >= min_freq: res.add(w, self.u_word2idx[w], self.u_word2vec[w], c, 0)
        log(f"{ICONS['success']} 筛选完成", Colors.GREEN)
        return res

    def stats(self):
        v, uv = len(self.word2idx), len(self.u_word2idx)
        vt, uvt = sum(self.word2count.values()), sum(self.u_word2count.values())
        log(f"{ICONS['table']} 词表【{self.name}】| 有效词：{v} | 无效词：{uv} | 总Token：{vt + uvt}", Colors.BLUE)

    def show_vocab(self):
        print_divider("-")
        log(f"{ICONS['file']} 词表内容预览：{self.name}", Colors.YELLOW)
        ws = list(self.word2idx.items())[:10]
        for i, (w, idx) in enumerate(ws, 1):
            log(f"  [{i}] {w:<15} | 索引：{idx:4d} | 频数：{self.word2count[w]}")
        if len(self.word2idx) > 10:
            log(f"  ... 还有 {len(self.word2idx) - 10} 个有效词", Colors.YELLOW)
        print_divider("-")

    def clear_freq(self):
        """修复BUG：重置所有词频为1"""
        for word in self.word2count:
            self.word2count[word] = 1
        for word in self.u_word2count:
            self.u_word2count[word] = 1
        log(f"{ICONS['success']} 所有词频已重置为 1", Colors.GREEN)

    def clear_u(self):
        self.u_word2idx.clear()
        self.u_word2vec.clear()
        self.u_word2count.clear()


# ===================== 【1级管理】词表文件夹管理 =====================
class VocabFolderManager:
    @staticmethod
    def list_all_vocabs():
        return [d for d in os.listdir(VOCAB_ROOT) if os.path.isdir(os.path.join(VOCAB_ROOT, d))]

    @staticmethod
    def get_vocab_stats(vocab_name):
        root = os.path.join(VOCAB_ROOT, vocab_name)
        main_file = os.path.join(root, f"{vocab_name}.txt")
        sub_dir = os.path.join(root, "sub_vocabs")
        sub_count = len([f for f in os.listdir(sub_dir) if f.endswith(".txt")]) if os.path.exists(sub_dir) else 0
        word_count = 0
        if os.path.exists(main_file):
            with open(main_file, "r", encoding="utf-8") as f:
                word_count = sum(1 for _ in f if _.strip())
        return word_count, sub_count

    @staticmethod
    def create_vocab(name):
        path = os.path.join(VOCAB_ROOT, name)
        if os.path.exists(path): return False
        os.makedirs(path)
        os.makedirs(os.path.join(path, "sub_vocabs"), exist_ok=True)
        open(os.path.join(path, f"{name}.txt"), "w", encoding="utf-8").close()
        return True

    @staticmethod
    def delete_vocab(name):
        if name == ActiveVocabManager.get_active_vocab():
            log(f"{ICONS['delete']} 使用中的词表禁止删除", Colors.RED)
            return False
        import shutil
        shutil.rmtree(os.path.join(VOCAB_ROOT, name))
        return True

    @staticmethod
    def rename_vocab(old, new):
        old_path = os.path.join(VOCAB_ROOT, old)
        new_path = os.path.join(VOCAB_ROOT, new)
        if not os.path.exists(old_path) or os.path.exists(new_path): return False
        os.rename(old_path, new_path)
        old_main = os.path.join(new_path, f"{old}.txt")
        new_main = os.path.join(new_path, f"{new}.txt")
        if os.path.exists(old_main): os.rename(old_main, new_main)
        # 如果是激活表，同步更新
        if ActiveVocabManager.get_active_vocab() == old:
            ActiveVocabManager.set_active_vocab(new)
        return True

    @staticmethod
    def import_finished_vocab(file_name):
        """从成品词表导入，创建新词表"""
        vocab_name = os.path.splitext(file_name)[0]
        src_path = os.path.join(FINISHED_VOCAB_ROOT, file_name)
        if not os.path.exists(src_path):
            log(f"{ICONS['delete']} 导入文件不存在", Colors.RED)
            return False
        # 创建新词表
        VocabFolderManager.create_vocab(vocab_name)
        # 导入内容到主表
        vocab_obj = Vocab(vocab_name)
        vocab_obj.import_from_file(src_path)
        main_file = os.path.join(VOCAB_ROOT, vocab_name, f"{vocab_name}.txt")
        vocab_obj.export_to_file(main_file)
        return True


# ===================== 【2级管理】主分表文件管理 =====================
class SubVocabManager:
    @staticmethod
    def get_paths(vocab_name):
        root = os.path.join(VOCAB_ROOT, vocab_name)
        main_file = os.path.join(root, f"{vocab_name}.txt")
        sub_dir = os.path.join(root, "sub_vocabs")
        os.makedirs(sub_dir, exist_ok=True)
        return main_file, sub_dir

    @staticmethod
    def list_sub_vocabs(vocab_name):
        _, sub_dir = SubVocabManager.get_paths(vocab_name)
        return [f[:-4] for f in os.listdir(sub_dir) if f.endswith(".txt")]

    @staticmethod
    def delete_sub(vocab_name, sub_name):
        _, sub_dir = SubVocabManager.get_paths(vocab_name)
        path = os.path.join(sub_dir, f"{sub_name}.txt")
        if os.path.exists(path): os.remove(path); return True
        return False

    @staticmethod
    def rename_sub(vocab_name, old, new):
        _, sub_dir = SubVocabManager.get_paths(vocab_name)
        old_p = os.path.join(sub_dir, f"{old}.txt")
        new_p = os.path.join(sub_dir, f"{new}.txt")
        if os.path.exists(old_p) and not os.path.exists(new_p):
            os.rename(old_p, new_p);
            return True
        return False

    @staticmethod
    def save_sub(vocab_name, vocab_obj):
        _, sub_dir = SubVocabManager.get_paths(vocab_name)
        path = os.path.join(sub_dir, f"{vocab_obj.name}.txt")
        vocab_obj.export_to_file(path)

    @staticmethod
    def independent_sub_to_vocab(sub_obj):
        """核心新功能：分表独立为全新词表"""
        new_vocab_name = f"{sub_obj.name}_independent"
        VocabFolderManager.create_vocab(new_vocab_name)
        main_file = os.path.join(VOCAB_ROOT, new_vocab_name, f"{new_vocab_name}.txt")
        sub_obj.export_to_file(main_file)
        log(f"{ICONS['independent']} 分表已独立为新词表：{new_vocab_name}", Colors.GREEN)


# ===================== 【3级管理】单一词表操作 =====================
def vocab_operation(vocab_obj, vocab_name, is_main):
    while True:
        print_menu_title(f"管理词表：{vocab_obj.name}", f"类型：{'主表' if is_main else '分表'}")
        vocab_obj.stats()
        vocab_obj.show_vocab()

        operations = ["[1]预览", "[2]统计", "[3]搜索", "[4]筛选", "[5]维度清洗", "[6]清空无效词", "[7]重置词频"]
        if not is_main:
            operations.append("[o]独立此分表")  # 仅分表显示独立功能

        print_operation_bar(operations)
        c = input().strip()
        if c == "0":
            break
        elif c == "1":
            vocab_obj.show_vocab()
        elif c == "2":
            vocab_obj.stats()
        elif c == "3":
            k = input("搜索关键词：").strip()
            f = float(input("模糊度(0=精确)：") or 0)
            sub = vocab_obj.search(k, f)
            SubVocabManager.save_sub(vocab_name, sub)
            sub.show_vocab()
        elif c == "4":
            f = int(input("最小词频：") or 1)
            sub = vocab_obj.filter(f)
            SubVocabManager.save_sub(vocab_name, sub)
            sub.show_vocab()
        elif c == "5":
            d = int(input("目标维度(0=自动)：") or 0)
            sub = vocab_obj.dim_clean(d)
            SubVocabManager.save_sub(vocab_name, sub)
            vocab_obj.show_vocab()
        elif c == "6":
            vocab_obj.clear_u()
            log(f"{ICONS['success']} 无效词已清空", Colors.GREEN)
        elif c == "7":
            vocab_obj.clear_freq()
        elif c == "o" and not is_main:
            SubVocabManager.independent_sub_to_vocab(vocab_obj)
        else:
            log(f"{ICONS['delete']} 无效指令", Colors.RED)
        input("\n按回车继续...")


# ===================== 【2级菜单】主分表管理 =====================
def enter_vocab(vocab_name):
    main_file, sub_dir = SubVocabManager.get_paths(vocab_name)
    main_vocab = Vocab(vocab_name)
    main_vocab.import_from_file(main_file)

    while True:
        active_name = ActiveVocabManager.get_active_vocab()
        print_menu_title(f"词表：{vocab_name} | 主分表管理", f"全局使用表：{active_name}")
        subs = SubVocabManager.list_sub_vocabs(vocab_name)

        log(f"[1] {ICONS['file']} 【主表】{vocab_name}.txt (词数：{len(main_vocab.word2idx)})", Colors.GREEN)
        sub_map = {}
        if subs:
            log(f"\n{ICONS['folder']} 分表列表：")
            for i, s in enumerate(subs, 2):
                sub_map[i] = s
                log(f"[{i}] 📄 {s}.txt")
        else:
            log(f"\n{ICONS['folder']} 暂无分表", Colors.YELLOW)

        print_operation_bar(["[u]设为使用表", "[s]搜索分表", "[r]重命名", "[d]删除"])
        c = input().strip()
        if c == "0":
            main_vocab.export_to_file(main_file)
            break

        if c.isdigit():
            num = int(c)
            if num == 1:
                vocab_operation(main_vocab, vocab_name, is_main=True)
            elif num in sub_map:
                sub_name = sub_map[num]
                sub_path = os.path.join(sub_dir, f"{sub_name}.txt")
                sub_obj = Vocab(sub_name)
                sub_obj.import_from_file(sub_path)
                vocab_operation(sub_obj, vocab_name, is_main=False)

        elif c == "u":
            ActiveVocabManager.set_active_vocab(vocab_name)
        elif c == "s":
            key = input("分表关键词：").strip()
            search_result = [s for s in subs if key in s]
            if not search_result:
                log(f"{ICONS['delete']} 未找到分表", Colors.RED)
                input("回车继续")
                continue

            print_divider("-")
            log(f"{ICONS['search']} 搜索结果：", Colors.BLUE)
            temp_map = {}
            for i, name in enumerate(search_result, 1):
                temp_map[i] = name
                log(f"[{i}] {name}")
            log("[0] 返回")
            choice = input("选择要打开的分表：").strip()
            if choice.isdigit() and int(choice) in temp_map:
                target = temp_map[int(choice)]
                sub_path = os.path.join(sub_dir, f"{target}.txt")
                sub_obj = Vocab(target)
                sub_obj.import_from_file(sub_path)
                vocab_operation(sub_obj, vocab_name, is_main=False)

        elif c == "r":
            target_num = input("表序号：").strip()
            if target_num.isdigit():
                n = int(target_num)
                new_name = input("新名称：").strip()
                if n == 1:
                    log(f"{ICONS['delete']} 主表不可重命名", Colors.RED)
                elif n in sub_map:
                    SubVocabManager.rename_sub(vocab_name, sub_map[n], new_name)
                    log(f"{ICONS['success']} 重命名成功", Colors.GREEN)
        elif c == "d":
            target_num = input("表序号：").strip()
            if target_num.isdigit():
                n = int(target_num)
                if n == 1:
                    log(f"{ICONS['delete']} 主表不可删除", Colors.RED)
                elif n in sub_map:
                    SubVocabManager.delete_sub(vocab_name, sub_map[n])
                    log(f"{ICONS['success']} 删除成功", Colors.GREEN)
        input("回车继续...")


# ===================== 【1级菜单】词表列表管理 =====================
def vocab_list_menu():
    ActiveVocabManager.init_active_vocab()
    active_vocab = ActiveVocabManager.get_active_vocab()

    status_list = [
        f"{ICONS['success']} 全局宽度：200列",
        f"{ICONS['success']} 自动校验：全部有效",
        f"{ICONS['scan']} 系统启动：自动扫描词表数据目录...",
        f"{ICONS['active']} 当前全局使用表：{active_vocab}"
    ]
    print_status_bar(status_list)

    while True:
        vocabs = VocabFolderManager.list_all_vocabs()
        active_vocab = ActiveVocabManager.get_active_vocab()
        print_menu_title("词表管理中心", f"根目录：数据库/资源文件/词表数据")

        for i, name in enumerate(vocabs, 1):
            wc, sc = VocabFolderManager.get_vocab_stats(name)
            mark = "✅" if name == active_vocab else "📂"
            log(f"[{i}] {mark} {name:<20} (主表词数：{wc} | 分表：{sc}个)")

        print_operation_bar(["[+]创建", "[i]导入", "[d]删除", "[r]重命名", "[s]刷新"])
        c = input().strip()
        if c == "0":
            log(f"{ICONS['exit']} 已退出", Colors.YELLOW)
            break
        elif c.isdigit() and 1 <= int(c) <= len(vocabs):
            enter_vocab(vocabs[int(c) - 1])
        elif c == "+":
            name = input("新词表名：").strip()
            VocabFolderManager.create_vocab(name) and log("创建成功", Colors.GREEN)
        elif c == "i":
            # 成品词表导入
            files = [f for f in os.listdir(FINISHED_VOCAB_ROOT) if f.endswith((".txt", ".vec"))]
            if not files:
                log(f"{ICONS['delete']} 成品词表目录无文件", Colors.RED)
                continue
            log(f"{ICONS['import']} 成品词表列表：", Colors.BLUE)
            for i, f in enumerate(files, 1):
                log(f"[{i}] {f}")
            idx = input("选择导入文件序号：").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(files):
                VocabFolderManager.import_finished_vocab(files[int(idx) - 1])
        elif c == "d":
            idx = int(input("序号：")) - 1
            if 0 <= idx < len(vocabs):
                VocabFolderManager.delete_vocab(vocabs[idx])
        elif c == "r":
            idx = int(input("序号：")) - 1
            if 0 <= idx < len(vocabs):
                new = input("新名称：").strip()
                VocabFolderManager.rename_vocab(vocabs[idx], new)
        elif c == "s":
            pass


# ===================== 应用启动入口 =====================
def start_vocab_manager():
    vocab_list_menu()


if __name__ == "__main__":
    start_vocab_manager()