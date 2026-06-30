# -*- coding: utf-8 -*-
"""
    系统补丁【AppID:10003】
    功能：删除 主路径/浪兮AI‑lab 文件夹
    规范：目录构建 | 仅必要用户提示 | 无内部信息展示
"""
import os
import shutil

# 导入目录构建
try:
    import 浪兮工具包.辅助工具.目录构建 as lxpb
except ImportError:
    import 目录构建 as lxpb

# 目标文件夹路径
TARGET_FOLDER = os.path.join(lxpb.MAIN_ABS_PATH, "浪兮AI-lab")

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

def log(msg, color=Colors.RESET):
    print(f"{color}{msg}{Colors.RESET}")

def patch_main():
    #log("=== 系统补丁执行中 ===", Colors.BLUE)
    if not os.path.exists(TARGET_FOLDER):
        log("step1.执行跳过", Colors.BLUE)
        return

    try:
        shutil.rmtree(TARGET_FOLDER)
        log("step1.执行成功", Colors.GREEN)
    except Exception as e:
        pass
        log(f"step1.执行失败（{str(e)}）", Colors.RED)

    #input("\n按回车键退出...")

import json

def patch2():
    json_path = os.path.join(lxpb.S_DIR, "app_home", "app_order.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and data:
            data.pop()
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log("step2.执行成功", Colors.GREEN)
    except Exception as e:
        pass
        log(f"step2.执行失败（{str(e)}）", Colors.RED)


def run_app(run_app_main, *info):
    patch_main()
    patch2()

if __name__ == "__main__":
    run_app(None)