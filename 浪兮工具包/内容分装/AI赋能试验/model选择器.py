import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
from pathlib import Path
try:
    import 浪兮工具包.辅助工具.目录构建 as lxpb
except:
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    sys.path.append(str(PROJECT_ROOT))
    import 浪兮工具包.辅助工具.目录构建 as lxpb

mp = os.path.join(lxpb.S_DIR, "AI_power", "models")
os.makedirs(mp, exist_ok=True)

import json
import shutil
import textwrap
from typing import Optional, List, Dict, Any, Union, Tuple

# --------------------- 硬件检测 ---------------------
def get_gpu_memory_gb() -> Optional[float]:
    """
    获取可用GPU显存（单位GB），仅支持NVIDIA显卡。
    返回第一个检测到的GPU可用显存，若失败返回 None。
    """
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        free_gb = info.free / (1024 ** 3)
        pynvml.nvmlShutdown()
        return round(free_gb, 2)
    except Exception:
        return None

def check_vram_requirement(vram_need: Union[str, float, int], available: Optional[float]) -> bool:
    """
    判断当前硬件是否满足模型显存需求。
    vram_need: 模型所需显存（数值），0或''表示无需显存。
    available: 当前可用显存（GB），若为None表示无法检测，保守返回False（即认为不满足）。
    """
    try:
        need = float(vram_need)
    except (TypeError, ValueError):
        need = 0.0
    if need <= 0:
        return True  # 无显存需求
    if available is None:
        return False  # 无法检测，视为不满足
    return available >= need

# --------------------- 模型管理器 ---------------------
class ModelManager:
    """负责 model_list.json 的增删改查"""
    def __init__(self, json_path: Path, available_path: Path, select_path: Path):
        self.json_path = json_path
        self.available_path = available_path
        self.select_path = select_path
        self.model_list: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if not self.json_path.exists():
            self.model_list = []
            self._save()
            print(f"model列表不存在，已自动创建：{self.json_path}")
        else:
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.model_list = data if isinstance(data, list) else []
                print(f"model列表读取成功！登记model数：{len(self.model_list)}")
            except Exception as e:
                print(f"model列表读取失败（{type(e).__name__}: {e}），已重置为空列表。")
                self.model_list = []

    def _save(self):
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.model_list, f, ensure_ascii=False, indent=4)

    def get_all(self) -> List[Dict]:
        return self.model_list

    def get_model_by_name(self, name: str) -> Optional[Dict]:
        for m in self.model_list:
            if m.get("name") == name:
                return m
        return None

    def find_indices(self, models: List[Dict]) -> List[int]:
        """返回模型对象在 model_list 中的索引列表"""
        indices = []
        for m in models:
            try:
                idx = self.model_list.index(m)
                indices.append(idx)
            except ValueError:
                pass
        return indices

# --------------------- 筛选与排序工具 ---------------------
def filter_models(models: List[Dict],
                  min_context: Optional[int] = None,
                  max_price: Optional[float] = None,
                  max_vram: Optional[float] = None) -> List[Dict]:
    """根据条件筛选模型列表"""
    result = []
    for m in models:
        # 上下文窗口
        if min_context is not None:
            cw = m.get("context_window")
            try:
                if int(cw) < min_context:
                    continue
            except (TypeError, ValueError):
                continue
        # token单价
        if max_price is not None:
            pricing = m.get("pricing")
            if isinstance(pricing, dict):
                price = pricing.get("per_token")
            else:
                price = pricing
            try:
                if float(price) > max_price:
                    continue
            except (TypeError, ValueError):
                continue
        # 显存需求
        if max_vram is not None:
            vram = m.get("vram_requirement")
            try:
                if float(vram) > max_vram:
                    continue
            except (TypeError, ValueError):
                continue
        result.append(m)
    return result

def sort_models(models: List[Dict], sort_by: int = 0) -> List[Dict]:
    """
    对模型列表排序（升序）。
    sort_by: 0-显存需求, 1-上下文窗口, 2-token单价
    """
    def get_vram(m):
        try: return float(m.get("vram_requirement", float("inf")))
        except: return float("inf")

    def get_context(m):
        try: return int(m.get("context_window", 0))
        except: return 0

    def get_price(m):
        p = m.get("pricing")
        if isinstance(p, dict):
            val = p.get("per_token", float("inf"))
        else:
            val = p
        try: return float(val)
        except: return float("inf")

    if sort_by == 1:
        key = get_context
    elif sort_by == 2:
        key = get_price
    else:  # 默认0
        key = get_vram
    return sorted(models, key=key)

# --------------------- 自动选择核心 ---------------------
def auto_select(manager: ModelManager,
                min_context: Optional[int] = None,
                max_price: Optional[float] = None,
                max_vram: Optional[float] = None,
                sort_by: int = 0) -> Optional[Dict]:
    """
    执行自动匹配流程：
    1. 筛选 -> 排序 -> 写入 available_models.json (索引列表)
    2. 逐一检查硬件显存，直到找到可运行的模型
    3. 将选中模型写入 selected_model.json 并返回
    """
    all_models = manager.get_all()
    if not all_models:
        print("模型列表为空，无法自动选择。")
        return None

    # 筛选
    candidates = filter_models(all_models, min_context, max_price, max_vram)
    if not candidates:
        print("没有满足筛选条件的模型。")
        # 写入空 available
        with open(manager.available_path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return None

    # 排序
    sorted_candidates = sort_models(candidates, sort_by)
    # 获取排序后的索引
    indices = manager.find_indices(sorted_candidates)

    # 写入 available_models.json（存储索引列表）
    with open(manager.available_path, "w", encoding="utf-8") as f:
        json.dump(indices, f, ensure_ascii=False, indent=4)

    # 硬件检测
    available_vram = get_gpu_memory_gb()
    if available_vram is None:
        print("警告：无法获取GPU显存信息，将认为本地模型显存不足。")

    # 依次尝试
    selected = None
    for i, idx in enumerate(indices):
        model = sorted_candidates[i]
        # 检查硬件
        if model.get("category") == "local":
            need_vram = model.get("vram_requirement", 0)
            if not check_vram_requirement(need_vram, available_vram):
                print(f"跳过模型 {model.get('name')}：显存不足（需要{need_vram}GB，可用{available_vram}GB）")
                continue
        # 通过检查，选中
        selected = model
        break

    if selected is None:
        print("所有备选模型均不满足当前硬件条件。")
        # 清空 selected
        if manager.select_path.exists():
            manager.select_path.unlink()
        return None

    # 写入 selected_model.json
    with open(manager.select_path, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=4)
    print(f"自动选择成功！模型：{selected.get('name')}")
    return selected

# --------------------- 手动选择辅助 ---------------------
def manual_select(manager: ModelManager, model_name: str) -> bool:
    """手动指定模型名称，写入 selected_model.json"""
    model = manager.get_model_by_name(model_name)
    if model is None:
        print(f"未找到名称为 '{model_name}' 的模型。")
        return False
    with open(manager.select_path, "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=4)
    print(f"已手动选择模型：{model_name}")
    return True

# --------------------- 控制台UI ---------------------
def print_header():
    print("\n" + "=" * 60)
    print("              AI 模型选择器")
    print("=" * 60)

def display_models(manager: ModelManager):
    models = manager.get_all()
    if not models:
        print("\n当前没有任何已登记的模型。")
        return

    print("\n已登记模型列表：")
    print("-" * 90)
    header = f"{'序号':<4} {'名称':<20} {'类别':<8} {'上下文':<8} {'显存(GB)':<10} {'单价':<10}"
    print(header)
    print("-" * 90)
    for i, m in enumerate(models, 1):
        name = m.get("name", "?")[:18]
        cat = m.get("category", "?")
        ctx = m.get("context_window", "?")
        vram = m.get("vram_requirement", "?")
        pricing = m.get("pricing", "?")
        if isinstance(pricing, dict):
            price = pricing.get("per_token", "?")
        else:
            price = pricing
        print(f"{i:<4} {name:<20} {cat:<8} {str(ctx):<8} {str(vram):<10} {str(price):<10}")
    print("-" * 90)

def manual_selection_ui(manager: ModelManager):
    """手动选择交互流程"""
    print("\n>>> 手动选择模式")
    while True:
        display_models(manager)
        print("\n操作：")
        print("  s <关键词>  - 按名称搜索（支持模糊）")
        print("  f <类别>    - 按类别筛选 (local/cloud)")
        print("  r           - 重置显示（取消筛选）")
        print("  o <字段>    - 排序 (vram/context/price/name)")
        print("  sel <名称>  - 直接选择指定模型")
        print("  sel <序号>  - 选择列表中序号对应的模型")
        print("  q           - 返回主菜单")

        cmd = input("\n请输入指令: ").strip().split()
        if not cmd:
            continue
        action = cmd[0].lower()

        # 基础视图（全量）
        models = manager.get_all()

        # 搜索
        if action == "s" and len(cmd) > 1:
            keyword = " ".join(cmd[1:]).lower()
            models = [m for m in models if keyword in m.get("name", "").lower()]
            print(f"搜索 '{keyword}' 结果：")
            for i, m in enumerate(models):
                print(f"{i+1}. {m.get('name')}")
        # 类别筛选
        elif action == "f" and len(cmd) > 1:
            cat = cmd[1].lower()
            models = [m for m in models if m.get("category", "").lower() == cat]
            print(f"筛选类别 '{cat}' 结果：")
            for i, m in enumerate(models):
                print(f"{i+1}. {m.get('name')}")
        # 重置
        elif action == "r":
            models = manager.get_all()
        # 排序
        elif action == "o" and len(cmd) > 1:
            field = cmd[1].lower()
            if field == "vram":
                models = sorted(models, key=lambda x: float(x.get("vram_requirement", float("inf"))))
            elif field == "context":
                models = sorted(models, key=lambda x: int(x.get("context_window", 0)))
            elif field == "price":
                def get_price(m):
                    p = m.get("pricing")
                    if isinstance(p, dict): p = p.get("per_token", float("inf"))
                    return float(p) if p is not None else float("inf")
                models = sorted(models, key=get_price)
            elif field == "name":
                models = sorted(models, key=lambda x: x.get("name", ""))
            else:
                print("不支持的排序字段。可用: vram/context/price/name")
                continue
            print("排序后列表：")
            for i, m in enumerate(models):
                print(f"{i+1}. {m.get('name')}")
        # 选择
        elif action == "sel" and len(cmd) > 1:
            target = " ".join(cmd[1:])
            # 尝试按序号选择
            try:
                idx = int(target) - 1
                if 0 <= idx < len(models):
                    selected = models[idx]
                    confirm = input(f"确认选择模型 '{selected.get('name')}' ? (y/n): ").lower()
                    if confirm == 'y':
                        if manual_select(manager, selected.get('name')):
                            return
                    else:
                        continue
                else:
                    print("序号超出范围。")
            except ValueError:
                # 按名称选择
                if manual_select(manager, target):
                    return
        elif action == "q":
            return
        else:
            print("未知指令，请重试。")

def auto_selection_ui(manager: ModelManager):
    """自动匹配交互流程"""
    print("\n>>> 自动匹配模式")
    print("输入筛选条件（直接回车表示不限制该项）：")
    try:
        min_ctx = input("  最小上下文窗口（整数）: ").strip()
        min_ctx = int(min_ctx) if min_ctx else None
    except:
        min_ctx = None
    try:
        max_price = input("  最大token单价（浮点数）: ").strip()
        max_price = float(max_price) if max_price else None
    except:
        max_price = None
    try:
        max_vram = input("  最大显存需求（GB，浮点数）: ").strip()
        max_vram = float(max_vram) if max_vram else None
    except:
        max_vram = None

    print("\n排序依据：")
    print("  0 - 显存需求（默认）")
    print("  1 - 上下文窗口")
    print("  2 - token单价")
    sort_choice = input("请输入序号 (0/1/2): ").strip()
    if sort_choice not in ("0", "1", "2"):
        print("无效选择，使用默认值 0。")
        sort_by = 0
    else:
        sort_by = int(sort_choice)

    print("\n正在执行自动匹配...")
    selected = auto_select(manager, min_ctx, max_price, max_vram, sort_by)
    if selected:
        print(f"最终选定模型：{selected.get('name')}")
        print(f"详细信息：{json.dumps(selected, ensure_ascii=False, indent=2)}")
    else:
        print("未选出合适的模型。")

def console_ui(manager: ModelManager):
    """主控制台界面"""
    while True:
        print_header()
        print("主菜单：")
        print("  1. 查看所有模型")
        print("  2. 手动选择模型")
        print("  3. 自动匹配模型")
        print("  4. 退出程序")
        choice = input("\n请输入选项: ").strip()
        if choice == "1":
            display_models(manager)
            input("\n按回车返回主菜单...")
        elif choice == "2":
            manual_selection_ui(manager)
        elif choice == "3":
            auto_selection_ui(manager)
            input("\n按回车返回主菜单...")
        elif choice == "4":
            print("程序结束。")
            break
        else:
            print("无效选项，请重新输入。")

# --------------------- 统一入口函数 ---------------------
def run_model_selector(config: Optional[Dict] = None):
    """
    模型选择器统一入口。
    参数 config 为 None 或未提供时启动控制台交互界面（UI模式）。
    否则为静默模式，根据 config 内容完成选择并打印报告。

    config 示例：
    {
        "mode": "auto",
        "min_context_window": 4096,     # 可选
        "max_price_per_token": 0.01,    # 可选
        "max_vram": 8,                  # 可选
        "sort_by": 0                    # 0:vram,1:context,2:price
    }
    或
    {
        "mode": "manual",
        "model_name": "某个模型名"
    }
    """
    # 初始化管理器
    json_path = Path(os.path.join(mp, "model_list.json"))
    available_path = Path(os.path.join(mp, "available_models.json"))
    select_path = Path(os.path.join(mp, "selected_model.json"))
    manager = ModelManager(json_path, available_path, select_path)

    # 无配置或配置不合法 → UI模式
    if config is None or not isinstance(config, dict) or "mode" not in config:
        console_ui(manager)
        return

    mode = config.get("mode", "ui").lower()
    print(f"\n--- 静默模式运行 (mode={mode}) ---")

    if mode == "auto":
        # 提取参数，缺失则用None
        min_ctx = config.get("min_context_window")
        max_price = config.get("max_price_per_token")
        max_vram = config.get("max_vram")
        sort_by = config.get("sort_by", 0)
        if sort_by not in (0,1,2):
            sort_by = 0

        selected = auto_select(manager, min_ctx, max_price, max_vram, sort_by)
        if selected:
            print(f"\n[自动选择完成] 模型：{selected.get('name')}")
            print(json.dumps(selected, ensure_ascii=False, indent=2))
        else:
            print("自动选择未找到合适的模型。")
    elif mode == "manual":
        model_name = config.get("model_name")
        if not model_name:
            print("错误：手动模式需要提供 model_name")
            return
        if manual_select(manager, model_name):
            print(f"[手动选择完成] 模型：{model_name}")
        else:
            print("手动选择失败，请检查模型名称。")
    else:
        print("未知模式，启动UI。")
        console_ui(manager)

# --------------------- 调试入口 ---------------------
if __name__ == "__main__":
    # 无参数调用 → 启动UI模式
    run_model_selector()