# -*- coding: utf-8 -*-
"""
    i2Rv数据初始化【AppID:3010001】
    功能：一键式i2Rv数据集全流程初始化（导入-处理-生成-清理）
    规范：顺序执行 | 启动器接口调用 | 目录构建 | 无隐私信息展示
    核心路径：R_DIR/图片资源/110005
"""
import os
import json
import shutil
from pathlib import Path

# 系统环境配置
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# ===================== 强制导入目录构建（项目可迁移） =====================
try:
    import 浪兮工具包.辅助工具.目录构建 as lxpb
except ImportError:
    import 目录构建 as lxpb

# ===================== 全局路径配置（严格按需求定义） =====================
# 项目核心根路径
BASE_DIR = lxpb.R_DIR
# 110005核心文件夹
TOOL_110005_ROOT = os.path.join(BASE_DIR, "图片资源", "110005")
# 目标CSV存储文件夹
CSV_TARGET_DIR = os.path.join(TOOL_110005_ROOT, "csv")
# 最终数据包文件夹（告知用户路径）
PACKAGE_DIR = os.path.join(TOOL_110005_ROOT, "i2Rv整合数据包")
# 20001文件导入的JSON路径
FILE_HELPER_JSON = os.path.join(lxpb.T_DIR, "文件助手", "file_path.json")


# ===================== 统一UI样式（无ID/迭代信息展示） =====================
class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


ICONS = {
    "step": "🔹", "success": "✅", "warn": "⚠️", "info": "📌",
    "done": "🎉", "clear": "🧹", "end": "✨"
}


def print_divider(char="=", length=60):
    print(Colors.BLUE + char * length + Colors.RESET)


def log(msg, color=Colors.RESET):
    print(f"{color}{msg}{Colors.RESET}")


def step_log(step_num, msg):
    """步骤日志格式化"""
    log(f"{ICONS['step']} 步骤{step_num}：{msg}", Colors.BLUE)


# ===================== 核心工具函数 =====================
def delete_file_helper_json():
    """步骤1：删除20001的导入列表JSON文件"""
    if os.path.exists(FILE_HELPER_JSON):
        try:
            os.remove(FILE_HELPER_JSON)
        except:
            pass


def load_csv_file_paths():
    """读取20001的JSON，筛选CSV格式文件路径"""
    if not os.path.exists(FILE_HELPER_JSON):
        return []
    try:
        with open(FILE_HELPER_JSON, "r", encoding="utf-8") as f:
            path_list = json.load(f)
        # 筛选.csv后缀文件（忽略大小写）
        return [p for p in path_list if str(p).lower().endswith(".csv") and os.path.exists(p)]
    except:
        return []


def safe_copy_file(src_path, target_dir):
    """
    安全复制文件：重名自动添加后缀(1)(2)...
    :param src_path: 源文件路径
    :param target_dir: 目标文件夹
    :return: 复制结果
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    file_name = os.path.basename(src_path)
    name, ext = os.path.splitext(file_name)
    target_path = os.path.join(target_dir, file_name)
    counter = 1

    # 重名自动重命名
    while os.path.exists(target_path):
        target_path = os.path.join(target_dir, f"{name}({counter}){ext}")
        counter += 1

    shutil.copy2(src_path, target_path)
    return True


# ===================== 主流程：纯顺序结构 =====================
def i2rv_init_main(run_app_main):
    print_divider()
    log(f"{ICONS['info']} i2Rv数据初始化 开始执行", Colors.GREEN)
    print_divider()

    # ============== 步骤1：删除20001的JSON文件 ==============
    step_log(1, "清理历史缓存")
    delete_file_helper_json()
    log(f"{ICONS['success']} 历史缓存清理完成", Colors.GREEN)

    # ============== 步骤2：提示用户导入CSV ==============
    step_log(2, "导入数据文件")
    log(f"{ICONS['info']} 请导入需要处理的csv数据文件", Colors.YELLOW)
    input("\n按回车键继续...")

    # ============== 步骤3：启动20001 文件导入 ==============
    step_log(3, "启动导入工具")
    run_app_main("文件导入")
    log(f"{ICONS['success']} 文件导入完成", Colors.GREEN)

    # ============== 步骤4：复制CSV文件到目标目录 ==============
    step_log(4, "复制数据文件")
    csv_list = load_csv_file_paths()
    if not csv_list:
        log(f"{ICONS['warn']} 未检测到有效的CSV文件，程序终止", Colors.RED)
        input("\n按回车键退出...")
        return

    success_copy = 0
    for csv_file in csv_list:
        if safe_copy_file(csv_file, CSV_TARGET_DIR):
            success_copy += 1
    log(f"{ICONS['success']} 复制完成：{success_copy} 个CSV文件", Colors.GREEN)

    # ============== 步骤6：启动110007 ==============
    step_log(5, "启动图片格式转换")
    run_app_main("110007")
    log(f"{ICONS['success']} 图片格式转换完成", Colors.GREEN)

    # ============== 步骤7：启动110008 ==============
    step_log(6, "启动数据切分")
    run_app_main("110008")
    log(f"{ICONS['success']} 数据切分完成", Colors.GREEN)

    # ============== 步骤8：启动110009 ==============
    step_log(7, "启动数据包整理")
    run_app_main("110009")
    log(f"{ICONS['success']} 数据包整理完成", Colors.GREEN)

    # ============== 步骤5：启动110006 ==============
    step_log(8, "启动情绪标签映射")
    run_app_main("110010")
    log(f"{ICONS['success']} 情绪标签映射完成", Colors.GREEN)

    # ============== 步骤9：启动130001 ==============
    step_log(9, "计算输入特征（支流B）")
    run_app_main("i2Rv输入支流B")
    log(f"{ICONS['success']} 输入特征（支流B）计算完成", Colors.GREEN)

    # ============== 步骤10：启动130002 ==============
    step_log(10, "计算输入特征（支流A）")
    run_app_main("130002")
    log(f"{ICONS['success']} 输入特征（支流A）计算完成", Colors.GREEN)

    # ============== 步骤11：处理完成，告知用户 ==============
    print_divider()
    step_log(11, "初始化报告")
    log(f"{ICONS['done']} 所有数据处理完毕！", Colors.GREEN)
    log(f"{ICONS['info']} 生成数据包位置：{PACKAGE_DIR}", Colors.BLUE)
    print_divider()

    # ============== 步骤12：清理残留选项 ==============
    step_log(12, "退出选项")
    log(f"{ICONS['warn']} 为保护资料，部分文件不会被自动删除", Colors.YELLOW)
    print_divider()
    log("[1] 完成并退出", Colors.GREEN)
    log("[2] 清理残留文件", Colors.YELLOW)
    print_divider()

    while True:
        choice = input("请选择操作：").strip()
        if choice == "1":
            log(f"{ICONS['success']} 已选择直接完成", Colors.GREEN)
            break
        elif choice == "2":
            log(f"{ICONS['clear']} 启动残留文件清理工具", Colors.BLUE)
            run_app_main("110002")
            break
        else:
            log(f"{ICONS['warn']} 输入无效，请重新选择", Colors.RED)

    # ============== 步骤13：程序结束 ==============
    print_divider()
    log(f"{ICONS['end']} 感谢使用i2Rv数据初始化工具", Colors.GREEN)
    log(f"👨‍💻 开发团队：DIG Lab Group URG 25", Colors.BLUE)
    print_divider()
    input("\n按回车键退出工具...")


# ===================== 标准启动接口 =====================
def run_app(run_app_main, *info):
    i2rv_init_main(run_app_main)


if __name__ == "__main__":
    # 独立运行时的兼容占位
    def mock_run_app(name):
        log(f"[模拟启动] {name}", Colors.YELLOW)


    run_app(mock_run_app)