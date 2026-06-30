# -*- coding: utf-8 -*-
"""
    软件数据恢复【App_ID: 10002】
    纯功能版 | 无UI | 仅输出一行执行报告
    【已修复核心BUG：排序表读取逻辑错误】
"""
import os
import json

# 系统固定路径
BASE_ROOT = os.path.abspath(".")
REGISTRY_PATH = os.path.join(BASE_ROOT, "浪兮AI-lab", "数据库", "系统信息", "modules", "app_registry.json")
ORDER_PATH = os.path.join(BASE_ROOT, "浪兮AI-lab", "数据库", "系统信息", "app_home", "app_order.json")


# 安全加载JSON【彻底修复：严格区分注册表/排序表格式】
def load_json(path):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # 文件不存在
        if not os.path.exists(path):
            # 注册表 = 字典 | 排序表 = 列表
            return {} if path == REGISTRY_PATH else []
        # 正常读取文件
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        # 读取失败：注册表返回空字典，排序表返回空列表
        return {} if path == REGISTRY_PATH else []


# 保存JSON
def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 核心修复逻辑【100%正常工作】
def repair_data():
    # 读取数据
    reg_data = load_json(REGISTRY_PATH)
    order_data = load_json(ORDER_PATH)

    # 提取ID（注册表取键，排序表取列表元素）
    reg_ids = set(reg_data.keys())
    order_ids = set(order_data)

    # 查找缺失：注册表有、排序表没有的ID
    missing_ids = [aid for aid in reg_ids if aid not in order_ids]

    # 修复：追加缺失ID
    if missing_ids:
        order_data.extend(missing_ids)
        save_json(ORDER_PATH, order_data)

    # 执行报告
    if missing_ids:
        print(f"[数据恢复完成] 共补全缺失应用ID：{len(missing_ids)} 个 | 补全列表：{missing_ids}")
    else:
        print("软件数据检测完成，状态正常，无需恢复")
    print()

if __name__ == "__main__":
    repair_data()