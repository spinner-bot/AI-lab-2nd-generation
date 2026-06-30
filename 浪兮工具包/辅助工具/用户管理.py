# 浪兮工具包/辅助工具/用户管理.py
"""
    用户与硬件注册管理器
    存储路径：数据库/系统信息/user_registry/user_registry.json
    依赖：目录构建、通用计时
    注册表结构：{硬件ID: {username:用户名, last_login:时间戳}}
    开发者：浪兮
"""
import sys
import uuid
import json
import subprocess
import os

try:
    from 浪兮工具包.辅助工具 import 目录构建 as lxpb
except ImportError:
    import 目录构建 as lxpb

try:
    from 浪兮工具包.辅助工具 import 通用计时 as lxgt
except ImportError:
    import 通用计时 as lxgt

USER_REG_DIR = os.path.join(lxpb.S_DIR, "user_registry")
USER_REG_JSON = os.path.join(USER_REG_DIR, "user_registry.json")
os.makedirs(USER_REG_DIR, exist_ok=True)

class UserManager:
    def __init__(self):
        self._cached_hardware_id = None
        self._reg_data = {}
        self._load_reg_json()

    def _get_raw_hardware_id(self) -> str:
        plat = sys.platform
        if plat.startswith("win"):
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
                guid = winreg.QueryValueEx(key, "MachineGuid")[0]
                return guid.strip()
            except:
                pass
            try:
                out = subprocess.check_output(["wmic", "csproduct", "get", "UUID"], universal_newlines=True, stderr=subprocess.DEVNULL)
                lines = [l.strip() for l in out.strip().splitlines() if l.strip()]
                if len(lines) >= 2:
                    return lines[1]
            except:
                pass
        elif plat == "linux":
            try:
                with open("/etc/machine-id", "r") as f:
                    mid = f.read().strip()
                    if mid:
                        return mid
            except:
                pass
            try:
                with open("/sys/class/dmi/id/product_uuid", "r") as f:
                    uuid_str = f.read().strip()
                    if uuid_str:
                        return uuid_str
            except:
                pass
        elif plat == "darwin":
            try:
                out = subprocess.check_output(["system_profiler", "SPHardwareDataType"], universal_newlines=True, stderr=subprocess.DEVNULL)
                for line in out.splitlines():
                    if "Hardware UUID" in line:
                        return line.split(":", 1)[1].strip()
            except:
                pass
        mac_num = uuid.getnode()
        if (mac_num >> 40) & 1:
            mac_num = 0x112233445566
        mac_hex = f"{mac_num:012x}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, mac_hex))

    def _load_reg_json(self):
        if not os.path.exists(USER_REG_JSON):
            self._reg_data = {}
            self._save_reg_json()
            return
        try:
            with open(USER_REG_JSON, "r", encoding="utf-8") as f:
                self._reg_data = json.load(f)
        except Exception:
            self._reg_data = {}
            self._save_reg_json()

    def _save_reg_json(self):
        with open(USER_REG_JSON, "w", encoding="utf-8") as f:
            json.dump(self._reg_data, f, ensure_ascii=False, indent=4)

    def get_local_hardware_id(self) -> str:
        if self._cached_hardware_id is None:
            self._cached_hardware_id = self._get_raw_hardware_id()
        return self._cached_hardware_id

    def check_device_registered(self, hardware_id: str, update_time: bool = True) -> bool:
        if hardware_id not in self._reg_data:
            return False
        if update_time:
            self._reg_data[hardware_id]["last_login"] = lxgt.t14()
            self._save_reg_json()
        return True

    def register_device_user(self, hardware_id: str, username: str):
        self._reg_data[hardware_id] = {
            "username": username,
            "last_login": lxgt.t14()
        }
        self._save_reg_json()

    def get_hardware_id_by_username(self, username: str) -> str | None:
        for hid, info in self._reg_data.items():
            if info["username"] == username:
                return hid
        return None

    def get_username_by_hardware_id(self, hardware_id: str) -> str | None:
        user_info = self._reg_data.get(hardware_id)
        return user_info["username"] if user_info else None

    def rename_user_by_hardware_id(self, hardware_id: str, new_username: str) -> bool:
        if hardware_id not in self._reg_data:
            return False
        self._reg_data[hardware_id]["username"] = new_username
        self._save_reg_json()
        return True

    def unregister_device(self, hardware_id: str) -> bool:
        if hardware_id in self._reg_data:
            del self._reg_data[hardware_id]
            self._save_reg_json()
            return True
        return False

    def get_all_register_list(self) -> dict:
        return self._reg_data.copy()

    def clear_all_register(self):
        self._reg_data.clear()
        self._save_reg_json()

    # ===================== 多用户管理系统 =====================
    def _get_sorted_user_list(self) -> list:
        """获取按最后登录时间倒序排列的用户列表（最新登录在前）"""
        user_list = []
        for hid, info in self._reg_data.items():
            user_list.append({
                "hardware_id": hid,
                "username": info["username"],
                "last_login": info["last_login"]
            })
        user_list.sort(key=lambda x: x["last_login"], reverse=True)
        return user_list

    def _show_user_list(self):
        """显示用户列表，绿色高亮当前登录设备"""
        current_hid = self.get_local_hardware_id()
        user_list = self._get_sorted_user_list()

        print("\n" + "=" * 60)
        print(f"{'序号':<4}{'用户名':<15}{'硬件ID':<36}{'最后登录':<14}")
        print("-" * 60)

        for idx, user in enumerate(user_list, 1):
            prefix = "  "
            suffix = ""
            if user["hardware_id"] == current_hid:
                prefix = "\033[1;32m★ "
                suffix = " (当前登录)\033[0m"

            print(f"{prefix}{idx:<2}{user['username']:<15}{user['hardware_id']:<36}{user['last_login']:<14}{suffix}")

        print("=" * 60)
        print(f"总计：{len(user_list)} 个注册用户\n")

    def _search_user(self):
        """模糊查询用户（支持用户名/硬件ID）"""
        keyword = input("请输入查询关键词（用户名/硬件ID）：").strip()
        if not keyword:
            print("查询关键词不能为空")
            return

        found = []
        for hid, info in self._reg_data.items():
            if keyword in info["username"] or keyword in hid:
                found.append({
                    "hardware_id": hid,
                    "username": info["username"],
                    "last_login": info["last_login"]
                })

        if not found:
            print("未找到匹配的用户")
            return

        print(f"\n找到 {len(found)} 个匹配用户：")
        for user in found:
            print(f"用户名：{user['username']}")
            print(f"硬件ID：{user['hardware_id']}")
            print(f"最后登录：{user['last_login']}\n")

    def _add_new_user(self):
        """注册新用户（自动检查重复）"""
        hardware_id = input("请输入新用户硬件ID：").strip()
        if not hardware_id:
            print("硬件ID不能为空")
            return

        if self.check_device_registered(hardware_id, update_time=False):
            print("该硬件ID已被注册")
            return

        username = input("请输入用户名：").strip()
        if not username:
            print("用户名不能为空")
            return

        self.register_device_user(hardware_id, username)
        print(f"✅ 用户 {username} 注册成功")

    def _rename_user(self):
        """按硬件ID重命名用户"""
        hardware_id = input("请输入要重命名的用户硬件ID：").strip()
        if not hardware_id:
            print("硬件ID不能为空")
            return

        if not self.check_device_registered(hardware_id, update_time=False):
            print("该硬件ID未注册")
            return

        old_name = self.get_username_by_hardware_id(hardware_id)
        new_name = input(f"请输入新用户名（当前：{old_name}）：").strip()
        if not new_name:
            print("用户名不能为空")
            return

        self.rename_user_by_hardware_id(hardware_id, new_name)
        print(f"✅ 重命名成功：{old_name} → {new_name}")

    def _delete_user(self):
        """注销用户（带二次确认）"""
        hardware_id = input("请输入要注销的用户硬件ID：").strip()
        if not hardware_id:
            print("硬件ID不能为空")
            return

        if not self.check_device_registered(hardware_id, update_time=False):
            print("该硬件ID未注册")
            return

        username = self.get_username_by_hardware_id(hardware_id)
        confirm = input(f"确认注销用户 {username}？此操作不可恢复 (y/N)：").strip().lower()
        if confirm != "y":
            print("已取消注销")
            return

        self.unregister_device(hardware_id)
        print(f"✅ 用户 {username} 已注销")

    def user_management_system(self):
        """多用户管理系统主入口（主程序直接调用）"""
        print("\n" + "=" * 60)
        print("                浪兮AI-Lab 多用户管理系统")
        print("=" * 60)

        while True:
            print("\n【功能菜单】")
            print("1. 查看所有用户")
            print("2. 查询用户")
            print("3. 注册新用户")
            print("4. 重命名用户")
            print("5. 注销用户")
            print("0. 退出系统")

            choice = input("\n请输入选项编号：").strip()

            if choice == "1":
                self._show_user_list()
            elif choice == "2":
                self._search_user()
            elif choice == "3":
                self._add_new_user()
            elif choice == "4":
                self._rename_user()
            elif choice == "5":
                self._delete_user()
            elif choice == "0":
                print("退出多用户管理系统")
                break
            else:
                print("无效选项，请重新输入")

#功能
user_mgr = UserManager()

#应用
start_user_management = user_mgr.user_management_system

#封装初始化
def u_reset():
    print("正在读取设备信息……")
    for i in range(11500000):
        pass
    hid = user_mgr.get_local_hardware_id()
    print("当前设备硬件ID：", hid, sep="")
    for i in range(16500000):
        pass
    return hid


if __name__ == "__main__":
    print("当前设备硬件ID：", user_mgr.get_local_hardware_id())
    print("注册表文件路径：", USER_REG_JSON)