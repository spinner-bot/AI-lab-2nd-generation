# 浪兮工具包/辅助工具/目录构建.py
import os

# -------------------------- 自动计算绝对路径（完全匹配你的层级） --------------------------
# 当前脚本位置：浪兮AI-lab/浪兮工具包/辅助工具/
CURRENT_SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__))
# 向上推导两级到主目录：辅助工具 → 浪兮工具包 → 浪兮AI-lab
MAIN_ABS_PATH = os.path.dirname(os.path.dirname(CURRENT_SCRIPT_PATH))
# 数据库根目录
DATABASE_DIR = os.path.join(MAIN_ABS_PATH, "数据库")
# 工具包根目录
TOOLKIT_DIR = os.path.join(MAIN_ABS_PATH, "浪兮工具包")

# -------------------------- 定义需要创建的目录（新增工具包子文件夹） --------------------------
REQUIRED_DIRS = [
    # 数据库目录
    os.path.join("数据库", "临时缓存"),
    os.path.join("数据库", "用户数据"),
    os.path.join("数据库", "资源文件"),
    os.path.join("数据库", "输出结果"),
    os.path.join("数据库", "运行日志"),
    os.path.join("数据库", "系统信息"),
    # 浪兮工具包子目录
    os.path.join("浪兮工具包", "内容分装"),
    os.path.join("浪兮工具包", "微软件包"),
    os.path.join("浪兮工具包", "辅助工具"),
    os.path.join("浪兮工具包", "通用功能")
]

# -------------------------- 导出全局绝对路径（所有文件通用） --------------------------
# 任何层级的文件导入这些变量，都能直接访问对应文件夹
DB_DIR = DATABASE_DIR
T_DIR = os.path.join(DATABASE_DIR, "临时缓存")
U_DIR = os.path.join(DATABASE_DIR, "用户数据")
R_DIR = os.path.join(DATABASE_DIR, "资源文件")
O_DIR = os.path.join(DATABASE_DIR, "输出结果")
L_DIR = os.path.join(DATABASE_DIR, "运行日志")
S_DIR = os.path.join(DATABASE_DIR, "系统信息")
# 新增工具包路径导出（方便后续使用）
TK_DIR = TOOLKIT_DIR
C_DIR = os.path.join(TOOLKIT_DIR, "内容分装")
A_DIR = os.path.join(TOOLKIT_DIR, "微软件包")
H_DIR = os.path.join(TOOLKIT_DIR, "辅助工具")
C_DIR = os.path.join(TOOLKIT_DIR, "通用功能")

# -------------------------- 自动构建函数 --------------------------
def build_lab_dirs() -> str:
    """
    自动构建浪兮AI-lab全套目录结构
    已存在目录自动跳过，不覆盖任何文件
    Returns:
        str: 主目录绝对路径
    """
    print(f"开始检测文件系统结构，并自动构建……")
    print(f"主目录绝对路径：{MAIN_ABS_PATH}")

    for dir_path in REQUIRED_DIRS:
        for i in range(7500000):
            pass
        full_path = os.path.join(MAIN_ABS_PATH, dir_path)
        try:
            os.makedirs(full_path, exist_ok=True)
            print(f"  ✅{dir_path} 创建完成（或确认存在）")
        except Exception as e:
            print(f"  ❌{dir_path} 创建失败：{str(e)}")

    for i in range(11500000):
        pass
    print("目录结构构建完成！\n")
    return MAIN_ABS_PATH

# -------------------------- 单独运行测试 --------------------------
if __name__ == "__main__":
    build_lab_dirs()
