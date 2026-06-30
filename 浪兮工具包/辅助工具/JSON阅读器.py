# -*- coding: utf-8 -*-
"""
    浪兮AI-lab - JSON阅读器
    App_ID: 110003
    【界面极致优化】层级清晰 | 括号对齐 | 索引整洁 | 折叠展开
    开发者：浪兮
"""
import json
import os

# 控制台配色
COLORS = {
    "TITLE": "\033[38;5;225m",
    "INDEX": "\033[38;5;81m",
    "KEY": "\033[38;5;118m",
    "VALUE": "\033[38;5;229m",
    "TOGGLE": "\033[38;5;226m",
    "TIP": "\033[38;5;141m",
    "RED": "\033[91m",
    "END": "\033[0m",
    "BOLD": "\033[1m"
}

# 全局状态
JSON_DATA = {}
COLLAPSED = set()
NODE_INDEX = {}
CURRENT_ID = 0
FILE = ""


# ===================== 加载文件 =====================
def load(path):
    global JSON_DATA
    try:
        with open(path, "r", encoding="utf-8") as f:
            JSON_DATA = json.load(f)
        return True
    except:
        return False


# ===================== 生成节点索引 =====================
def build_index(obj, path=""):
    global CURRENT_ID
    if isinstance(obj, (dict, list)):
        CURRENT_ID += 1
        NODE_INDEX[CURRENT_ID] = path
        if isinstance(obj, dict):
            for k, v in obj.items():
                build_index(v, f"{path}.{k}" if path else k)
        else:
            for i, v in enumerate(obj):
                build_index(v, f"{path}[{i}]" if path else f"[{i}]")


# ===================== 核心打印（优化层级+括号） =====================
def render(obj, path="", indent=0):
    space = "  " * indent
    toggle = f"{COLORS['TOGGLE']}[-]{COLORS['END']}" if path not in COLLAPSED else f"{COLORS['TOGGLE']}[+]{COLORS['END']}"

    # 字典
    if isinstance(obj, dict):
        idx = next((k for k, v in NODE_INDEX.items() if v == path), "")
        print(f"{space}{COLORS['INDEX']}{idx}{COLORS['END']} {toggle} {COLORS['KEY']}{{{COLORS['END']}")
        if path in COLLAPSED:
            return
        for k, v in obj.items():
            new_path = f"{path}.{k}" if path else k
            print(f"{space}  {COLORS['KEY']}{k}{COLORS['END']}: ", end="")
            render(v, new_path, indent + 1)
        print(f"{space}{COLORS['KEY']}}}{COLORS['END']}")

    # 列表
    elif isinstance(obj, list):
        idx = next((k for k, v in NODE_INDEX.items() if v == path), "")
        print(f"{space}{COLORS['INDEX']}{idx}{COLORS['END']} {toggle} {COLORS['KEY']}[{COLORS['END']}")
        if path in COLLAPSED:
            return
        for i, v in enumerate(obj):
            new_path = f"{path}[{i}]" if path else f"[{i}]"
            print(f"{space}  {COLORS['KEY']}{i}{COLORS['END']}: ", end="")
            render(v, new_path, indent + 1)
        print(f"{space}{COLORS['KEY']}]{COLORS['END']}")

    # 普通值（直接显示，无折叠）
    else:
        val = json.dumps(obj, ensure_ascii=False)
        print(f"{COLORS['VALUE']}{val}{COLORS['END']}")


# ===================== 界面 =====================
def show():
    os.system("cls")
    global NODE_INDEX, CURRENT_ID
    NODE_INDEX.clear()
    CURRENT_ID = 0
    build_index(JSON_DATA)

    # 标题
    print(f"{COLORS['BOLD']}{COLORS['TITLE']}" + "=" * 60)
    print("           浪兮AI-lab · JSON阅读器")
    print(f" 文件：{os.path.basename(FILE)}")
    print("=" * 60 + f"{COLORS['END']}")

    # 操作提示
    print(f"\n{COLORS['TIP']}  数字 → 折叠/展开  |  + 全展开  |  - 全折叠  |  0 退出{COLORS['END']}")
    print(f"{COLORS['TOGGLE']}  [-] 已展开  |  [+] 已折叠{COLORS['END']}")
    print("-" * 60 + "\n")

    # 渲染JSON
    render(JSON_DATA)
    print("\n" + "-" * 60)


# ===================== 指令 =====================
def run():
    while True:
        cmd = input(f"\n{COLORS['TIP']}指令：{COLORS['END']}").strip()
        if cmd == "0":
            break
        if cmd == "+":
            COLLAPSED.clear()
            show()
            continue
        if cmd == "-":
            COLLAPSED.update(NODE_INDEX.values())
            show()
            continue
        if cmd.isdigit() and int(cmd) in NODE_INDEX:
            p = NODE_INDEX[int(cmd)]
            if p in COLLAPSED:
                COLLAPSED.remove(p)
            else:
                COLLAPSED.add(p)
            show()
            continue


# ===================== 启动 =====================
def start_json_reader(run_app, path):
    global FILE, COLLAPSED
    FILE = path
    COLLAPSED = set()
    if not load(path):
        print(f"{COLORS['RED']}加载失败{COLORS['END']}")
        input()
        return
    show()
    run()


def main(run_app, *args):
    if args:
        start_json_reader(run_app, args[0])


if __name__ == "__main__":
    main(lambda x: None, "plan.json")