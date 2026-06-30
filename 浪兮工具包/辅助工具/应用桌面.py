"""
    浪兮AI-lab - 应用桌面【终极优化版 + 应用排序功能】
    1. 开发者操作提示带应用名称
    2. 解除禁用：展示禁用列表选择 + 兼容手动输入
    3. 新增：应用排序系统（禁用保留位次/分组排序/开发者排序）
    原则：纯UI层，启动交由主程序run_app
"""
import os
import json

try:
    from 浪兮工具包.辅助工具 import 模块管理 as lxmm
    from 浪兮工具包.辅助工具 import 目录构建 as lxpb
except ImportError:
    import 模块管理 as lxmm
    import 目录构建 as lxpb

# ===================== 路径配置 =====================
APP_STATE_DIR = os.path.join(lxpb.S_DIR, "app_home")
APP_STATE_PATH = os.path.join(APP_STATE_DIR, "app_state.json")
# ===================== 【新增】排序配置路径 =====================
APP_ORDER_PATH = os.path.join(APP_STATE_DIR, "app_order.json")
p=os.path.join(APP_STATE_DIR, "running.json")
os.makedirs(APP_STATE_DIR, exist_ok=True)
# ===================== 全局配置 =====================
HIGHLIGHT_TOP = "\033[1;32m"
NORMAL = "\033[0m"
BLUE = "\033[94m"
# UI分隔线：单线仅用于置顶和普通之间，其余全部双线
BLUE_DIVIDER = BLUE + "-" * 70 + NORMAL
DOUBLE_DIVIDER = BLUE + "=" * 70 + NORMAL
_CURR_APP_LIST = []

# ===================== 应用状态读写 =====================
def load_app_state():
    if not os.path.exists(APP_STATE_PATH):
        save_app_state({})
        return {}
    try:
        with open(APP_STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_app_state(state_data):
    with open(APP_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state_data, f, ensure_ascii=False, indent=4)

# ===================== 【新增】应用排序管理函数 =====================
def init_app_order():
    """初始化排序：首次运行生成全量AppID列表"""
    if not os.path.exists(APP_ORDER_PATH):
        lxmm.sync()
        all_ids = list(lxmm.mm.list_all_modules().keys())
        save_app_order(all_ids)

def load_app_order():
    """加载应用排序列表"""
    init_app_order()
    try:
        with open(APP_ORDER_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        lxmm.sync()
        return list(lxmm.mm.list_all_modules().keys())

def save_app_order(order_list):
    """保存排序（实时写入硬盘）"""
    with open(APP_ORDER_PATH, "w", encoding="utf-8") as f:
        json.dump(order_list, f, ensure_ascii=False, indent=4)

# ===================== 【改造】核心工具函数（仅新增排序逻辑，原有功能不变） =====================
def get_valid_apps():
    """获取正常+置顶应用（主页显示）+ 按排序规则排列"""
    lxmm.sync()
    all_registry = lxmm.mm.list_all_modules()
    app_state = load_app_state()
    app_order = load_app_order()  # 加载排序
    top_apps, normal_apps = [], []

    # 按自定义排序遍历
    for app_id in app_order:
        if app_id not in all_registry:
            continue
        status = app_state.get(app_id, {}).get("status", 0)
        if status == -1:
            continue  # 禁用：隐藏，保留排序位次
        app_name = all_registry[app_id]["name"]
        alias = app_state.get(app_id, {}).get("alias", None)
        display_name = alias if alias else app_name
        app_item = {
            "app_id": app_id,
            "display_name": display_name,
            "raw_name": app_name,
            "status": status
        }
        if status == 1:
            top_apps.append(app_item)
        else:
            normal_apps.append(app_item)

    total_count = len(all_registry)
    valid_count = len(top_apps) + len(normal_apps)
    return top_apps, normal_apps, total_count, valid_count

def get_disabled_apps():
    """【新增】获取所有已禁用的应用列表"""
    lxmm.sync()
    all_registry = lxmm.mm.list_all_modules()
    app_state = load_app_state()
    disabled_list = []

    for app_id in all_registry:
        status = app_state.get(app_id, {}).get("status", 0)
        if status == -1:
            app_name = all_registry[app_id]["name"]
            alias = app_state.get(app_id, {}).get("alias", None)
            display_name = alias if alias else app_name
            disabled_list.append({
                "app_id": app_id,
                "display_name": display_name,
                "raw_name": app_name
            })
    return disabled_list

def parse_input_to_app_id(input_str):
    """解析输入：索引/ID/名称 → AppID"""
    input_str = str(input_str).strip()
    if input_str.isdigit():
        idx = int(input_str) - 1
        if 0 <= idx < len(_CURR_APP_LIST):
            return _CURR_APP_LIST[idx]["app_id"]
    if lxmm.mm.is_module_exist(input_str): return input_str
    return lxmm.n2id(input_str)

# ===================== 【新增】开发者模式 - 应用排序功能 =====================
def developer_sort_apps():
    """应用排序：上下移/移到首尾/实时保存"""
    while True:
        lxmm.sync()
        order = load_app_order()
        all_registry = lxmm.mm.list_all_modules()

        print("\n" + DOUBLE_DIVIDER)
        print(f"        🔧 开发者模式 - 应用排序管理")
        print(DOUBLE_DIVIDER)
        print("序号 | AppID     | 应用名称")
        print(DOUBLE_DIVIDER)

        for i, app_id in enumerate(order, 1):
            app_name = all_registry.get(app_id, {}).get("name", "未知应用")
            print(f"{HIGHLIGHT_TOP}{i:2d}{NORMAL} | {app_id:9s} | {app_name}")

        print(DOUBLE_DIVIDER)
        print("操作：1-上移 | 2-下移 | 3-移到最前 | 4-移到最后 | 0-返回")
        opt = input("请选择操作：").strip()
        if opt == "0":
            break

        try:
            pos = int(input("请输入要移动的应用序号：")) - 1
            if pos < 0 or pos >= len(order):
                print("❌ 序号无效！")
                input("回车继续...")
                continue

            if opt == "1" and pos > 0:
                order[pos], order[pos-1] = order[pos-1], order[pos]
            elif opt == "2" and pos < len(order)-1:
                order[pos], order[pos+1] = order[pos+1], order[pos]
            elif opt == "3":
                item = order.pop(pos)
                order.insert(0, item)
            elif opt == "4":
                item = order.pop(pos)
                order.append(item)
            else:
                print("❌ 无效操作！")
                input("回车继续...")
                continue

            # 实时保存
            save_app_order(order)
            print("✅ 排序已保存！")
        except Exception as e:
            print(f"❌ 操作失败：{e}")
        input("回车继续...")

# ===================== 显示应用列表 =====================
def show_app_list():
    global _CURR_APP_LIST
    top_apps, normal_apps, total_count, valid_count = get_valid_apps()
    all_display = []
    index = 1

    # 顶部统一双线
    print("\n" + DOUBLE_DIVIDER)
    print(f"        {HIGHLIGHT_TOP}浪兮AI-lab{NORMAL} 应用桌面")
    print(DOUBLE_DIVIDER)

    if top_apps:
        print(f"{HIGHLIGHT_TOP}📌 已置顶{NORMAL}")
        for app in top_apps:
            print(f"{HIGHLIGHT_TOP}[{index:2d}]{NORMAL} {app['display_name']}")
            all_display.append(app)
            index += 1
        # 仅有置顶和普通之间用【单线】
        print(BLUE_DIVIDER)

    for app in normal_apps:
        print(f"{HIGHLIGHT_TOP}[{index:2d}]{NORMAL} {app['display_name']}")
        all_display.append(app)
        index += 1

    # 底部统一双线
    print(DOUBLE_DIVIDER)
    print(f"总计应用：{total_count}（可用：{valid_count}）")
    _CURR_APP_LIST = all_display
    return all_display

# ===================== 搜索功能 =====================
def search_app(keyword, run_app):
    lxmm.sync()
    all_registry = lxmm.mm.list_all_modules()
    app_state = load_app_state()
    result_list = []

    print("\n" + DOUBLE_DIVIDER)
    print(f"🔍 搜索结果（关键词：{keyword}）")
    print(DOUBLE_DIVIDER)

    for app_id, info in all_registry.items():
        status = app_state.get(app_id, {}).get("status", 0)
        if status == -1: continue
        alias = app_state.get(app_id, {}).get("alias", None)
        display_name = alias or info["name"]
        if keyword in info["name"] or keyword in display_name:
            print(f"{HIGHLIGHT_TOP}[{len(result_list)+1:2d}]{NORMAL} {display_name}")
            result_list.append({"app_id": app_id})

    if not result_list:
        print("未找到匹配的应用！")
        print(DOUBLE_DIVIDER)
        return

    print(DOUBLE_DIVIDER)
    print("输入索引打开应用 | 输入 0 返回主页")
    while True:
        cmd = input("请输入指令：").strip()
        if cmd == "0": return
        if cmd.isdigit():
            idx = int(cmd)-1
            if 0 <= idx < len(result_list):
                run_app(result_list[idx]["app_id"])
                return

# ===================== 开发者模式 =====================
def developer_mode(run_app):
    app_state = load_app_state()
    while True:
        print("\n" + DOUBLE_DIVIDER)
        print("        🔧 开发者模式")
        print(DOUBLE_DIVIDER)
        print("1. 启动应用")
        print("2. 禁用应用")
        print("3. 解禁应用")
        print("4. 设置应用别名")
        print("5. 清除应用别名")
        print("6. 置顶/取消置顶应用")
        print("7. 查找应用信息")
        print("8. 应用排序")
        print("0. 返回桌面")
        print(DOUBLE_DIVIDER)

        choice = input("请选择操作：").strip()
        if choice == "0": break

        # 1. 启动应用
        if choice == "1":
            inp = input("输入索引/AppID/名称：").strip()
            app_id = parse_input_to_app_id(inp)
            if app_id:
                app_name = lxmm.id2n(app_id)
                print(f"▶️ 启动应用：{app_name}")
                run_app(app_id)
            else: print("未匹配到应用")

        # 2. 禁用应用
        elif choice == "2":
            inp = input("输入索引/AppID/名称：").strip()
            app_id = parse_input_to_app_id(inp)
            if app_id:
                app_name = lxmm.id2n(app_id)
                app_state[app_id] = app_state.get(app_id, {})
                app_state[app_id]["status"] = -1
                save_app_state(app_state)
                print(f"✅ 已禁用：{app_name}")
            else: print("未匹配到应用")

        # 3. 解除禁用
        elif choice == "3":
            disabled_apps = get_disabled_apps()
            if not disabled_apps:
                print("ℹ️ 暂无禁用的应用")
                input("回车返回...")
                continue

            print("\n" + DOUBLE_DIVIDER)
            print("🚫 已禁用应用列表")
            print(DOUBLE_DIVIDER)
            for i, app in enumerate(disabled_apps, 1):
                print(f"{HIGHLIGHT_TOP}[{i:2d}]{NORMAL} {app['display_name']}")
            print(DOUBLE_DIVIDER)
            print("输入索引选择 | 直接输入AppID/名称")
            inp = input("请输入：").strip()

            app_id = None
            if inp.isdigit():
                idx = int(inp)-1
                if 0 <= idx < len(disabled_apps):
                    app_id = disabled_apps[idx]["app_id"]
            else:
                app_id = parse_input_to_app_id(inp)

            if app_id:
                app_name = lxmm.id2n(app_id)
                app_state[app_id] = app_state.get(app_id, {})
                app_state[app_id]["status"] = 0
                save_app_state(app_state)
                print(f"✅ 已解除禁用：{app_name}")
            else: print("未匹配到应用")

        # 4. 设置别名
        elif choice == "4":
            inp = input("输入索引/AppID/名称：").strip()
            app_id = parse_input_to_app_id(inp)
            if app_id:
                app_name = lxmm.id2n(app_id)
                alias = input("输入新别名：").strip()
                app_state[app_id] = app_state.get(app_id, {})
                app_state[app_id]["alias"] = alias
                save_app_state(app_state)
                print(f"✅ 已为【{app_name}】设置别名：{alias}")
            else: print("未匹配到应用")

        # 5. 清除别名
        elif choice == "5":
            inp = input("输入索引/AppID/名称：").strip()
            app_id = parse_input_to_app_id(inp)
            if app_id:
                app_name = lxmm.id2n(app_id)
                app_state[app_id] = app_state.get(app_id, {})
                app_state[app_id]["alias"] = None
                save_app_state(app_state)
                print(f"✅ 已清除【{app_name}】的别名")
            else: print("未匹配到应用")

        # 6. 置顶切换
        elif choice == "6":
            inp = input("输入索引/AppID/名称：").strip()
            app_id = parse_input_to_app_id(inp)
            if app_id:
                app_name = lxmm.id2n(app_id)
                app_state[app_id] = app_state.get(app_id, {})
                curr = app_state[app_id].get("status", 0)
                new_status = 1 if curr == 0 else 0
                app_state[app_id]["status"] = new_status
                save_app_state(app_state)
                status_text = "置顶" if new_status ==1 else "取消置顶"
                print(f"✅ {status_text}：{app_name}")
            else: print("未匹配到应用")

        # 7. 查看应用信息
        elif choice == "7":
            inp = input("输入索引：").strip()
            if inp.isdigit():
                idx = int(inp)-1
                if 0 <= idx < len(_CURR_APP_LIST):
                    app = _CURR_APP_LIST[idx]
                    st = load_app_state().get(app["app_id"], {})
                    print("\n📋 应用完整信息")
                    print(f"AppID: {app['app_id']}")
                    print(f"名称: {app['raw_name']}")
                    print(f"别名: {st.get('alias','无')}")
                    print(f"状态: {st.get('status',0)} (0正常/-1禁用/1置顶)")
            input("\n回车返回...")

        # 8. 应用排序
        elif choice == "8":
            developer_sort_apps()

        input("\n按回车返回开发者菜单...")

# ===================== 主入口 =====================
def app_desktop(run_app):
    print("\n🚀 正在加载应用桌面...")
    with open(p, "w", encoding="utf-8") as f:
        json.dump([True], f)
    print("   开始自动数据恢复...")
    run_app(10002)
    while True:
        app_list = show_app_list()
        print("\n【指令】数字=打开 | 文字=搜索 | 0=菜单")
        cmd = input("指令：").strip()

        if cmd == "0":
            print("\n1. 退出  2. 开发者模式")
            sub = input("选择：").strip()
            if sub == "1":
                if input("确定退出？y/n：").lower()=="y":
                    print("\n👋 已退出应用桌面")
                    with open(p, "w", encoding="utf-8") as f:
                        json.dump([False], f)
                    break
            elif sub == "2":
                developer_mode(run_app)
            continue

        if cmd.isdigit():
            idx = int(cmd)-1
            if 0 <= idx < len(app_list):
                run_app(app_list[idx]["app_id"])
            continue

        if cmd:
            search_app(cmd, run_app)

if __name__ == "__main__":
    print("请从主程序启动，并传入run_app函数！")