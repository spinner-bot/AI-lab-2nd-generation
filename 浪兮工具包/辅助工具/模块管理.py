"""
    模块微应用管理器
    核心设计：以 应用ID 为不可变唯一主键
    数据持久化：自动存至 数据库/系统信息/module_registry.json
    主程序仅关联固定应用ID，实现架构解耦、独立迭代维护
    开发者：浪兮
"""
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import json
import tkinter as tk

try:
    import 目录构建 as lxpb
except:
    from 浪兮工具包.辅助工具 import 目录构建 as lxpb

try:
    import 浪兮工具包.微软件包.浪兮效率时钟 as lxtm
except:
    pass

try:
    import 用户管理 as lxum
except:
    from 浪兮工具包.辅助工具 import 用户管理 as lxum

# ===================== 路径配置 =====================
# 系统信息文件夹路径
SYS_INFO_DIR = os.path.join(lxpb.S_DIR, "modules")
# 模块注册表JSON文件
REGISTRY_JSON_PATH = os.path.join(SYS_INFO_DIR, "app_registry.json")

# 确保目录存在
os.makedirs(SYS_INFO_DIR, exist_ok=True)


# ====================================================

class ModuleManager:
    def __init__(self):
        # 应用注册表：key = 固定应用ID(不变量)
        # value = dict: name / desc / 预留扩展字段
        self._app_registry = {}
        # 启动自动加载本地JSON数据
        self._load_from_json()

    def _load_from_json(self):
        """私有方法：从JSON加载注册表"""
        if not os.path.exists(REGISTRY_JSON_PATH):
            # 文件不存在则初始化空注册表并新建
            self._save_to_json()
            return
        try:
            with open(REGISTRY_JSON_PATH, "r", encoding="utf-8") as f:
                self._app_registry = json.load(f)
        except Exception:
            # 损坏/解析失败，重置为空
            self._app_registry = {}
            self._save_to_json()

    def _save_to_json(self):
        """私有方法：保存注册表到JSON"""
        with open(REGISTRY_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(self._app_registry, f, ensure_ascii=False, indent=4)

    def register_module(self, app_id: str, app_name: str, desc: str = ""):
        """注册微应用/模块"""
        if app_id in self._app_registry:
            print(f"✅应用(App_ID {app_id})已在注册表中，跳过注册")
            return
        self._app_registry[app_id] = {
            "name": app_name,
            "desc": desc
        }
        # 注册后自动持久化
        self._save_to_json()
        print(f"✅应用(App_ID {app_id})完成注册")

    def unregister_module(self, app_id: str) -> bool:
        """根据应用ID 注销模块"""
        if app_id in self._app_registry:
            del self._app_registry[app_id]
            self._save_to_json()
            return True
        return False

    def get_module_info(self, app_id: str) -> dict | None:
        """通过应用ID 查询模块完整信息"""
        return self._app_registry.get(app_id, None)

    def get_app_id_by_name(self, app_name: str) -> str | None:
        """通过应用名称 反向查找应用ID"""
        for aid, info in self._app_registry.items():
            if info["name"] == app_name:
                return aid
        return None

    def is_module_exist(self, app_id: str) -> bool:
        """判断应用ID 是否已注册"""
        return app_id in self._app_registry

    def list_all_modules(self) -> dict:
        """获取所有已注册模块注册表"""
        return self._app_registry.copy()

    def clear_all_modules(self):
        """清空所有注册模块（调试专用）"""
        self._app_registry.clear()
        self._save_to_json()

    # ===================== 新增：你要求的3个核心函数 =====================
    def sync_registry(self):
        """
        同步内存与文件注册表：求并集并双向补足缺失数据
        规则：
        1. 合并两边所有AppID，不删除任何有效条目
        2. 相同ID的字段：优先保留非空值，内存优先级高于文件
        3. 自动处理None值，统一转为空字符串
        4. 同步后同时更新内存和文件，保证完全一致
        """
        # 1. 强制加载文件最新数据（忽略缓存）
        file_registry = {}
        if os.path.exists(REGISTRY_JSON_PATH):
            try:
                with open(REGISTRY_JSON_PATH, "r", encoding="utf-8") as f:
                    file_registry = json.load(f)
            except Exception:
                file_registry = {}

        # 2. 获取当前内存注册表
        mem_registry = self._app_registry.copy()

        # 3. 计算所有AppID的并集
        all_app_ids = set(mem_registry.keys()) | set(file_registry.keys())
        merged_registry = {}

        # 4. 双向补足数据
        for app_id in all_app_ids:
            mem_entry = mem_registry.get(app_id, {})
            file_entry = file_registry.get(app_id, {})

            # 合并字段：内存优先，空值用文件补
            merged_entry = {
                "name": mem_entry.get("name") or file_entry.get("name") or "",
                "desc": mem_entry.get("desc") or file_entry.get("desc") or ""
            }

            merged_registry[app_id] = merged_entry

        # 5. 更新内存并写入文件
        self._app_registry = merged_registry
        self._save_to_json()
        print(f"✅ 注册表同步完成，共 {len(merged_registry)} 个应用")

    def id2n(self, app_id) -> str | None:
        """输入AppID（支持int/str），返回应用名称，不存在返回None"""
        self._load_from_json()  # 自动刷新最新数据
        if isinstance(app_id, int):
            app_id = str(app_id)
        info = self._app_registry.get(app_id)
        return info["name"] if info else None

    def n2id(self, app_name: str) -> str | None:
        """输入应用名称，返回对应AppID，不存在返回None"""
        self._load_from_json()  # 自动刷新最新数据
        for aid, info in self._app_registry.items():
            if info["name"] == app_name:
                return aid
        return None


# 全局单例实例，全项目统一调用
mm = ModuleManager()


# 软件系统初始化
def mm_reset():
    global apps  # 声明修改全局apps列表
    print("开始读取软件注册表……")

    # ===================== 强制同步注册表 =====================
    sync()
    # ==========================================================

    # ===================== 加载最新注册表数据 =====================
    mm._load_from_json()

    # ===================== 【核心：同步app_order.json序列表】 =====================
    # 你的应用序列表路径（严格按你提供的路径）
    APP_ORDER_PATH = os.path.join(lxpb.S_DIR, "app_home", "app_order.json")
    # 确保目录存在
    os.makedirs(os.path.dirname(APP_ORDER_PATH), exist_ok=True)

    # 加载序列表：不存在则创建空列表
    app_order = []
    if os.path.exists(APP_ORDER_PATH):
        with open(APP_ORDER_PATH, "r", encoding="utf-8") as f:
            app_order = json.load(f)

    # 遍历注册表，将缺失的AppID追加到序列表末尾
    for app_id in mm._app_registry.keys():
        if app_id not in app_order:
            app_order.append(app_id)
            #print(f"📌 自动更新序列表：新增AppID {app_id}")

    # 保存更新后的序列表
    with open(APP_ORDER_PATH, "w", encoding="utf-8") as f:
        json.dump(app_order, f, ensure_ascii=False, indent=4)
    # ============================================================================

    # ===================== 自动补全全局apps列表（原有逻辑保留） =====================
    exist_app_ids = [item["app_id"] for item in apps]
    for app_id, app_info in mm._app_registry.items():
        if app_id not in exist_app_ids:
            new_app = {
                "app_id": app_id,
                "app_name": app_info.get("name", ""),
                "desc": app_info.get("desc", "")
            }
            apps.append(new_app)
            print(f"📌 自动补全应用：{app_info.get('name')} (ID:{app_id})")
    # ============================================================================

    # 原有注册逻辑（完全保留）
    for app in apps:
        for i in range(11500000):
            pass
        mm.register_module(
            app_id=app["app_id"],
            app_name=app["app_name"],
            desc=app["desc"]
        )
    for i in range(26500000):
        pass
    print("软件系统初始化完成！\n")


# 全局快捷函数（直接调用，不用写mm.xxx）
def sync():
    mm.sync_registry()


def id2n(app_id):
    return mm.id2n(app_id)


def n2id(app_name):
    return mm.n2id(app_name)


# 初始软件表
apps = \
    [
        {
            "app_id": "0000",
            "app_name": "虚拟测试软件",
            "desc": "该虚拟软件用于系统测试"
        },
        {
            "app_id": "10001",
            "app_name": "多用户",
            "desc": "系统用户服务"
        },
        {
            "app_id": "10002",
            "app_name": "软件数据恢复",
            "desc": "系统软件服务"
        },
        {
            "app_id": "10003",
            "app_name": "系统补丁",
            "desc": "修复问题"
        },
        {
            "app_id": "10004",
            "app_name": "经典模式",
            "desc": "使用经典模式"
        },
        {
            "app_id": "20001",
            "app_name": "文件导入",
            "desc": "通用的跨软件文件导入助手"
        },
        {
            "app_id": "30001",
            "app_name": "应用桌面",
            "desc": "系统默认的应用主页"
        },
        {
            "app_id": "110001",
            "app_name": "词表管理",
            "desc": "NLP词表管理+成品词表导入"
        },
        {
            "app_id": "110002",
            "app_name": "文库管理",
            "desc": "文本文库管理"
        },
        {
            "app_id": "110003",
            "app_name": "JSON阅读器",
            "desc": "提供清晰的JSON阅读功能"
        },
        {
            "app_id": "110004",
            "app_name": "快速词表切换",
            "desc": "浅度扫描，操作简便"
        },
        {
            "app_id": "110005",
            "app_name": "csv绘图器",
            "desc": "csv2jpg"
        },
        {
            "app_id": "110006",
            "app_name": "csv150528工具",
            "desc": "csv150528工具,功能单一"
        },
        {
            "app_id": "110007",
            "app_name": "csv转图i2Rv适配",
            "desc": "csv转图i2Rv适配,功能单一"
        },
        {
            "app_id": "110008",
            "app_name": "csv数据i2Rv切分",
            "desc": "csv数据i2Rv切分,功能单一"
        },
        {
            "app_id": "110009",
            "app_name": "i2Rv数据包整合",
            "desc": "i2Rv数据包整合,功能单一"
        },
        {
            "app_id": "110010",
            "app_name": "i2Rv情绪映射",
            "desc": "i2Rv项目模块，第一分流程"
        },
        {
            "app_id": "110011",
            "app_name": "i2Rv支流B清洗",
            "desc": "130001逆操作"
        },
        {
            "app_id": "120001",
            "app_name": "词义推理",
            "desc": "词向量逻辑匹配计算"
        },
        {
            "app_id": "130001",
            "app_name": "i2Rv输入支流B",
            "desc": "i2Rv项目模块，第一分流程"
        },
        {
            "app_id": "130002",
            "app_name": "i2Rv输入支流A",
            "desc": "i2Rv项目模块，第一分流程"
        },
        {
            "app_id": "210001",
            "app_name": "平行语料处理",
            "desc": "平行语料管理+全自动导入，包括格式转换与内容清洗"
        },
        {
            "app_id": "310001",
            "app_name": "翻译训练配置器",
            "desc": "这是一个翻译训练配置器"
        },
        {
            "app_id": "310002",
            "app_name": "Non-Attention 翻译训练器",
            "desc": "这是一个Non-Attention 翻译训练器"
        },
        {
            "app_id": "2010001",
            "app_name": "浪兮效率时钟",
            "desc": "浪兮效率 | 高效生活"
        },
        {
            "app_id": "3010001",
            "app_name": "i2Rv数据初始化",
            "desc": "i2Rv项目资源自动初始化"
        }
    ]

if __name__ == "__main__":
    print(f"注册表文件路径：{REGISTRY_JSON_PATH}")