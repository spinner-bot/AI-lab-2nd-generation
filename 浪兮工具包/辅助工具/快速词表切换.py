# -*- coding: utf-8 -*-
"""
    快速词表切换【AppID:110004】
    轻量化 | 极速切换 | 无循环 | 兼容浪兮词表系统
"""
import os

# ===================== 【严格复用原系统全局路径】保证兼容性 =====================
BASE_ROOT = os.path.abspath(".")
VOCAB_ROOT = os.path.join(BASE_ROOT, "数据库", "资源文件", "词表数据")
ACTIVE_VOCAB_FILE = os.path.join(VOCAB_ROOT, "active_vocab.txt")

# ===================== 【复用原系统UI样式】保持界面统一 =====================
class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"

ICONS = {
    "success": "✅", "scan": "🔍", "active": "⭐", "exit": "🚪", "warning": "⚠️"
}

def print_divider(char="=", length=80):
    print(Colors.BLUE + char * length + Colors.RESET)

def print_menu_title(title, subtitle=""):
    print(f"\n{Colors.GREEN}{title}{Colors.RESET} | {subtitle}")
    print_divider("=")

def log(msg, color=Colors.RESET):
    print(f"{color}{msg}{Colors.RESET}")

# ===================== 【核心功能：极速版词表操作】 =====================
class FastVocabSwitcher:
    @staticmethod
    def get_all_vocabs_fast():
        """极速扫描：仅获取词表文件夹名称，不读取内部内容"""
        if not os.path.exists(VOCAB_ROOT):
            os.makedirs(VOCAB_ROOT, exist_ok=True)
            return []
        # 只获取文件夹名 = 词表名，极速加载
        return [d for d in os.listdir(VOCAB_ROOT) if os.path.isdir(os.path.join(VOCAB_ROOT, d))]

    @staticmethod
    def get_current_active_vocab():
        """获取当前激活的词表（复用原系统激活文件）"""
        if not os.path.exists(ACTIVE_VOCAB_FILE):
            return None
        with open(ACTIVE_VOCAB_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()

    @staticmethod
    def set_active_vocab(vocab_name):
        """设置激活词表：清空文件并写入新词表名"""
        with open(ACTIVE_VOCAB_FILE, "w", encoding="utf-8") as f:
            f.write(vocab_name)
        return True

# ===================== 【APP主逻辑】 =====================
def start_fast_vocab_switch():
    # 1. 极速加载数据
    vocab_list = FastVocabSwitcher.get_all_vocabs_fast()
    current_vocab = FastVocabSwitcher.get_current_active_vocab()

    # 2. 打印标题
    print_menu_title("快速词表切换", "AppID:110004 | 修改后自动退出")
    log(f"{ICONS['scan']} 已极速扫描词表目录 | 共找到 {len(vocab_list)} 个词表", Colors.BLUE)
    log(f"{ICONS['active']} 当前使用中：{current_vocab if current_vocab else '未设置'}", Colors.GREEN)
    print_divider("-")

    # 3. 无词表时直接退出
    if not vocab_list:
        log(f"{ICONS['warning']} 未找到任何词表，请先创建词表！", Colors.RED)
        input("\n按回车退出...")
        return

    # 4. 打印词表列表（高亮当前激活项）
    log("📋 词表列表：", Colors.YELLOW)
    for idx, vocab_name in enumerate(vocab_list, 1):
        if vocab_name == current_vocab:
            # 高亮显示正在使用的词表
            log(f"[{idx}] {ICONS['active']} {vocab_name} 【正在使用】", Colors.GREEN)
        else:
            log(f"[{idx}] 📂 {vocab_name}")

    # 5. 操作栏
    print_divider("-")
    log("[0] 退出程序 | 输入数字 → 切换为对应词表并自动退出", Colors.YELLOW)
    print_divider("=")

    # 6. 获取用户输入（单次操作，无循环）
    try:
        choice = input("请输入指令：").strip()

        # 退出
        if choice == "0":
            log(f"{ICONS['exit']} 已退出快速词表切换", Colors.YELLOW)
            return

        # 切换词表
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(vocab_list):
                target_vocab = vocab_list[index]
                FastVocabSwitcher.set_active_vocab(target_vocab)
                log(f"\n{ICONS['success']} 切换成功！", Colors.GREEN)
                log(f"已将词表【{target_vocab}】设为全局使用", Colors.GREEN)
            else:
                log(f"\n{ICONS['warning']} 输入的序号无效！", Colors.RED)
        else:
            log(f"\n{ICONS['warning']} 请输入有效数字！", Colors.RED)

    except Exception as e:
        log(f"\n{ICONS['warning']} 操作失败：{str(e)}", Colors.RED)

    # 7. 自动退出（无循环，符合轻量化要求）
    input("\n按回车退出程序...")

# ===================== 启动入口 =====================
if __name__ == "__main__":
    start_fast_vocab_switch()