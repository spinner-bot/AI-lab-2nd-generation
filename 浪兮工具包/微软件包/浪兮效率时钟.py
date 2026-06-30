import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import tkinter.simpledialog as sd
import os
import json
import calendar
import zipfile
import shutil
from datetime import datetime, date, timedelta



# ===================== 核心配置 =====================

from 浪兮工具包.辅助工具 import 目录构建 as lxpb
ROOT_DIR = os.path.join(lxpb.U_DIR, "浪兮效率时钟")

DATA_DIR = os.path.join(ROOT_DIR, "数据")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
PLAN_PATH = os.path.join(ROOT_DIR, "plans.json")
SCHEDULE_RULES_PATH = os.path.join(ROOT_DIR, "schedule_rules.json")
MANUAL_PLANS_PATH = os.path.join(ROOT_DIR, "manual_plans.json")
os.makedirs(ROOT_DIR, exist_ok=True)

DEFAULT_PLANS = {
    "工作日": {
        "type": "切分制",
        "items": [{"name": "睡觉", "hours": 8}, {"name": "工作", "hours": 8}, {"name": "生活", "hours": 8}],
        "bg_tag": "生活",
        "color": [0, 255, 255]
    },
    "休息日": {
        "type": "分配制",
        "items": [{"name": "睡觉", "hours": 9}, {"name": "休闲", "hours": 6}, {"name": "运动", "hours": 2}],
        "bg_tag": "",
        "color": [147, 253, 2]
    },
    "吃了就睡": {
        "type": "切分制",
        "items": [{"name": "吃饭", "hours": 1.5}, {"name": "睡觉", "hours": 22.5}],
        "bg_tag": "睡觉",
        "color": [255, 134, 68]
    }
}

DEFAULT_SCHEDULE_RULES = [
    {"rule_type": "week", "value": "6", "plan_name": "休息日"},
    {"rule_type": "week", "value": "7", "plan_name": "休息日"},
    {"rule_type": "default", "value": "default", "plan_name": "工作日"}
]

DEFAULT_THEME = {
    "bg_window": "#f0f0f0",
    "bg_button": "#e0e0e0",
    "fg_button": "#000000",
    "bg_frame": "#d9d9d9"
}

# ===================== 工具函数 =====================
def hours_to_hm(total_hours):
    if total_hours <= 0: return "0分钟"
    h = int(total_hours)
    m = round((total_hours - h) * 60)
    return f"{h}小时{m}分钟" if h else f"{m}分钟"

def hm_to_hours(h, m):
    return round(h + m / 60, 2)

def time_str_to_minutes(t_str):
    try:
        h, m = map(int, str(t_str).split(":"))
        return h * 60 + m
    except:
        return 0

def minutes_to_time_str(minutes):
    try:
        h = max(0, minutes // 60)
        m = max(0, minutes % 60)
        return f"{h:02d}:{m:02d}"
    except:
        return "00:00"

def is_time_overlap(start1, end1, start2, end2):
    s1, e1 = time_str_to_minutes(start1), time_str_to_minutes(end1)
    s2, e2 = time_str_to_minutes(start2), time_str_to_minutes(end2)
    return not (e1 <= s2 or e2 <= s1)

def get_overlap_interval(s1, e1, s2, e2):
    s = max(s1, s2)
    e = min(e1, e2)
    return (s, e) if s < e else None

def get_time_mid_point(start, end):
    s = time_str_to_minutes(start)
    e = time_str_to_minutes(end)
    return (s + e) / 2

def auto_balance(items, target_sum=24):
    total = sum(it.get("hours", 0) for it in items)
    if total <= 0:
        n = len(items)
        each = target_sum / n
        return [{"name": it.get("name", "未知"), "hours": round(each, 2)} for it in items]
    ratio = target_sum / total
    return [{"name": it.get("name", "未知"), "hours": round(it.get("hours", 0) * ratio, 2)} for it in items]

def sort_records(records, plan_type):
    records = [r for r in records if isinstance(r, dict)]
    if plan_type == "切分制":
        return sorted(records, key=lambda x: time_str_to_minutes(x.get("开始", "00:00")))
    else:
        return sorted(records, key=lambda x: (
            get_time_mid_point(x.get("开始", "00:00"), x.get("结束", "00:00")),
            -(time_str_to_minutes(x.get("结束", "00:00")) - time_str_to_minutes(x.get("开始", "00:00"))),
            x.get("标签", "")
        ))

def choose_tag_dialog(parent, title, msg, options):
    options = [o for o in options if o]
    if not options:
        messagebox.showwarning("提示", "无可用类别")
        return None
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.geometry("400x150")
    dialog.transient(parent)
    dialog.grab_set()
    ttk.Label(dialog, text=msg, wraplength=350).pack(pady=10)
    var = tk.StringVar(value=options[0])
    cb = ttk.Combobox(dialog, textvariable=var, values=options, state="readonly")
    cb.pack(pady=5, fill=tk.X, padx=20)
    result = None
    def confirm():
        nonlocal result
        result = var.get()
        dialog.destroy()
    ttk.Button(dialog, text="确认", command=confirm).pack(pady=10)
    parent.wait_window(dialog)
    return result

def rgb_to_hex(r, g, b):
    try:
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"
    except:
        return "#808080"

def parse_week_selection(week_str):
    result = set()
    parts = week_str.split(',')
    for p in parts:
        if '-' in p:
            a, b = p.split('-')
            for i in range(int(a), int(b)+1):
                result.add(str(i))
        else:
            result.add(p.strip())
    return result

def format_week_display(week_set):
    week_map = {"1":"周一","2":"周二","3":"周三","4":"周四","5":"周五","6":"周六","7":"周日"}
    return ','.join([week_map.get(w,w) for w in sorted(week_set, key=int)])

def parse_month_selection(month_str):
    result = set()
    parts = month_str.split(',')
    for p in parts:
        if '-' in p:
            a, b = p.split('-')
            for i in range(int(a), int(b)+1):
                result.add(str(i))
        else:
            result.add(p.strip())
    return result

def format_month_display(month_set):
    return ','.join(sorted(month_set, key=int))

def parse_year_selection(year_str):
    result = set()
    parts = year_str.split(',')
    for p in parts:
        if '-' in p and len(p) == 5:
            result.add(p.strip())
    return result

def format_year_display(year_set):
    return ','.join(sorted(year_set))

# ===================== DataCore =====================
class DataCore:
    @staticmethod
    def get_today_date():
        return date.today().strftime("%Y-%m-%d")

    @staticmethod
    def get_day_dir(day=None):
        day = day or DataCore.get_today_date()
        return os.path.join(DATA_DIR, str(day))

    @staticmethod
    def get_records_path(day=None):
        return os.path.join(DataCore.get_day_dir(day), "records.json")

    @staticmethod
    def get_day_plan_path(day=None):
        return os.path.join(DataCore.get_day_dir(day), "day_plan.json")

    @staticmethod
    def load_day_plan(day=None):
        day = day or DataCore.get_today_date()
        manual_plans = DataCore.load_manual_plans()
        if day in manual_plans:
            return {"name": manual_plans[day], "type": DataCore.load_plans()[manual_plans[day]]["type"]}
        rules = DataCore.load_schedule_rules()
        target_date = datetime.strptime(day, "%Y-%m-%d")
        year = target_date.year
        month = target_date.month
        week_num = str(target_date.isoweekday())
        month_day = target_date.strftime("%m-%d")
        day_in_month = target_date.day
        month_week_index = (day_in_month - 1) // 7 + 1
        month_week_str = f"{month_week_index}-{week_num}"
        for rule in rules[:-1]:
            r_type = rule["rule_type"]
            r_val = rule["value"]
            if r_type == "week":
                week_set = parse_week_selection(r_val)
                if week_num in week_set:
                    plan_name = rule["plan_name"]
                    return {"name": plan_name, "type": DataCore.load_plans()[plan_name]["type"]}
            elif r_type == "month":
                month_set = parse_month_selection(r_val)
                if str(month) in month_set:
                    plan_name = rule["plan_name"]
                    return {"name": plan_name, "type": DataCore.load_plans()[plan_name]["type"]}
            elif r_type == "year":
                year_set = parse_year_selection(r_val)
                if month_day in year_set:
                    plan_name = rule["plan_name"]
                    return {"name": plan_name, "type": DataCore.load_plans()[plan_name]["type"]}
            elif r_type == "month_week" and r_val == month_week_str:
                plan_name = rule["plan_name"]
                return {"name": plan_name, "type": DataCore.load_plans()[plan_name]["type"]}
        default_plan = rules[-1]["plan_name"]
        return {"name": default_plan, "type": DataCore.load_plans()[default_plan]["type"]}

    @staticmethod
    def save_day_plan(plan_name, day=None):
        day = day or DataCore.get_today_date()
        manual_plans = DataCore.load_manual_plans()
        manual_plans[day] = plan_name
        DataCore.save_manual_plans(manual_plans)
        path = DataCore.get_day_plan_path(day)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {"name": plan_name, "type": DataCore.load_plans()[plan_name]["type"]}
        json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    @staticmethod
    def load_manual_plans():
        try:
            if os.path.exists(MANUAL_PLANS_PATH):
                return json.load(open(MANUAL_PLANS_PATH, 'r', encoding='utf-8'))
        except:
            pass
        return {}

    @staticmethod
    def save_manual_plans(data):
        os.makedirs(ROOT_DIR, exist_ok=True)
        json.dump(data, open(MANUAL_PLANS_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    @staticmethod
    def load_schedule_rules():
        try:
            if os.path.exists(SCHEDULE_RULES_PATH):
                return json.load(open(SCHEDULE_RULES_PATH, 'r', encoding='utf-8'))
        except:
            pass
        DataCore.save_schedule_rules(DEFAULT_SCHEDULE_RULES)
        return DEFAULT_SCHEDULE_RULES

    @staticmethod
    def save_schedule_rules(rules):
        os.makedirs(ROOT_DIR, exist_ok=True)
        json.dump(rules, open(SCHEDULE_RULES_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    @staticmethod
    def load_records(day=None):
        p = DataCore.get_records_path(day)
        if not os.path.exists(p):
            return []
        try:
            data = json.load(open(p, 'r', encoding='utf-8'))
            return [r for r in data if isinstance(r, dict)]
        except:
            return []

    @staticmethod
    def save_record(r, day=None):
        if not isinstance(r, dict): return
        day = day or DataCore.get_today_date()
        rs = DataCore.load_records(day)
        rs.append(r)
        p = DataCore.get_records_path(day)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(rs, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    @staticmethod
    def delete_record(i, day=None):
        day = day or DataCore.get_today_date()
        rs = DataCore.load_records(day)
        if 0 <= i < len(rs):
            del rs[i]
            p = DataCore.get_records_path(day)
            if rs:
                json.dump(rs, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
            else:
                if os.path.exists(p):
                    os.remove(p)

    @staticmethod
    def update_record(i, r, day=None):
        if not isinstance(r, dict): return
        day = day or DataCore.get_today_date()
        rs = DataCore.load_records(day)
        if 0 <= i < len(rs):
            rs[i] = r
            p = DataCore.get_records_path(day)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            json.dump(rs, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    @staticmethod
    def save_all_records(records, day=None):
        records = [r for r in records if isinstance(r, dict)]
        day = day or DataCore.get_today_date()
        p = DataCore.get_records_path(day)
        if records:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            json.dump(records, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        else:
            if os.path.exists(p):
                os.remove(p)

    @staticmethod
    def calc_real_time_stat(day=None):
        today = DataCore.get_today_date()
        target_day = day or today
        plans = DataCore.load_plans()
        day_plan = DataCore.load_day_plan(target_day)
        plan_name = day_plan.get("name", "工作日")
        plan_exists = plan_name in plans
        plan_type = None
        bg_tag = None
        target = {}
        total_plan_hours = 0
        records = DataCore.load_records(target_day)
        has_records = len(records) > 0
        stat = {}
        total_used_hours = 0.0
        progress = 0.0
        if plan_exists:
            plan = plans[plan_name]
            plan_type = plan.get("type", "切分制")
            bg_tag = plan.get("bg_tag", "")
            items = plan.get("items", [])
            items = [it for it in items if isinstance(it, dict) and it.get("name")]
            target = {it.get("name", "未知"): it.get("hours", 0) for it in items}
            total_plan_hours = sum(target.values())
            records = sort_records(records, plan_type)
            stat = {k: 0.0 for k in target.keys()}
        used_minutes = 0
        for r in records:
            tag = r.get("标签", "")
            s = time_str_to_minutes(r.get("开始", "00:00"))
            e = time_str_to_minutes(r.get("结束", "00:00"))
            dur = max(0, (e - s) / 60)
            if plan_exists and tag in stat:
                stat[tag] += dur
            used_minutes += max(0, e - s)
        total_used_hours = used_minutes / 60
        if plan_exists and plan_type == "切分制":
            if target_day == today:
                current_minutes = datetime.now().hour * 60 + datetime.now().minute
                total_available = current_minutes
            else:
                try:
                    target_date = datetime.strptime(target_day, "%Y-%m-%d").date()
                    today_date = date.today()
                    total_available = 24 * 60 if target_date < today_date else 0
                except:
                    total_available = 0
            bg_used = max(0, (total_available - used_minutes) / 60)
            if plan_exists and bg_tag in stat:
                stat[bg_tag] += bg_used
        if plan_exists and total_plan_hours > 0:
            valid_total = sum(min(stat[k], target[k]) for k in target.keys())
            progress = (valid_total / total_plan_hours) * 100
        # 返回额外包含未封顶的单项统计（用于超限显示）
        raw_stat = stat.copy() if plan_exists else {}
        return (stat, round(progress, 1), bg_tag, target, plan_exists, plan_name, plan_type, total_used_hours,
                has_records, raw_stat)

    @staticmethod
    def time_from_start(sh, sm, h):
        try:
            s = datetime(2000, 1, 1, int(sh), int(sm))
            e = s + timedelta(hours=float(h))
            return e.hour, e.minute
        except:
            return 0, 0

    @staticmethod
    def time_to_end(eh, em, h):
        try:
            e = datetime(2000, 1, 1, int(eh), int(em))
            s = e - timedelta(hours=float(h))
            return s.hour, s.minute
        except:
            return 0, 0

    @staticmethod
    def load_config():
        try:
            if os.path.exists(CONFIG_PATH):
                c = json.load(open(CONFIG_PATH, 'r', encoding='utf-8'))
                return {
                    "overtime_threshold": c.get("overtime_threshold", 105),
                    "whiten_k": c.get("whiten_k", 0.6),
                    "show_seconds": c.get("show_seconds", True),
                    "use_24h": c.get("use_24h", True),
                    "show_ampm": c.get("show_ampm", False),
                    "theme": c.get("theme", DEFAULT_THEME)
                }
        except:
            pass
        c = {"overtime_threshold": 105, "whiten_k": 0.6, "show_seconds": True, "use_24h": True, "show_ampm": False, "theme": DEFAULT_THEME}
        DataCore.save_config(c)
        return c

    @staticmethod
    def save_config(c):
        if not isinstance(c, dict):
            c = {"overtime_threshold": 105, "whiten_k": 0.6, "show_seconds": True, "use_24h": True, "show_ampm": False, "theme": DEFAULT_THEME}
        os.makedirs(ROOT_DIR, exist_ok=True)
        json.dump(c, open(CONFIG_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    @staticmethod
    def load_plans():
        try:
            if os.path.exists(PLAN_PATH):
                plans = json.load(open(PLAN_PATH, 'r', encoding='utf-8'))
                repaired = {}
                for name, info in plans.items():
                    if not name or not isinstance(info, dict): continue
                    repaired[name] = {
                        "type": info.get("type", "切分制"),
                        "items": [it for it in info.get("items", []) if isinstance(it, dict) and it.get("name")],
                        "bg_tag": info.get("bg_tag", ""),
                        "color": info.get("color", [128, 128, 128])
                    }
                    if not repaired[name]["items"]:
                        repaired[name]["items"] = [{"name": "默认", "hours": 24}]
                return repaired if repaired else DEFAULT_PLANS.copy()
        except:
            pass
        DataCore.save_plans(DEFAULT_PLANS.copy())
        return DEFAULT_PLANS.copy()

    @staticmethod
    def save_plans(plans):
        safe_plans = {}
        for name, info in plans.items():
            if not name or not isinstance(info, dict): continue
            safe_plans[name] = {
                "type": info.get("type", "切分制"),
                "items": [it for it in info.get("items", []) if isinstance(it, dict) and it.get("name")],
                "bg_tag": info.get("bg_tag", ""),
                "color": info.get("color", [128, 128, 128])
            }
            if not safe_plans[name]["items"]:
                safe_plans[name]["items"] = [{"name": "默认", "hours": 24}]
        os.makedirs(ROOT_DIR, exist_ok=True)
        json.dump(safe_plans, open(PLAN_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# ===================== 主应用 =====================
class EfficiencyClock:
    def __init__(self, root):
        self.root = root
        self.root.title("浪兮效率时钟")
        self.root.geometry("750x650")
        self.root.minsize(650, 550)
        self.config = DataCore.load_config()
        self.overtime_threshold = self.config.get("overtime_threshold", 105)
        self.whiten_k = self.config.get("whiten_k", 0.6)
        self.show_seconds = self.config.get("show_seconds", True)
        self.use_24h = self.config.get("use_24h", True)
        self.show_ampm = self.config.get("show_ampm", False)
        self.theme = self.config.get("theme", DEFAULT_THEME)
        self.calendar_year = date.today().year
        self.calendar_month = date.today().month
        self.after_id = None
        self.plans = DataCore.load_plans()
        self.edit_plan_name = None
        self.current_view_day = None
        self.last_refresh_minute = -1
        self.current_plan_color = [128, 128, 128]
        self.quick_turn = tk.BooleanVar(value=False)
        self.apply_theme()
        self.show_home()

    def apply_theme(self):
        self.root.configure(bg=self.theme.get("bg_window", "#f0f0f0"))
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', background=self.theme.get("bg_button", "#e0e0e0"), foreground=self.theme.get("fg_button", "#000000"))
        style.configure('TFrame', background=self.theme.get("bg_window", "#f0f0f0"))
        style.configure('TLabelframe', background=self.theme.get("bg_window", "#f0f0f0"))
        style.configure('TLabelframe.Label', background=self.theme.get("bg_window", "#f0f0f0"))
        style.configure('TLabel', background=self.theme.get("bg_window", "#f0f0f0"))

    def mix_color_with_white(self, r, g, b):
        try:
            r, g, b = int(r), int(g), int(b)
            k = self.whiten_k
            nr = int(r * (1 - k) + 255 * k)
            ng = int(g * (1 - k) + 255 * k)
            nb = int(b * (1 - k) + 255 * k)
            return f"#{nr:02x}{ng:02x}{nb:02x}"
        except:
            return "#f0f0f0"

    def clear(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        for w in self.root.winfo_children(): w.destroy()

    def format_time(self, dt):
        if self.use_24h:
            fmt = "%H:%M"
            if self.show_seconds:
                fmt = "%H:%M:%S"
            return dt.strftime(fmt)
        else:
            fmt = "%I:%M"
            if self.show_seconds:
                fmt = "%I:%M:%S"
            time_str = dt.strftime(fmt).lstrip("0")
            if self.show_ampm:
                ampm = dt.strftime("%p")
                return f"{time_str} {ampm}"
            else:
                return time_str

    def show_home(self):
        self.clear()
        self.current_view_day = None
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.clock = ttk.Label(main, font=("微软雅黑", 36, "bold"))
        self.clock.pack(pady=20)
        self.stat_frame = ttk.LabelFrame(main, text="今日时间统计（点击查看/编辑）", padding=15)
        self.stat_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.stat_frame.bind("<Button-1>", lambda e: self.show_detail())
        btn_f = ttk.Frame(main)
        btn_f.pack(fill=tk.X, pady=20)
        for i in range(4): btn_f.columnconfigure(i, weight=1)
        ttk.Button(btn_f, text="记录", command=self.show_add).grid(row=0, column=0, sticky=tk.EW, padx=5)
        ttk.Button(btn_f, text="日历", command=self.show_calendar).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Button(btn_f, text="管理", command=self.show_management).grid(row=0, column=2, sticky=tk.EW, padx=5)
        ttk.Button(btn_f, text="设置", command=self.show_setting).grid(row=0, column=3, sticky=tk.EW, padx=5)
        slogan = ttk.Label(main, text="浪兮效率 | 专注高效生活", font=("微软雅黑", 10), foreground="gray")
        slogan.pack(pady=(5,0))
        self.force_refresh_home()
        self.update_home_smart()

    def force_refresh_home(self):
        now = datetime.now()
        self.last_refresh_minute = now.hour * 60 + now.minute
        result = DataCore.calc_real_time_stat()
        stat, prog, bg_tag, target, plan_exists, _, _, _, _, raw_stat = result
        for w in self.stat_frame.winfo_children(): w.destroy()
        total_t = sum(target.values())
        for tag, t in target.items():
            act = stat.get(tag, 0.0)
            raw_act = raw_stat.get(tag, 0.0)
            p = (raw_act / t) * 100 if t else 0
            exceed = p > self.overtime_threshold
            prefix = "🟢【背景类别】" if tag == bg_tag else "🔹 "
            base_txt = f"{prefix}{tag}：{hours_to_hm(act)} / {hours_to_hm(t)} ({round(p, 1)}%)"
            if exceed:
                extra_time = raw_act - t
                if extra_time > 0:
                    base_txt += f" 超出{hours_to_hm(extra_time)}"
            lbl = ttk.Label(self.stat_frame, text=base_txt, font=("微软雅黑", 11))
            lbl.pack(anchor=tk.W, pady=3)
            if exceed:
                lbl.config(foreground="red")
            lbl.bind("<Button-1>", lambda e: self.show_detail())
        c = "black" if prog == 0 else ("red" if prog < 40 else "orange" if prog < 70 else "gold" if prog < 90 else "green")
        frm = ttk.Frame(self.stat_frame)
        frm.pack(anchor=tk.W, pady=5, fill=tk.X)
        ttk.Label(frm, text="📊 有效总完成度：", font=("微软雅黑", 11, "bold")).grid(row=0, column=0)
        ttk.Label(frm, text=f"{prog}%", font=("微软雅黑", 11, "bold"), foreground=c).grid(row=0, column=1)
        ttk.Label(frm, text=f"（总计目标：{hours_to_hm(total_t)}）", font=("微软雅黑", 11, "bold")).grid(row=0, column=2)

    def update_home_smart(self):
        if not self.clock.winfo_exists(): return
        now = datetime.now()
        current_minute = now.hour * 60 + now.minute
        self.clock.config(text=self.format_time(now))
        if current_minute != self.last_refresh_minute:
            self.force_refresh_home()
        self.after_id = self.root.after(100, self.update_home_smart)

    def show_management(self):
        self.clear()
        f = ttk.Frame(self.root, padding=30)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="计划管理中心", font=("微软雅黑", 18, "bold")).pack(pady=(0, 20))
        t = DataCore.load_day_plan()
        plan = self.plans.get(t["name"], {})
        ttk.Label(f, text=f"今日计划：{t['name']}（{t['type']}）", font=("微软雅黑", 14)).pack(anchor=tk.W)
        ttk.Label(f, text=f"背景类别：{plan.get('bg_tag', '无')}", font=("微软雅黑", 12)).pack(anchor=tk.W)
        ttk.Label(f, text="计划构成：").pack(anchor=tk.W)
        for item in plan.get("items", []):
            ttk.Label(f, text=f"  • {item.get('name', '未知')}：{item.get('hours', 0)}h").pack(anchor=tk.W, padx=20)
        ttk.Separator(f, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        today_obj = date.today()
        tomorrow_str = (today_obj + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after_tomorrow_str = (today_obj + timedelta(days=2)).strftime("%Y-%m-%d")
        tmr_plan = DataCore.load_day_plan(tomorrow_str)
        dat_plan = DataCore.load_day_plan(day_after_tomorrow_str)
        ttk.Label(f, text=f"明天：{tmr_plan['name']}（{tmr_plan['type']}）", font=("微软雅黑", 12)).pack(anchor=tk.W)
        ttk.Label(f, text=f"后天：{dat_plan['name']}（{dat_plan['type']}）", font=("微软雅黑", 12)).pack(anchor=tk.W)
        ttk.Separator(f, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        bf = ttk.Frame(f)
        bf.pack(fill=tk.X, pady=10)
        for i in range(4): bf.columnconfigure(i, weight=1)
        ttk.Button(bf, text="日程安排", command=self.show_schedule).grid(row=0, column=0, sticky=tk.EW, padx=5)
        ttk.Button(bf, text="日计划管理", command=self.show_plan_management).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Button(bf, text="临时计划变更", command=self.show_temp_plan_change).grid(row=0, column=2, sticky=tk.EW, padx=5)
        ttk.Button(bf, text="返回", command=self.show_home).grid(row=0, column=3, sticky=tk.EW, padx=5)

    # ========== 日程安排完整实现 ==========
    def show_schedule(self):
        self.clear()
        f = ttk.Frame(self.root, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="📅 日程自动分配规则", font=("微软雅黑", 16, "bold")).pack(pady=10)
        top_f = ttk.Frame(f)
        top_f.pack(fill=tk.X, pady=5)
        ttk.Button(top_f, text="➕ 添加规则", command=self.add_schedule_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_f, text="👁 查看手动修改日程", command=self.show_manual_schedule).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_f, text="返回", command=self.show_management).pack(side=tk.RIGHT, padx=5)
        list_frame = ttk.LabelFrame(f, text="规则列表（优先级从上到下）")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        rules = DataCore.load_schedule_rules()
        for idx, rule in enumerate(rules):
            row = ttk.Frame(scroll_frame)
            row.pack(fill=tk.X, pady=2, padx=5)
            if rule["rule_type"] == "week":
                week_set = parse_week_selection(rule["value"])
                text = f"规则：星期 {format_week_display(week_set)} → {rule['plan_name']}"
            elif rule["rule_type"] == "month":
                month_set = parse_month_selection(rule["value"])
                text = f"规则：月份 {format_month_display(month_set)} → {rule['plan_name']}"
            elif rule["rule_type"] == "year":
                year_set = parse_year_selection(rule["value"])
                text = f"规则：每年 {format_year_display(year_set)} → {rule['plan_name']}"
            elif rule["rule_type"] == "month_week":
                try:
                    a, b = rule['value'].split('-')
                    week_map = {"1": "周一", "2": "周二", "3": "周三", "4": "周四", "5": "周五", "6": "周六", "7": "周日"}
                    text = f"规则：每月第{a}个{week_map.get(b, b)} → {rule['plan_name']}"
                except:
                    text = f"规则：按月周几{rule['value']} → {rule['plan_name']}"
            else:
                text = f"【默认兜底规则】→ {rule['plan_name']}"
            ttk.Label(row, text=text, width=50).pack(side=tk.LEFT, padx=5)
            is_default = rule["rule_type"] == "default"
            ttk.Button(row, text="编辑", command=lambda i=idx: self.edit_schedule_rule(i)).pack(side=tk.LEFT, padx=2)
            if not is_default:
                ttk.Button(row, text="删除", command=lambda i=idx: self.delete_schedule_rule(i)).pack(side=tk.LEFT, padx=2)
                ttk.Button(row, text="上移", command=lambda i=idx: self.move_up_rule(i)).pack(side=tk.LEFT, padx=2)

    def add_schedule_rule(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加日程规则")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(dialog, text="规则类型：").pack(pady=5)
        rule_type = tk.StringVar(value="week")
        type_frame = ttk.Frame(dialog)
        type_frame.pack(pady=2)
        ttk.Radiobutton(type_frame, text="按星期", variable=rule_type, value="week").grid(row=0, column=0, padx=5)
        ttk.Radiobutton(type_frame, text="按月份", variable=rule_type, value="month").grid(row=0, column=1, padx=5)
        ttk.Radiobutton(type_frame, text="按年度", variable=rule_type, value="year").grid(row=0, column=2, padx=5)
        ttk.Radiobutton(type_frame, text="按月周几", variable=rule_type, value="month_week").grid(row=0, column=3, padx=5)

        param_frame = ttk.LabelFrame(dialog, text="规则参数")
        param_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        week_frame = ttk.Frame(param_frame)
        week_vars = []
        week_days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        week_map_rev = {"周一": "1", "周二": "2", "周三": "3", "周四": "4", "周五": "5", "周六": "6", "周日": "7"}
        for i, day in enumerate(week_days):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(week_frame, text=day, variable=var)
            cb.grid(row=i//4, column=i%4, sticky=tk.W, padx=5, pady=2)
            week_vars.append((day, var))

        month_frame = ttk.Frame(param_frame)
        month_vars = []
        months = [f"{i}月" for i in range(1,13)]
        for i, mon in enumerate(months):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(month_frame, text=mon, variable=var)
            cb.grid(row=i//6, column=i%6, sticky=tk.W, padx=5, pady=2)
            month_vars.append((str(i+1), var))

        year_frame = ttk.Frame(param_frame)
        year_listbox = tk.Listbox(year_frame, height=6, selectmode=tk.MULTIPLE)
        year_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        year_scroll = ttk.Scrollbar(year_frame, orient=tk.VERTICAL, command=year_listbox.yview)
        year_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        year_listbox.config(yscrollcommand=year_scroll.set)
        year_entries = []
        def add_year_date():
            date_str = sd.askstring("添加日期", "请输入日期 (MM-DD):")
            if date_str and len(date_str)==5 and date_str[2]=='-':
                if date_str not in year_entries:
                    year_entries.append(date_str)
                    year_listbox.insert(tk.END, date_str)
        def remove_year_date():
            selected = year_listbox.curselection()
            for i in reversed(selected):
                year_entries.pop(i)
                year_listbox.delete(i)
        year_btn_frame = ttk.Frame(year_frame)
        year_btn_frame.pack(side=tk.RIGHT, padx=5)
        ttk.Button(year_btn_frame, text="添加", command=add_year_date).pack(pady=2)
        ttk.Button(year_btn_frame, text="删除", command=remove_year_date).pack(pady=2)

        month_week_frame = ttk.Frame(param_frame)
        week_num_var = tk.StringVar(value="1")
        week_num_spin = ttk.Spinbox(month_week_frame, from_=1, to=5, textvariable=week_num_var, width=5)
        weekday_in_month_var = tk.StringVar(value="周一")
        weekday_in_month_combo = ttk.Combobox(month_week_frame, textvariable=weekday_in_month_var,
                                              values=["周一", "周二", "周三", "周四", "周五", "周六", "周日"], state="readonly")

        def update_param_visibility(*args):
            week_frame.pack_forget()
            month_frame.pack_forget()
            year_frame.pack_forget()
            month_week_frame.pack_forget()
            typ = rule_type.get()
            if typ == "week":
                week_frame.pack(anchor=tk.W, pady=5)
            elif typ == "month":
                month_frame.pack(anchor=tk.W, pady=5)
            elif typ == "year":
                year_frame.pack(anchor=tk.W, pady=5, fill=tk.X)
            elif typ == "month_week":
                month_week_frame.pack(anchor=tk.W, pady=5)
                ttk.Label(month_week_frame, text="第").pack(side=tk.LEFT)
                week_num_spin.pack(side=tk.LEFT)
                ttk.Label(month_week_frame, text="周").pack(side=tk.LEFT, padx=5)
                weekday_in_month_combo.pack(side=tk.LEFT)
                weekday_in_month_combo.current(0)

        rule_type.trace_add("write", update_param_visibility)
        update_param_visibility()

        ttk.Label(dialog, text="关联计划：").pack(pady=5)
        plan_var = tk.StringVar(value=list(self.plans.keys())[0] if self.plans else "")
        ttk.Combobox(dialog, textvariable=plan_var, values=list(self.plans.keys()), state="readonly").pack()

        def confirm():
            typ = rule_type.get()
            plan_name = plan_var.get()
            if not plan_name:
                messagebox.showerror("错误", "请选择关联计划")
                return
            if typ == "week":
                selected = [week_map_rev[day] for day, var in week_vars if var.get()]
                if not selected:
                    messagebox.showerror("错误", "请至少选择一个星期")
                    return
                value = ",".join(sorted(selected, key=int))
            elif typ == "month":
                selected = [num for num, var in month_vars if var.get()]
                if not selected:
                    messagebox.showerror("错误", "请至少选择一个月")
                    return
                value = ",".join(sorted(selected, key=int))
            elif typ == "year":
                if not year_entries:
                    messagebox.showerror("错误", "请至少添加一个日期")
                    return
                value = ",".join(sorted(year_entries))
            elif typ == "month_week":
                week_idx = week_num_var.get()
                weekday_name = weekday_in_month_combo.get()
                if not weekday_name:
                    messagebox.showerror("错误", "请选择星期几")
                    return
                weekday_num = week_map_rev[weekday_name]
                value = f"{week_idx}-{weekday_num}"
            else:
                return
            rules = DataCore.load_schedule_rules()
            new_rule = {"rule_type": typ, "value": value, "plan_name": plan_name}
            rules.insert(-1, new_rule)
            DataCore.save_schedule_rules(rules)
            dialog.destroy()
            self.show_schedule()
        ttk.Button(dialog, text="确认添加", command=confirm).pack(pady=10)

    def edit_schedule_rule(self, idx):
        rules = DataCore.load_schedule_rules()
        rule = rules[idx]
        is_default = rule["rule_type"] == "default"
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑规则")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="规则类型：").pack(pady=5)
        rule_type = tk.StringVar(value=rule["rule_type"])
        type_frame = ttk.Frame(dialog)
        type_frame.pack(pady=2)
        rb_week = ttk.Radiobutton(type_frame, text="按星期", variable=rule_type, value="week")
        rb_month = ttk.Radiobutton(type_frame, text="按月份", variable=rule_type, value="month")
        rb_year = ttk.Radiobutton(type_frame, text="按年度", variable=rule_type, value="year")
        rb_monthweek = ttk.Radiobutton(type_frame, text="按月周几", variable=rule_type, value="month_week")
        rb_week.grid(row=0, column=0, padx=5)
        rb_month.grid(row=0, column=1, padx=5)
        rb_year.grid(row=0, column=2, padx=5)
        rb_monthweek.grid(row=0, column=3, padx=5)
        if is_default:
            rb_week.config(state=tk.DISABLED)
            rb_month.config(state=tk.DISABLED)
            rb_year.config(state=tk.DISABLED)
            rb_monthweek.config(state=tk.DISABLED)

        param_frame = ttk.LabelFrame(dialog, text="规则参数")
        param_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        week_frame = ttk.Frame(param_frame)
        week_vars = []
        week_days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        week_map_rev = {"周一": "1", "周二": "2", "周三": "3", "周四": "4", "周五": "5", "周六": "6", "周日": "7"}
        for i, day in enumerate(week_days):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(week_frame, text=day, variable=var)
            cb.grid(row=i//4, column=i%4, sticky=tk.W, padx=5, pady=2)
            week_vars.append((day, var))

        month_frame = ttk.Frame(param_frame)
        month_vars = []
        months = [f"{i}月" for i in range(1,13)]
        for i, mon in enumerate(months):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(month_frame, text=mon, variable=var)
            cb.grid(row=i//6, column=i%6, sticky=tk.W, padx=5, pady=2)
            month_vars.append((str(i+1), var))

        year_frame = ttk.Frame(param_frame)
        year_listbox = tk.Listbox(year_frame, height=6, selectmode=tk.MULTIPLE)
        year_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        year_scroll = ttk.Scrollbar(year_frame, orient=tk.VERTICAL, command=year_listbox.yview)
        year_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        year_listbox.config(yscrollcommand=year_scroll.set)
        year_entries = []
        def add_year_date():
            date_str = sd.askstring("添加日期", "请输入日期 (MM-DD):")
            if date_str and len(date_str)==5 and date_str[2]=='-':
                if date_str not in year_entries:
                    year_entries.append(date_str)
                    year_listbox.insert(tk.END, date_str)
        def remove_year_date():
            selected = year_listbox.curselection()
            for i in reversed(selected):
                year_entries.pop(i)
                year_listbox.delete(i)
        year_btn_frame = ttk.Frame(year_frame)
        year_btn_frame.pack(side=tk.RIGHT, padx=5)
        ttk.Button(year_btn_frame, text="添加", command=add_year_date).pack(pady=2)
        ttk.Button(year_btn_frame, text="删除", command=remove_year_date).pack(pady=2)

        month_week_frame = ttk.Frame(param_frame)
        week_num_var = tk.StringVar(value="1")
        week_num_spin = ttk.Spinbox(month_week_frame, from_=1, to=5, textvariable=week_num_var, width=5)
        weekday_in_month_var = tk.StringVar(value="周一")
        weekday_in_month_combo = ttk.Combobox(month_week_frame, textvariable=weekday_in_month_var,
                                              values=["周一", "周二", "周三", "周四", "周五", "周六", "周日"], state="readonly")

        if rule["rule_type"] == "week":
            selected_set = parse_week_selection(rule["value"])
            for day, var in week_vars:
                if week_map_rev[day] in selected_set:
                    var.set(True)
        elif rule["rule_type"] == "month":
            selected_set = parse_month_selection(rule["value"])
            for num, var in month_vars:
                if num in selected_set:
                    var.set(True)
        elif rule["rule_type"] == "year":
            selected_set = parse_year_selection(rule["value"])
            year_entries = sorted(selected_set)
            for d in year_entries:
                year_listbox.insert(tk.END, d)
        elif rule["rule_type"] == "month_week":
            parts = rule["value"].split('-')
            if len(parts) == 2:
                week_num_var.set(parts[0])
                weekday_num = parts[1]
                for day, num in week_map_rev.items():
                    if num == weekday_num:
                        weekday_in_month_var.set(day)
                        break

        def update_param_visibility(*args):
            week_frame.pack_forget()
            month_frame.pack_forget()
            year_frame.pack_forget()
            month_week_frame.pack_forget()
            typ = rule_type.get()
            if typ == "week":
                week_frame.pack(anchor=tk.W, pady=5)
            elif typ == "month":
                month_frame.pack(anchor=tk.W, pady=5)
            elif typ == "year":
                year_frame.pack(anchor=tk.W, pady=5, fill=tk.X)
            elif typ == "month_week":
                month_week_frame.pack(anchor=tk.W, pady=5)
                ttk.Label(month_week_frame, text="第").pack(side=tk.LEFT)
                week_num_spin.pack(side=tk.LEFT)
                ttk.Label(month_week_frame, text="周").pack(side=tk.LEFT, padx=5)
                weekday_in_month_combo.pack(side=tk.LEFT)

        rule_type.trace_add("write", update_param_visibility)
        update_param_visibility()

        ttk.Label(dialog, text="关联计划：").pack(pady=5)
        plan_var = tk.StringVar(value=rule["plan_name"])
        ttk.Combobox(dialog, textvariable=plan_var, values=list(self.plans.keys()), state="readonly").pack()

        def confirm():
            typ = rule_type.get()
            plan_name = plan_var.get()
            if not plan_name:
                messagebox.showerror("错误", "请选择关联计划")
                return
            if typ == "week":
                selected = [week_map_rev[day] for day, var in week_vars if var.get()]
                if not selected:
                    messagebox.showerror("错误", "请至少选择一个星期")
                    return
                value = ",".join(sorted(selected, key=int))
            elif typ == "month":
                selected = [num for num, var in month_vars if var.get()]
                if not selected:
                    messagebox.showerror("错误", "请至少选择一个月")
                    return
                value = ",".join(sorted(selected, key=int))
            elif typ == "year":
                if not year_entries:
                    messagebox.showerror("错误", "请至少添加一个日期")
                    return
                value = ",".join(sorted(year_entries))
            elif typ == "month_week":
                week_idx = week_num_var.get()
                weekday_name = weekday_in_month_combo.get()
                if not weekday_name:
                    messagebox.showerror("错误", "请选择星期几")
                    return
                weekday_num = week_map_rev[weekday_name]
                value = f"{week_idx}-{weekday_num}"
            else:
                return
            rules[idx] = {"rule_type": typ, "value": value, "plan_name": plan_name}
            DataCore.save_schedule_rules(rules)
            dialog.destroy()
            self.show_schedule()
        ttk.Button(dialog, text="确认修改", command=confirm).pack(pady=10)

    def delete_schedule_rule(self, idx):
        if messagebox.askyesno("确认", "确定删除该规则？"):
            rules = DataCore.load_schedule_rules()
            del rules[idx]
            DataCore.save_schedule_rules(rules)
            self.show_schedule()

    def move_up_rule(self, idx):
        if idx <= 0: return
        rules = DataCore.load_schedule_rules()
        rules[idx], rules[idx-1] = rules[idx-1], rules[idx]
        DataCore.save_schedule_rules(rules)
        self.show_schedule()

    def show_manual_schedule(self):
        self.clear()
        f = ttk.Frame(self.root, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="✏️ 手动修改的日程", font=("微软雅黑", 16, "bold")).pack(pady=10)
        ttk.Button(f, text="返回", command=self.show_schedule).pack(anchor=tk.E, pady=5)
        list_f = ttk.LabelFrame(f, text="手动日程列表")
        list_f.pack(fill=tk.BOTH, expand=True, pady=10)
        manual = DataCore.load_manual_plans()
        if not manual:
            ttk.Label(list_f, text="暂无手动修改的日程").pack(pady=20)
            return
        for day, plan_name in manual.items():
            row = ttk.Frame(list_f)
            row.pack(fill=tk.X, pady=2, padx=5)
            ttk.Label(row, text=f"{day} → {plan_name}", width=30).pack(side=tk.LEFT, padx=5)
            ttk.Button(row, text="取消手动设置", command=lambda d=day: self.delete_manual_schedule(d)).pack(side=tk.LEFT, padx=2)
            ttk.Button(row, text="查看", command=lambda d=day: self.show_day_preview(d)).pack(side=tk.LEFT, padx=2)

    def delete_manual_schedule(self, day):
        if messagebox.askyesno("确认", f"确定取消{day}的手动设置？"):
            DataCore.delete_manual_plan(day)
            self.show_manual_schedule()

    # ========== 临时计划变更完整实现 ==========
    def show_temp_plan_change(self):
        self.clear()
        f = ttk.Frame(self.root, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="临时计划变更 - 快速切换今日计划", font=("微软雅黑", 16, "bold")).pack(pady=10)
        current = DataCore.load_day_plan()
        ttk.Label(f, text=f"当前今日计划：{current['name']}（{current['type']}）").pack(pady=5)
        list_f = ttk.Frame(f)
        list_f.pack(fill=tk.BOTH, expand=True, pady=10)
        for name, info in self.plans.items():
            if name == current["name"]:
                ttk.Button(list_f, text=f"✅ {name} | {info['type']}", state=tk.DISABLED).pack(fill=tk.X, pady=2)
            else:
                ttk.Button(list_f, text=f"{name} | {info['type']}", command=lambda n=name: self.change_today_plan(n)).pack(fill=tk.X, pady=2)
        ttk.Button(f, text="返回", command=self.show_management).pack(pady=10)

    def change_today_plan(self, new_plan_name):
        old_plan = DataCore.load_day_plan()
        new_plan = self.plans.get(new_plan_name, None)
        if not new_plan:
            messagebox.showerror("错误", "所选计划不存在")
            return
        today = DataCore.get_today_date()
        records = DataCore.load_records(today)
        new_tags = [item["name"] for item in new_plan.get("items", [])]
        invalid_records = [r for r in records if r.get("标签") not in new_tags]
        for r in invalid_records:
            choice = choose_tag_dialog(self.root, "类别重分配", f"记录【{r.get('标签')} {r.get('开始')}-{r.get('结束')}】不在新计划中\n请选择新类别", new_tags)
            if not choice:
                messagebox.showwarning("提示", "必须选择有效类别，变更已取消")
                return
            r["标签"] = choice
        if old_plan["type"] == "分配制" and new_plan["type"] == "切分制":
            records = self.process_overlap_for_split(records, new_tags)
        DataCore.save_all_records(records, today)
        DataCore.save_day_plan(new_plan_name, today)
        messagebox.showinfo("成功", f"今日计划已切换为：{new_plan_name}")
        self.show_management()

    def process_overlap_for_split(self, records, valid_tags):
        sorted_records = sort_records(records, "分配制")
        new_records = []
        n = len(sorted_records)
        used = [False] * n
        for i in range(n):
            if used[i]: continue
            current = sorted_records[i]
            s1, e1 = time_str_to_minutes(current.get("开始")), time_str_to_minutes(current.get("结束"))
            overlaps = []
            for j in range(i+1, n):
                if used[j]: continue
                r2 = sorted_records[j]
                s2, e2 = time_str_to_minutes(r2.get("开始")), time_str_to_minutes(r2.get("结束"))
                overlap = get_overlap_interval(s1, e1, s2, e2)
                if overlap:
                    overlaps.append((j, overlap))
            if not overlaps:
                new_records.append(current)
                used[i] = True
                continue
            all_overlap_records = [current] + [sorted_records[j] for j, _ in overlaps]
            overlap_times = [o for _, o in overlaps]
            max_overlap = max(overlap_times, key=lambda x: x[1] - x[0])
            start_overlap, end_overlap = max_overlap
            options = [r.get("标签") for r in all_overlap_records]
            keep_tag = choose_tag_dialog(self.root, "重叠区间处理", f"重叠区间：{minutes_to_time_str(start_overlap)}-{minutes_to_time_str(end_overlap)}\n请选择保留的标签", options)
            if not keep_tag:
                messagebox.showwarning("提示", "必须选择有效标签，处理已取消")
                return records
            for idx, r in enumerate(all_overlap_records):
                used[i+idx] = True
                rs, re = time_str_to_minutes(r.get("开始")), time_str_to_minutes(r.get("结束"))
                if r.get("标签") == keep_tag:
                    new_records.append(r)
                    continue
                if rs < start_overlap:
                    part1 = r.copy()
                    part1["结束"] = minutes_to_time_str(start_overlap)
                    part1["内容"] = f"{r.get('内容')}(1)"
                    new_records.append(part1)
                if re > end_overlap:
                    part2 = r.copy()
                    part2["开始"] = minutes_to_time_str(end_overlap)
                    part2["内容"] = f"{r.get('内容')}(2)"
                    new_records.append(part2)
        return new_records

    # ========== 日计划管理完整实现 ==========
    def show_plan_management(self):
        self.clear()
        f = ttk.Frame(self.root, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="日计划管理", font=("微软雅黑", 16, "bold")).pack(pady=10)
        list_f = ttk.Frame(f)
        list_f.pack(fill=tk.BOTH, expand=True, pady=10)
        for name, info in self.plans.items():
            row = ttk.Frame(list_f)
            row.pack(fill=tk.X, pady=2)
            color = info.get("color", [128, 128, 128])
            cvs = tk.Canvas(row, width=20, height=20, highlightthickness=0)
            cvs.pack(side=tk.LEFT, padx=5)
            cvs.create_oval(2, 2, 18, 18, fill=rgb_to_hex(*color), outline="")
            if info.get("type") == "分配制":
                total_hours = sum(item.get("hours", 0) for item in info.get("items", []))
                info_text = f"{name} | {info.get('type')} | 总时长：{total_hours:.1f}h"
            else:
                info_text = f"{name} | {info.get('type')} | 背景：{info.get('bg_tag', '无')}"
            ttk.Label(row, text=info_text, width=45).pack(side=tk.LEFT, padx=5)
            ttk.Button(row, text="查看/编辑", command=lambda n=name: self.show_edit_plan(n)).pack(side=tk.LEFT, padx=2)
            ttk.Button(row, text="重命名", command=lambda n=name: self.rename_plan(n)).pack(side=tk.LEFT, padx=2)
            ttk.Button(row, text="删除", command=lambda n=name: self.delete_plan(n)).pack(side=tk.LEFT, padx=2)
        bf = ttk.Frame(f)
        bf.pack(fill=tk.X, pady=10)
        ttk.Button(bf, text="创建日计划", command=self.show_create_plan).pack(side=tk.LEFT, padx=5)
        ttk.Button(bf, text="返回", command=self.show_management).pack(side=tk.RIGHT, padx=5)

    def _open_plan_editor(self, is_edit=False):
        self.clear()
        f = ttk.Frame(self.root, padding=25)
        f.pack(fill=tk.BOTH, expand=True)
        title = "编辑日计划" if is_edit else "创建日计划"
        ttk.Label(f, text=title, font=("微软雅黑", 16)).pack(pady=10)
        name_frm = ttk.Frame(f)
        name_frm.pack(fill=tk.X, pady=5)
        ttk.Label(name_frm, text="计划名称：").pack(side=tk.LEFT)
        self.plan_name_var = ttk.Entry(name_frm)
        self.plan_name_var.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.plan_type = tk.StringVar(value="切分制")
        type_frm = ttk.Frame(f)
        type_frm.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(type_frm, text="切分制", variable=self.plan_type, value="切分制", command=self._refresh_item_frame).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frm, text="分配制", variable=self.plan_type, value="分配制", command=self._refresh_item_frame).pack(side=tk.LEFT, padx=5)
        color_frm = ttk.LabelFrame(f, text="计划颜色标签")
        color_frm.pack(fill=tk.X, pady=5)
        self.color_preview = tk.Canvas(color_frm, width=40, height=20, bg=rgb_to_hex(*self.current_plan_color))
        self.color_preview.pack(side=tk.LEFT, padx=5)
        ttk.Button(color_frm, text="选择颜色", command=self.choose_color).pack(side=tk.LEFT, padx=5)
        ttk.Label(color_frm, text="RGB:").pack(side=tk.LEFT)
        self.r_entry = ttk.Entry(color_frm, width=5)
        self.g_entry = ttk.Entry(color_frm, width=5)
        self.b_entry = ttk.Entry(color_frm, width=5)
        self.r_entry.pack(side=tk.LEFT, padx=2)
        self.g_entry.pack(side=tk.LEFT, padx=2)
        self.b_entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(color_frm, text="应用RGB", command=self.apply_rgb).pack(side=tk.LEFT, padx=5)
        self.canvas = tk.Canvas(f, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(f, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(fill=tk.BOTH, expand=True, pady=10)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10, before=self.canvas)
        self.item_rows = []
        self.bg_var = tk.StringVar(value="")
        if is_edit and self.edit_plan_name in self.plans:
            data = self.plans[self.edit_plan_name]
            self.plan_name_var.insert(0, self.edit_plan_name)
            self.plan_type.set(data.get("type", "切分制"))
            self.bg_var.set(data.get("bg_tag", ""))
            self.current_plan_color = data.get("color", [128, 128, 128])
            self.update_color_preview()
            for it in data.get("items", []):
                self._add_item_row(it.get("name", ""), it.get("hours", 0))
        else:
            self.current_plan_color = [128, 128, 128]
            self.update_color_preview()
            self._add_item_row()
            if self.plan_type.get() == "切分制":
                self._add_item_row()
        bottom_btn_frm = ttk.Frame(f)
        bottom_btn_frm.pack(fill=tk.X, pady=10, side=tk.BOTTOM)
        ttk.Button(bottom_btn_frm, text="+ 添加时间类别", command=self._add_item_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_btn_frm, text="保存", command=self._save_plan).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_btn_frm, text="返回", command=self.show_plan_management).pack(side=tk.RIGHT, padx=5)

    def _add_item_row(self, name="", hours=0):
        t = self.plan_type.get()
        min_cnt = 2 if t == "切分制" else 1
        row = ttk.Frame(self.scrollable_frame)
        row.pack(fill=tk.X, pady=2, padx=5)
        self.item_rows.append(row)
        ttk.Label(row, text="时间类别：").pack(side=tk.LEFT, padx=2)
        name_ent = ttk.Entry(row, width=12)
        name_ent.insert(0, name)
        name_ent.pack(side=tk.LEFT, padx=2)
        ttk.Label(row, text="计划时长(h)：").pack(side=tk.LEFT, padx=2)
        hour_ent = ttk.Entry(row, width=6)
        hour_ent.insert(0, hours)
        hour_ent.pack(side=tk.LEFT, padx=2)
        if t == "切分制":
            bg_btn = ttk.Radiobutton(row, text="背景类别", variable=self.bg_var, value=name)
            bg_btn.pack(side=tk.LEFT, padx=5)
            def upd_name(e=None): bg_btn.config(value=name_ent.get())
            name_ent.bind("<KeyRelease>", upd_name)
        del_btn = ttk.Button(row, text="删除", width=5)
        del_btn.pack(side=tk.RIGHT, padx=2)
        def delete_row():
            if len(self.item_rows) > min_cnt:
                row.destroy()
                self.item_rows.remove(row)
        del_btn.config(command=delete_row)
        if len(self.item_rows) <= min_cnt:
            del_btn.config(state=tk.DISABLED)

    def choose_color(self):
        color = colorchooser.askcolor(title="选择颜色")[0]
        if color:
            self.current_plan_color = [int(c) for c in color]
            self.update_color_preview()

    def apply_rgb(self):
        try:
            r = int(self.r_entry.get())
            g = int(self.g_entry.get())
            b = int(self.b_entry.get())
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                self.current_plan_color = [r, g, b]
                self.update_color_preview()
            else:
                messagebox.showerror("错误", "RGB值必须在0-255之间")
        except:
            messagebox.showerror("错误", "请输入有效数字")

    def update_color_preview(self):
        hex_color = rgb_to_hex(*self.current_plan_color)
        self.color_preview.config(bg=hex_color)
        self.r_entry.delete(0, tk.END)
        self.g_entry.delete(0, tk.END)
        self.b_entry.delete(0, tk.END)
        self.r_entry.insert(0, str(self.current_plan_color[0]))
        self.g_entry.insert(0, str(self.current_plan_color[1]))
        self.b_entry.insert(0, str(self.current_plan_color[2]))

    def _refresh_item_frame(self):
        for row in self.item_rows: row.destroy()
        self.item_rows.clear()
        t = self.plan_type.get()
        self._add_item_row()
        if t == "切分制":
            self._add_item_row()

    def show_create_plan(self):
        self._open_plan_editor()

    def show_edit_plan(self, name):
        self.edit_plan_name = name
        self._open_plan_editor(is_edit=True)

    def _save_plan(self):
        name = self.plan_name_var.get().strip()
        if not name:
            return messagebox.showwarning("提示", "请输入计划名称")
        t = self.plan_type.get()
        items = []
        item_names = []
        total = 0.0
        for row in self.item_rows:
            ws = [w for w in row.winfo_children() if isinstance(w, ttk.Entry)]
            if len(ws) < 2: continue
            n = ws[0].get().strip()
            try:
                h = float(ws[1].get())
            except:
                h = 0.0
            if not n:
                return messagebox.showwarning("提示", "类别名称不能为空")
            if h < 0:
                return messagebox.showwarning("提示", "时长不能为负数")
            if t == "分配制" and h > 24:
                return messagebox.showerror("错误", f"类别【{n}】时长超过24小时，禁止保存！")
            items.append({"name": n, "hours": h})
            item_names.append(n)
            total += h
        if t == "切分制":
            bg_tag = self.bg_var.get().strip()
            if not bg_tag:
                messagebox.showerror("错误", "切分制日计划必须选择【背景类别】！")
                return
            if bg_tag not in item_names:
                messagebox.showerror("错误", f"背景类别“{bg_tag}”不在当前类别列表中，请重新选择！")
                return
            if total == 0:
                items = auto_balance(items, 24)
                total = 24
            if not abs(total - 24) < 0.01:
                res = messagebox.askyesnocancel("提示", f"总和{total:.1f}h≠24h\n是否自动平衡？")
                if res is None: return
                if res:
                    items = auto_balance(items, 24)
                else:
                    return
        else:
            bg_tag = ""
        self.plans[name] = {
            "type": t,
            "items": items,
            "bg_tag": bg_tag,
            "color": self.current_plan_color
        }
        DataCore.save_plans(self.plans)
        messagebox.showinfo("成功", "保存成功")
        self.show_plan_management()

    def rename_plan(self, old):
        new = sd.askstring("重命名", "输入新名称：", initialvalue=old)
        if not new or new.strip() == old:
            return
        if new in self.plans:
            return messagebox.showwarning("提示", "名称已存在")
        self.plans[new.strip()] = self.plans.pop(old)
        DataCore.save_plans(self.plans)
        self.show_plan_management()

    def delete_plan(self, name):
        if not messagebox.askyesno("确认", f"确定删除【{name}】？"):
            return
        del self.plans[name]
        DataCore.save_plans(self.plans)
        self.show_plan_management()

    # ========== 记录管理相关 ==========
    def check_record_overlap(self, new_start, new_end, new_tag, day):
        records = DataCore.load_records(day)
        day_plan = DataCore.load_day_plan(day)
        plan_type = day_plan.get("type")
        conflicts = []
        for r in records:
            if plan_type == "切分制":
                if is_time_overlap(new_start, new_end, r.get("开始"), r.get("结束")):
                    conflicts.append(f"{r.get('标签')} {r.get('开始')}-{r.get('结束')}")
            else:
                if r.get("标签") == new_tag and is_time_overlap(new_start, new_end, r.get("开始"), r.get("结束")):
                    conflicts.append(f"{r.get('标签')} {r.get('开始')}-{r.get('结束')}")
        if conflicts:
            messagebox.showerror("冲突", "\n".join(conflicts))
            return True
        return False

    def show_detail(self, day=None):
        self.clear()
        self.current_view_day = day
        f = ttk.Frame(self.root, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        title = f"{day} 记录管理" if day else "今日记录管理"
        ttk.Label(f, text=title, font=("微软雅黑", 16)).pack(pady=10)
        ttk.Button(f, text="➕ 新增记录", command=lambda: self.show_add(day=day)).pack(pady=5)
        self.list_frame = ttk.Frame(f)
        self.list_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Button(f, text="返回", command=self.show_home if not day else lambda: self.show_day_preview(day)).pack(pady=10)
        self.force_refresh_detail()
        self.update_detail_smart()

    def force_refresh_detail(self):
        now = datetime.now()
        self.last_refresh_minute = now.hour * 60 + now.minute
        for w in self.list_frame.winfo_children(): w.destroy()
        day_plan = DataCore.load_day_plan(self.current_view_day)
        records = DataCore.load_records(self.current_view_day)
        records = sort_records(records, day_plan.get("type")) if day_plan.get("name") in self.plans else records
        for i, r in enumerate(records):
            rf = ttk.Frame(self.list_frame)
            rf.pack(fill=tk.X, pady=2)
            dur = (time_str_to_minutes(r.get("结束")) - time_str_to_minutes(r.get("开始"))) / 60
            txt = f"[{r.get('标签')}] {r.get('开始')}-{r.get('结束')} | {hours_to_hm(dur)} | {r.get('内容')}"
            ttk.Label(rf, text=txt, width=70).pack(side=tk.LEFT)
            ttk.Button(rf, text="修改", command=lambda idx=i, d=self.current_view_day: self.show_edit(idx, d)).pack(side=tk.LEFT, padx=2)
            ttk.Button(rf, text="删除", command=lambda idx=i, d=self.current_view_day: self.confirm_delete(idx, d)).pack(side=tk.LEFT, padx=2)

    def update_detail_smart(self):
        if not self.list_frame.winfo_exists(): return
        now = datetime.now()
        current_minute = now.hour * 60 + now.minute
        if current_minute != self.last_refresh_minute:
            self.force_refresh_detail()
        self.after_id = self.root.after(1000, self.update_detail_smart)

    def confirm_delete(self, i, d):
        if messagebox.askyesno("确认", "确定删除？"):
            DataCore.delete_record(i, d)
            self.show_detail(d)

    def show_edit(self, i, d):
        self.edit_idx = i
        self.edit_day = d
        self.show_add(DataCore.load_records(d)[i], d)

    def show_add(self, edit=None, day=None):
        self.clear()
        f = ttk.Frame(self.root, padding=25)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="编辑记录" if edit else "新增记录", font=("微软雅黑", 16)).pack(pady=10)
        self.mode = tk.StringVar(value="1")
        mf = ttk.Frame(f)
        mf.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(mf, text="开始+结束", variable=self.mode, value="1", command=self.switch).pack(side=tk.LEFT)
        ttk.Radiobutton(mf, text="时长+单点", variable=self.mode, value="2", command=self.switch).pack(side=tk.LEFT)
        self.m1 = ttk.Frame(f)
        self.m1.pack(fill=tk.X, pady=5)
        ttk.Label(self.m1, text="开始：").pack(side=tk.LEFT)
        self.h1 = ttk.Entry(self.m1, width=5)
        self.h1.pack(side=tk.LEFT, padx=2)
        ttk.Label(self.m1, text=":").pack(side=tk.LEFT)
        self.m1_ = ttk.Entry(self.m1, width=5)
        self.m1_.pack(side=tk.LEFT, padx=2)
        ttk.Label(self.m1, text="结束：").pack(side=tk.LEFT)
        self.h2 = ttk.Entry(self.m1, width=5)
        self.h2.pack(side=tk.LEFT, padx=2)
        ttk.Label(self.m1, text=":").pack(side=tk.LEFT)
        self.m2_ = ttk.Entry(self.m1, width=5)
        self.m2_.pack(side=tk.LEFT, padx=2)
        self.m2 = ttk.Frame(f)
        self.dh = tk.StringVar()
        self.dm = tk.StringVar()
        self.opt = tk.StringVar(value="start")
        ttk.Label(self.m2, text="时长：").pack(side=tk.LEFT)
        ttk.Entry(self.m2, textvariable=self.dh, width=3).pack(side=tk.LEFT)
        ttk.Entry(self.m2, textvariable=self.dm, width=3).pack(side=tk.LEFT)
        ttk.Label(self.m2, text="时").pack(side=tk.LEFT)
        ttk.Label(self.m2, text="分").pack(side=tk.LEFT)
        ttk.Radiobutton(self.m2, text="开始", variable=self.opt, value="start").pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(self.m2, text="结束", variable=self.opt, value="end").pack(side=tk.LEFT, padx=3)
        self.mh = ttk.Entry(self.m2, width=5)
        self.mm = ttk.Entry(self.m2, width=5)
        ttk.Label(self.m2, text="时间：").pack(side=tk.LEFT)
        self.mh.pack(side=tk.LEFT, padx=2)
        ttk.Label(self.m2, text=":").pack(side=tk.LEFT)
        self.mm.pack(side=tk.LEFT, padx=2)
        self.m2.pack_forget()
        ttk.Label(f, text="内容：").pack(fill=tk.X, pady=2)
        self.content = ttk.Entry(f)
        self.content.pack(fill=tk.X, pady=5)
        self.tag = tk.StringVar(value="工作")
        day_plan = DataCore.load_day_plan(day)
        plan = self.plans.get(day_plan.get("name"), {})
        tags = [it.get("name") for it in plan.get("items", [])]
        ttk.Combobox(f, textvariable=self.tag, values=tags, state="readonly").pack(fill=tk.X, pady=5)
        if edit:
            s, e = edit.get("开始", "00:00").split(':'), edit.get("结束", "00:00").split(':')
            self.h1.insert(0, s[0]), self.m1_.insert(0, s[1])
            self.h2.insert(0, e[0]), self.m2_.insert(0, e[1])
            self.content.insert(0, edit.get("内容", ""))
            self.tag.set(edit.get("标签", ""))
        bf = ttk.Frame(f)
        bf.pack(pady=15)
        ttk.Button(bf, text="保存", command=lambda: self.save_record(edit, day)).pack(side=tk.LEFT, padx=5)
        cmd = self.show_home if not day else lambda: self.show_detail(day)
        ttk.Button(bf, text="返回", command=cmd).pack(side=tk.LEFT, padx=5)

    def switch(self):
        if self.mode.get() == "1":
            self.m2.pack_forget(); self.m1.pack(fill=tk.X, pady=5)
        else:
            self.m1.pack_forget(); self.m2.pack(fill=tk.X, pady=5)

    def save_record(self, edit, day):
        try:
            if self.mode.get() == "1":
                sh, sm = int(self.h1.get()), int(self.m1_.get())
                eh, em = int(self.h2.get()), int(self.m2_.get())
                s_str = f"{sh:02d}:{sm:02d}"
                e_str = f"{eh:02d}:{em:02d}"
            else:
                dh, dm = int(self.dh.get() or 0), int(self.dm.get() or 0)
                dur = hm_to_hours(dh, dm)
                th, tm = int(self.mh.get()), int(self.mm.get())
                if self.opt.get() == "start":
                    eh, em = DataCore.time_from_start(th, tm, dur)
                    s_str = f"{th:02d}:{tm:02d}"
                    e_str = f"{eh:02d}:{em:02d}"
                else:
                    sh, sm = DataCore.time_to_end(th, tm, dur)
                    s_str = f"{sh:02d}:{sm:02d}"
                    e_str = f"{th:02d}:{tm:02d}"
            if not self.content.get():
                return messagebox.showwarning("提示", "请填写内容")
            if not edit and self.check_record_overlap(s_str, e_str, self.tag.get(), day):
                return
            dur = hm_to_hours(*map(int, e_str.split(':'))) - hm_to_hours(*map(int, s_str.split(':')))
            r = {"日期": day or DataCore.get_today_date(), "开始": s_str, "结束": e_str, "时长": dur, "内容": self.content.get(), "标签": self.tag.get()}
            if edit:
                DataCore.update_record(self.edit_idx, r, self.edit_day)
            else:
                DataCore.save_record(r, day)
            self.show_home()
        except:
            messagebox.showerror("错误", "时间格式错误")

    def show_day_preview(self, day):
        self.clear()
        f = ttk.Frame(self.root, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text=f"{day} 详情", font=("微软雅黑", 16, "bold")).pack(pady=10)
        try:
            result = DataCore.calc_real_time_stat(day)
            stat, prog, bg_tag, target, plan_exists, plan_name, plan_type, total_used, has_records, _ = result
        except:
            plan_exists = False
            total_used = 0
            stat = {}
            prog = 0
        if plan_exists:
            ttk.Label(f, text=f"📋 当日计划：{plan_name}（{plan_type}）", font=("微软雅黑", 12, "bold")).pack(anchor=tk.W, pady=2)
            c = "black" if prog == 0 else ("red" if prog < 40 else "orange" if prog < 70 else "gold" if prog < 90 else "green")
            ttk.Label(f, text=f"📊 总完成度：{prog}%", font=("微软雅黑", 12, "bold"), foreground=c).pack(anchor=tk.W, pady=5)
        else:
            ttk.Label(f, text="📋 日计划不存在", font=("微软雅黑", 12, "bold"), foreground="purple").pack(anchor=tk.W, pady=2)
            ttk.Label(f, text=f"⏱ 总记录时长：{hours_to_hm(total_used)}", font=("微软雅黑", 12, "bold")).pack(anchor=tk.W, pady=5)
        ttk.Separator(f, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        if plan_exists:
            for tag, t in target.items():
                act = stat.get(tag, 0.0)
                prefix = "🟢【背景类别】" if tag == bg_tag else "🔹 "
                txt = f"{prefix}{tag}：{hours_to_hm(act)} / {hours_to_hm(t)}"
                ttk.Label(f, text=txt).pack(anchor=tk.W, pady=2)
        else:
            ttk.Label(f, text="无有效计划，仅展示分类总时长", foreground="gray").pack(anchor=tk.W, pady=5)
            for tag, act in stat.items():
                ttk.Label(f, text=f"🔹 {tag}：{hours_to_hm(act)}").pack(anchor=tk.W, pady=2)
        btn_f = ttk.Frame(f)
        btn_f.pack(pady=15)
        ttk.Button(btn_f, text="计划管理", command=lambda: self.change_day_plan(day)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_f, text="记录管理", command=lambda: self.show_detail(day)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_f, text="返回日历", command=self.show_calendar).pack(side=tk.LEFT, padx=5)

    def change_day_plan(self, day):
        plans = DataCore.load_plans()
        plan_list = [name for name in plans.keys() if name]
        if not plan_list:
            messagebox.showwarning("提示", "暂无可用日计划")
            return
        current = DataCore.load_day_plan(day)
        choice = choose_tag_dialog(self.root, "单日计划变更", f"当前{day}计划：{current['name']}\n请选择新计划", plan_list)
        if choice:
            DataCore.save_day_plan(choice, day)
            messagebox.showinfo("成功", f"{day}计划已变更为：{choice}")
            self.show_day_preview(day)

    # ========== 日历（完整排版） ==========
    def show_calendar(self):
        self.clear()
        f = ttk.Frame(self.root, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        # 顶部导航栏
        nav_frame = ttk.Frame(f)
        nav_frame.pack(fill=tk.X, pady=5)
        self.year_prev_btn = ttk.Button(nav_frame, text="◀◀", command=self.year_prev)
        self.month_prev_btn = ttk.Button(nav_frame, text="◀", command=self.last)
        self.ct = ttk.Label(nav_frame, text=f"{self.calendar_year}年{self.calendar_month}月", font=("微软雅黑", 16))
        self.tb = ttk.Button(nav_frame, text="返回今天", command=self.today)
        self.month_next_btn = ttk.Button(nav_frame, text="▶", command=self.next)
        self.year_next_btn = ttk.Button(nav_frame, text="▶▶", command=self.year_next)
        # 初始排列
        self.year_prev_btn.pack(side=tk.LEFT, padx=2)
        self.month_prev_btn.pack(side=tk.LEFT, padx=2)
        self.ct.pack(side=tk.LEFT, expand=True)
        self.tb.pack(side=tk.LEFT, padx=5)
        self.month_next_btn.pack(side=tk.LEFT, padx=2)
        self.year_next_btn.pack(side=tk.LEFT, padx=2)
        self.ctm()
        self.update_calendar_nav_buttons()
        wd = ["一", "二", "三", "四", "五", "六", "日"]
        wf = ttk.Frame(f)
        wf.pack(fill=tk.X)
        for i in range(7):
            wf.columnconfigure(i, weight=1)
            ttk.Label(wf, text=wd[i], relief="solid", anchor=tk.CENTER).grid(row=0, column=i, sticky=tk.NSEW, padx=1, pady=1)
        self.cg = tk.Frame(f)
        self.cg.pack(fill=tk.BOTH, expand=True, pady=10)
        self.rcal()
        bottom_frame = ttk.Frame(f)
        bottom_frame.pack(fill=tk.X, pady=5)
        self.quick_turn_var = tk.BooleanVar(value=self.quick_turn.get())
        quick_cb = ttk.Checkbutton(bottom_frame, text="快速翻页", variable=self.quick_turn_var, command=self.toggle_quick_buttons)
        quick_cb.pack(side=tk.LEFT)
        ttk.Button(bottom_frame, text="返回主页", command=self.show_home).pack(side=tk.RIGHT, padx=5)

    def update_calendar_nav_buttons(self):
        if self.quick_turn.get():
            self.year_prev_btn.pack(side=tk.LEFT, padx=2)
            self.year_next_btn.pack(side=tk.LEFT, padx=2)
        else:
            self.year_prev_btn.pack_forget()
            self.year_next_btn.pack_forget()
        self.month_prev_btn.pack(side=tk.LEFT, padx=2)
        self.ct.pack(side=tk.LEFT, expand=True)
        self.tb.pack(side=tk.LEFT, padx=5)
        self.month_next_btn.pack(side=tk.LEFT, padx=2)
        if self.quick_turn.get():
            self.year_prev_btn.pack(side=tk.LEFT, padx=2)
            self.year_next_btn.pack(side=tk.LEFT, padx=2)

    def toggle_quick_buttons(self):
        self.quick_turn.set(self.quick_turn_var.get())
        self.update_calendar_nav_buttons()

    def year_prev(self):
        self.calendar_year -= 1
        self.ct.config(text=f"{self.calendar_year}年{self.calendar_month}月")
        self.ctm()
        self.rcal()

    def year_next(self):
        self.calendar_year += 1
        self.ct.config(text=f"{self.calendar_year}年{self.calendar_month}月")
        self.ctm()
        self.rcal()

    def ctm(self):
        ty, tm = date.today().year, date.today().month
        if self.calendar_year == ty and self.calendar_month == tm:
            self.tb.pack_forget()
        else:
            self.tb.pack(side=tk.LEFT, padx=5)

    def today(self):
        self.calendar_year = date.today().year
        self.calendar_month = date.today().month
        self.ct.config(text=f"{self.calendar_year}年{self.calendar_month}月")
        self.ctm()
        self.rcal()

    def rcal(self):
        for w in self.cg.winfo_children(): w.destroy()
        for i in range(6): self.cg.rowconfigure(i, weight=1)
        for i in range(7): self.cg.columnconfigure(i, weight=1)
        cal = calendar.monthcalendar(self.calendar_year, self.calendar_month)
        ts = DataCore.get_today_date()
        for ri, wk in enumerate(cal):
            for ci, d in enumerate(wk):
                if d == 0:
                    tk.Label(self.cg, text="", relief="solid", anchor=tk.CENTER).grid(row=ri, column=ci, sticky=tk.NSEW, padx=1, pady=1)
                    continue
                ds = f"{self.calendar_year}-{self.calendar_month:02d}-{d:02d}"
                try:
                    _, prog, _, _, plan_exists, plan_name, _, _, has_records, _ = DataCore.calc_real_time_stat(ds)
                except:
                    prog = 0
                    plan_exists = False
                    has_records = False
                    plan_name = None
                plan = self.plans.get(plan_name, None) if plan_name else None
                base_color = plan.get("color", [128, 128, 128]) if plan else [128, 128, 128]
                mix_color = self.mix_color_with_white(*base_color)
                it = tk.Frame(self.cg, relief="solid", borderwidth=1, bg=mix_color, cursor="hand2")
                if ds == ts: it.config(highlightbackground="green", highlightthickness=3)
                it.grid(row=ri, column=ci, sticky=tk.NSEW, padx=1, pady=1)
                day_lbl = tk.Label(it, text=f"{d}日", anchor=tk.CENTER, bg=mix_color)
                day_lbl.pack(pady=1)
                day_lbl.bind("<Button-1>", lambda e, s=ds: self.show_day_preview(s))
                if not has_records:
                    prog_lbl = tk.Label(it, text="--", anchor=tk.CENTER, foreground="black", bg=mix_color, font=("微软雅黑", 10, "bold"))
                    prog_lbl.pack()
                    prog_lbl.bind("<Button-1>", lambda e, s=ds: self.show_day_preview(s))
                elif not plan_exists:
                    prog_lbl = tk.Label(it, text="PD", anchor=tk.CENTER, foreground="purple", bg=mix_color, font=("微软雅黑", 10, "bold"))
                    prog_lbl.pack()
                    prog_lbl.bind("<Button-1>", lambda e, s=ds: self.show_day_preview(s))
                else:
                    c = "black" if prog == 0 else ("red" if prog < 40 else "orange" if prog < 70 else "gold" if prog < 90 else "green")
                    prog_lbl = tk.Label(it, text=f"{prog}%", anchor=tk.CENTER, foreground=c, bg=mix_color)
                    prog_lbl.pack()
                    prog_lbl.bind("<Button-1>", lambda e, s=ds: self.show_day_preview(s))
                it.bind("<Button-1>", lambda e, s=ds: self.show_day_preview(s))

    def last(self):
        if self.calendar_month == 1:
            self.calendar_year -= 1; self.calendar_month = 12
        else:
            self.calendar_month -= 1
        self.ct.config(text=f"{self.calendar_year}年{self.calendar_month}月")
        self.ctm()
        self.rcal()

    def next(self):
        if self.calendar_month == 12:
            self.calendar_year += 1; self.calendar_month = 1
        else:
            self.calendar_month += 1
        self.ct.config(text=f"{self.calendar_year}年{self.calendar_month}月")
        self.ctm()
        self.rcal()

    # ========== 设置中心 ==========
    def show_setting(self):
        self.clear()
        f = ttk.Frame(self.root, padding=30)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="设置中心", font=("微软雅黑", 16)).pack(pady=10)
        ttk.Button(f, text="自定义", command=self.show_custom_settings, width=20).pack(pady=5)
        ttk.Button(f, text="外观", command=self.show_appearance, width=20).pack(pady=5)
        ttk.Button(f, text="帮助", command=self.show_help, width=20).pack(pady=5)
        ttk.Button(f, text="存档管理", command=self.show_archive_management, width=20).pack(pady=5)
        ttk.Button(f, text="恢复", command=self.reset, width=20).pack(pady=5)
        ttk.Button(f, text="返回", command=self.show_home, width=20).pack(pady=20)
        ad_frame = ttk.Frame(f)
        ad_frame.pack(side=tk.BOTTOM, pady=10)
        ttk.Label(ad_frame, text="开发者：浪兮spinner_bot", font=("微软雅黑", 9), foreground="gray").pack()
        ttk.Label(ad_frame, text="抖音@浪兮有点浪", font=("微软雅黑", 9), foreground="gray").pack()

    def show_custom_settings(self):
        self.clear()
        f = ttk.Frame(self.root, padding=30)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="自定义设置", font=("微软雅黑", 16)).pack(pady=10)
        thresh_frame = ttk.LabelFrame(f, text="标签超限阈值")
        thresh_frame.pack(fill=tk.X, pady=5)
        self.tl = ttk.Label(thresh_frame, text=f"当前阈值：{self.overtime_threshold}%", font=("微软雅黑", 12))
        self.tl.pack(pady=5)
        btn_frame = ttk.Frame(thresh_frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="-", command=self.sub, width=3).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="+", command=self.add, width=3).pack(side=tk.LEFT, padx=5)
        time_frame = ttk.LabelFrame(f, text="时间显示")
        time_frame.pack(fill=tk.X, pady=5)
        self.show_sec_var = tk.BooleanVar(value=self.show_seconds)
        ttk.Checkbutton(time_frame, text="显示秒", variable=self.show_sec_var, command=self.save_time_settings).pack(anchor=tk.W)
        self.use_24h_var = tk.BooleanVar(value=self.use_24h)
        ttk.Checkbutton(time_frame, text="24小时制", variable=self.use_24h_var, command=self.save_time_settings).pack(anchor=tk.W)
        self.show_ampm_var = tk.BooleanVar(value=self.show_ampm)
        ttk.Checkbutton(time_frame, text="半日显示(AM/PM)", variable=self.show_ampm_var, command=self.save_time_settings).pack(anchor=tk.W)
        ttk.Button(f, text="返回", command=self.show_setting).pack(pady=20)

    def show_appearance(self):
        self.clear()
        f = ttk.Frame(self.root, padding=30)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="外观设置", font=("微软雅黑", 16)).pack(pady=10)
        coeff_frame = ttk.LabelFrame(f, text="日历背景色")
        coeff_frame.pack(fill=tk.X, pady=5)
        ttk.Label(coeff_frame, text="白化系数：", font=("微软雅黑", 12)).pack(side=tk.LEFT, padx=5)
        self.k_var = tk.DoubleVar(value=self.whiten_k)
        scale = ttk.Scale(coeff_frame, from_=0.0, to=1.0, variable=self.k_var, orient=tk.HORIZONTAL, length=200, command=self.on_whiten_scale)
        scale.pack(side=tk.LEFT, padx=10)
        self.k_label = ttk.Label(coeff_frame, text=f"{self.whiten_k:.2f}", width=6)
        self.k_label.pack(side=tk.LEFT, padx=5)
        style_frame = ttk.LabelFrame(f, text="界面样式")
        style_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(style_frame, text="窗口背景色:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.bg_window_var = tk.StringVar(value=self.theme.get("bg_window", "#f0f0f0"))
        ttk.Entry(style_frame, textvariable=self.bg_window_var, width=10).grid(row=0, column=1, padx=5)
        ttk.Button(style_frame, text="选择", command=lambda: self.pick_color("bg_window")).grid(row=0, column=2)
        ttk.Label(style_frame, text="按钮背景色:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.bg_button_var = tk.StringVar(value=self.theme.get("bg_button", "#e0e0e0"))
        ttk.Entry(style_frame, textvariable=self.bg_button_var, width=10).grid(row=1, column=1, padx=5)
        ttk.Button(style_frame, text="选择", command=lambda: self.pick_color("bg_button")).grid(row=1, column=2)
        ttk.Label(style_frame, text="按钮文字色:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        self.fg_button_var = tk.StringVar(value=self.theme.get("fg_button", "#000000"))
        ttk.Entry(style_frame, textvariable=self.fg_button_var, width=10).grid(row=2, column=1, padx=5)
        ttk.Button(style_frame, text="选择", command=lambda: self.pick_color("fg_button")).grid(row=2, column=2)
        preset_frame = ttk.Frame(style_frame)
        preset_frame.grid(row=3, column=0, columnspan=3, pady=5)
        ttk.Label(preset_frame, text="预设方案:").pack(side=tk.LEFT)
        def apply_preset(preset):
            if preset == "默认":
                self.bg_window_var.set("#f0f0f0")
                self.bg_button_var.set("#e0e0e0")
                self.fg_button_var.set("#000000")
            elif preset == "深色":
                self.bg_window_var.set("#2d2d2d")
                self.bg_button_var.set("#3c3c3c")
                self.fg_button_var.set("#ffffff")
            elif preset == "浅色":
                self.bg_window_var.set("#ffffff")
                self.bg_button_var.set("#f0f0f0")
                self.fg_button_var.set("#000000")
            self.save_theme()
        ttk.Button(preset_frame, text="默认", command=lambda: apply_preset("默认")).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="深色", command=lambda: apply_preset("深色")).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="浅色", command=lambda: apply_preset("浅色")).pack(side=tk.LEFT, padx=2)
        ttk.Button(style_frame, text="应用样式", command=self.save_theme).grid(row=4, column=0, columnspan=3, pady=5)
        ttk.Button(f, text="返回", command=self.show_setting).pack(pady=20)

    def pick_color(self, key):
        color = colorchooser.askcolor(title="选择颜色")[0]
        if color:
            hex_color = rgb_to_hex(int(color[0]), int(color[1]), int(color[2]))
            if key == "bg_window":
                self.bg_window_var.set(hex_color)
            elif key == "bg_button":
                self.bg_button_var.set(hex_color)
            elif key == "fg_button":
                self.fg_button_var.set(hex_color)

    def save_theme(self):
        self.theme = {
            "bg_window": self.bg_window_var.get(),
            "bg_button": self.bg_button_var.get(),
            "fg_button": self.fg_button_var.get(),
            "bg_frame": "#d9d9d9"
        }
        self.config["theme"] = self.theme
        DataCore.save_config(self.config)
        self.apply_theme()
        messagebox.showinfo("成功", "样式已应用")

    def on_whiten_scale(self, event=None):
        new_val = self.k_var.get()
        self.k_label.config(text=f"{new_val:.2f}")
        self.whiten_k = new_val
        self.config["whiten_k"] = self.whiten_k
        DataCore.save_config(self.config)
        if hasattr(self, 'cg') and self.cg.winfo_exists():
            self.rcal()

    def save_time_settings(self):
        self.show_seconds = self.show_sec_var.get()
        self.use_24h = self.use_24h_var.get()
        self.show_ampm = self.show_ampm_var.get()
        self.config["show_seconds"] = self.show_seconds
        self.config["use_24h"] = self.use_24h
        self.config["show_ampm"] = self.show_ampm
        DataCore.save_config(self.config)

    def add(self):
        if self.overtime_threshold < 150:
            self.overtime_threshold += 1
            self.save_th()

    def sub(self):
        if self.overtime_threshold > 100:
            self.overtime_threshold -= 1
            self.save_th()

    def save_th(self):
        self.config["overtime_threshold"] = self.overtime_threshold
        DataCore.save_config(self.config)
        self.tl.config(text=f"当前阈值：{self.overtime_threshold}%")

    def reset(self):
        self.clear()
        f = ttk.Frame(self.root, padding=30)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="恢复设置", font=("微软雅黑", 16)).pack(pady=10)
        ttk.Button(f, text="重置计划数据", command=self.reset_plan_data, width=20).pack(pady=5)
        ttk.Button(f, text="重置日程数据", command=self.reset_schedule_data, width=20).pack(pady=5)
        ttk.Button(f, text="重置设置数据", command=self.do_reset, width=20).pack(pady=5)
        ttk.Button(f, text="返回", command=self.show_setting).pack(pady=20)

    def reset_plan_data(self):
        if not messagebox.askyesno("确认", "确定重置所有日计划为默认？此操作不可恢复！"):
            return
        if os.path.exists(PLAN_PATH):
            os.remove(PLAN_PATH)
        self.plans = DataCore.load_plans()
        messagebox.showinfo("成功", "日计划数据已重置为默认！")

    def reset_schedule_data(self):
        if not messagebox.askyesno("确认", "确定重置日程规则为默认？此操作不可恢复！"):
            return
        if os.path.exists(SCHEDULE_RULES_PATH):
            os.remove(SCHEDULE_RULES_PATH)
        if os.path.exists(MANUAL_PLANS_PATH):
            os.remove(MANUAL_PLANS_PATH)
        messagebox.showinfo("成功", "日程数据已重置为默认！")

    def do_reset(self):
        if not messagebox.askyesno("确认", "确定重置所有设置为默认？\n（不会影响日计划、日程规则和手动修改）"):
            return
        default_config = {"overtime_threshold": 105, "whiten_k": 0.6, "show_seconds": True, "use_24h": True, "show_ampm": False, "theme": DEFAULT_THEME}
        DataCore.save_config(default_config)
        self.config = default_config
        self.overtime_threshold = default_config["overtime_threshold"]
        self.whiten_k = default_config["whiten_k"]
        self.show_seconds = default_config["show_seconds"]
        self.use_24h = default_config["use_24h"]
        self.show_ampm = default_config["show_ampm"]
        self.theme = default_config["theme"]
        self.apply_theme()
        messagebox.showinfo("成功", "设置数据已重置为默认！")

    # ========== 帮助中心 ==========
    def show_help(self):
        self.clear()
        f = ttk.Frame(self.root, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="帮助中心", font=("微软雅黑", 16, "bold")).pack(pady=10)
        top_frame = ttk.Frame(f)
        top_frame.pack(fill=tk.X, pady=5)
        ttk.Button(top_frame, text="联系开发者", command=self.contact_developer).pack(side=tk.RIGHT, padx=5)
        paned = ttk.PanedWindow(f, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=10)
        left_frame = ttk.Frame(paned, width=280)
        paned.add(left_frame, weight=1)
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)
        tree = ttk.Treeview(left_frame, show="tree", height=20)
        tree.pack(fill=tk.BOTH, expand=True)
        guide_root = tree.insert("", "end", text="📘 使用指南", open=True)
        faq_root = tree.insert("", "end", text="❓ 常见问题", open=True)
        intro = tree.insert(guide_root, "end", text="1. 软件概述", open=False)
        tree.insert(intro, "end", text="1.1 什么是浪兮效率时钟")
        tree.insert(intro, "end", text="1.2 主要特性")
        quick = tree.insert(guide_root, "end", text="2. 快速入门", open=False)
        tree.insert(quick, "end", text="2.1 安装与启动")
        tree.insert(quick, "end", text="2.2 主界面介绍")
        core = tree.insert(guide_root, "end", text="3. 核心操作", open=False)
        tree.insert(core, "end", text="3.1 记录时间")
        tree.insert(core, "end", text="3.2 日计划管理")
        tree.insert(core, "end", text="3.3 日程自动分配")
        tree.insert(core, "end", text="3.4 日历使用")
        advanced = tree.insert(guide_root, "end", text="4. 高级功能", open=False)
        tree.insert(advanced, "end", text="4.1 临时计划变更")
        tree.insert(advanced, "end", text="4.2 数据备份与恢复")
        tree.insert(advanced, "end", text="4.3 自定义设置")
        tree.insert(advanced, "end", text="4.4 外观主题")
        tree.insert(advanced, "end", text="4.5 帮助与支持")
        q_cut = tree.insert(faq_root, "end", text="切分制问题", open=False)
        tree.insert(q_cut, "end", text="为什么没有记录也有完成度？")
        tree.insert(q_cut, "end", text="保存切分制计划提示背景类别无效")
        tree.insert(q_cut, "end", text="切分制下新增记录提示冲突")
        q_alloc = tree.insert(faq_root, "end", text="分配制问题", open=False)
        tree.insert(q_alloc, "end", text="单个类别时长超过24小时")
        tree.insert(q_alloc, "end", text="如何使总时长超过24小时")
        q_cal = tree.insert(faq_root, "end", text="日历显示问题", open=False)
        tree.insert(q_cal, "end", text="某天显示“PD”是什么意思？")
        tree.insert(q_cal, "end", text="日历格子不显示或按钮消失")
        q_data = tree.insert(faq_root, "end", text="数据与恢复", open=False)
        tree.insert(q_data, "end", text="误删计划或记录如何恢复？")
        tree.insert(q_data, "end", text="重置设置数据会删除计划吗？")
        q_other = tree.insert(faq_root, "end", text="其他问题", open=False)
        tree.insert(q_other, "end", text="无法启动或崩溃")
        tree.insert(q_other, "end", text="如何联系开发者？")
        content_text = tk.Text(right_frame, wrap=tk.WORD, font=("微软雅黑", 11))
        content_text.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(content_text, command=content_text.yview)
        content_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        help_content = {
            "1.1 什么是浪兮效率时钟": "浪兮效率时钟是一款基于分类时间管理理念的桌面工具。它借鉴3×8时间管理法，帮助用户将一天的时间按自定义类别进行计划与追踪，并自动统计完成度。",
            "1.2 主要特性": "两种计划模式（切分制/分配制）；多套日计划预设；日程自动分配规则；记录管理（增删改查）；日历视图；数据备份与恢复；界面主题自定义。",
            "2.1 安装与启动": "确保系统已安装 Python 3.6+，将 `浪兮效率时钟.py` 保存到任意文件夹，双击运行或执行 `python 浪兮效率时钟.py`。首次启动会自动创建数据文件夹。",
            "2.2 主界面介绍": "顶部大时钟实时显示时间；中部显示今日各类别完成情况，点击可进入记录管理；底部四个按钮：记录、日历、管理、设置；下方有宣传语。",
            "3.1 记录时间": "点击「记录」按钮，选择输入模式（起止时间或时长+单点），填写内容和类别，保存。切分制下不允许时间重叠，分配制下同类别不能重叠。",
            "3.2 日计划管理": "在「管理」→「日计划管理」中可创建、编辑、删除日计划。切分制要求总和24小时且必须选背景类别；分配制不限总和但单个类别≤24小时。",
            "3.3 日程自动分配": "在「管理」→「日程安排」中可添加按星期、月份、年度、月周几的规则，优先级从上到下。默认兜底规则不可删除。",
            "3.4 日历使用": "点击日历格子可查看该天详情。格子底色为日计划颜色与白色混合，百分比数字颜色代表完成度（红<40%、橙<70%、金<90%、绿≥90%）。",
            "4.1 临时计划变更": "在「管理」→「临时计划变更」中可快速切换今日计划，程序会引导处理类别不匹配和重叠区间。",
            "4.2 数据备份与恢复": "在「设置」→「存档管理」中可导出 `.lxtm` 存档，导入时可选覆盖或合并模式，冲突时逐日解决。",
            "4.3 自定义设置": "可调整超限阈值、时间显示格式（秒、12/24小时制、AM/PM）。",
            "4.4 外观主题": "可调整日历底色白化系数，以及窗口背景、按钮颜色等，并提供预设方案。",
            "4.5 帮助与支持": "本帮助中心及右上角联系开发者（QQ:3442386217，抖音@浪兮有点浪）。",
            "为什么没有记录也有完成度？": "切分制下未记录的时间自动归入背景类别，因此背景类别会有进度。",
            "保存切分制计划提示背景类别无效": "请确保在编辑界面中，某个类别前选中了「背景类别」单选按钮，且该类别存在于列表中。",
            "切分制下新增记录提示冲突": "切分制禁止任何时间重叠，请修改记录时间或调整已有记录。",
            "单个类别时长超过24小时": "分配制中每个类别时长不能超过24小时，保存时会报错。",
            "如何使总时长超过24小时": "分配制允许计划总时长超过24小时，但每个类别完成度单独计算，总完成度上限100%。",
            "某天显示“PD”是什么意思？": "表示该天使用的日计划已被删除，请重新为该天指定一个有效的日计划。",
            "日历格子不显示或按钮消失": "重启程序；若仍存在，检查数据文件夹中是否有损坏的 JSON 文件，可尝试使用存档管理恢复。",
            "误删计划或记录如何恢复？": "如之前有导出存档，可通过导入存档恢复（合并模式）。",
            "重置设置数据会删除计划吗？": "不会，重置设置数据只影响 config.json 中的参数，不影响计划、日程规则和记录。",
            "无法启动或崩溃": "检查 Python 版本需要 3.6+；删除损坏的配置文件（如 plans.json）重新启动。",
            "如何联系开发者？": "在帮助页面右上角点击「联系开发者」，会显示 QQ 号和抖音账号。"
        }
        def on_tree_select(event):
            selected = tree.selection()
            if not selected: return
            item = selected[0]
            text = tree.item(item, "text")
            if text in help_content:
                content_text.delete(1.0, tk.END)
                content_text.insert(tk.END, help_content[text])
            else:
                content_text.delete(1.0, tk.END)
                content_text.insert(tk.END, "请从下方选择一个具体条目。")
        tree.bind("<<TreeviewSelect>>", on_tree_select)
        ttk.Button(f, text="返回设置", command=self.show_setting).pack(pady=10)

    def contact_developer(self):
        messagebox.showinfo("联系开发者", "QQ号：3442386217\n抖音：@浪兮有点浪")

    # ========== 存档管理（修复导入） ==========
    def show_archive_management(self):
        self.clear()
        f = ttk.Frame(self.root, padding=30)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="存档管理", font=("微软雅黑", 16, "bold")).pack(pady=10)
        ttk.Button(f, text="导出存档", command=self.export_archive, width=20).pack(pady=5)
        ttk.Button(f, text="导入存档", command=self.import_archive, width=20).pack(pady=5)
        ttk.Button(f, text="返回", command=self.show_setting, width=20).pack(pady=20)

    def export_archive(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".lxtm", filetypes=[("浪兮效率时钟存档", "*.lxtm")], title="导出存档")
        if not file_path: return
        try:
            temp_dir = os.path.join(ROOT_DIR, "temp_export")
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            for fname in ["config.json", "plans.json", "schedule_rules.json", "manual_plans.json"]:
                src = os.path.join(ROOT_DIR, fname)
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(temp_dir, fname))
            if os.path.exists(DATA_DIR):
                for day_folder in os.listdir(DATA_DIR):
                    day_path = os.path.join(DATA_DIR, day_folder)
                    if os.path.isdir(day_path):
                        has_data = False
                        for f in os.listdir(day_path):
                            if f in ["records.json", "day_plan.json"]:
                                has_data = True
                                break
                        if has_data:
                            shutil.copytree(day_path, os.path.join(temp_dir, "数据", day_folder))
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        arcname = os.path.relpath(full_path, temp_dir)
                        zipf.write(full_path, arcname)
            shutil.rmtree(temp_dir)
            messagebox.showinfo("成功", f"存档已导出至：{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")

    def import_archive(self):
        file_path = filedialog.askopenfilename(filetypes=[("浪兮效率时钟存档", "*.lxtm")], title="选择存档文件")
        if not file_path: return
        mode_dialog = tk.Toplevel(self.root)
        mode_dialog.title("导入模式")
        mode_dialog.geometry("450x250")
        mode_dialog.transient(self.root)
        mode_dialog.grab_set()
        ttk.Label(mode_dialog, text="请选择导入模式：").pack(pady=10)
        mode_var = tk.StringVar(value="merge")
        ttk.Radiobutton(mode_dialog, text="合并模式（保留现有数据，冲突时逐日选择）", variable=mode_var, value="merge").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(mode_dialog, text="覆盖模式（完全替换现有数据，谨慎使用）", variable=mode_var, value="overwrite").pack(anchor=tk.W, padx=20)
        update_config_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(mode_dialog, text="同时更新配置文件（计划、日程规则等）", variable=update_config_var).pack(anchor=tk.W, padx=20, pady=10)
        def confirm_import():
            mode = mode_var.get()
            update_config = update_config_var.get()
            mode_dialog.destroy()
            self._do_import(file_path, mode, update_config)
        ttk.Button(mode_dialog, text="确认", command=confirm_import).pack(pady=10)

    def _do_import(self, archive_path, mode, update_config):
        temp_dir = os.path.join(ROOT_DIR, "temp_import")
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        try:
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            if mode == "overwrite":
                if messagebox.askyesno("警告", "覆盖模式将删除当前所有数据（包括记录、计划、日程等），确定继续吗？"):
                    for item in os.listdir(ROOT_DIR):
                        item_path = os.path.join(ROOT_DIR, item)
                        if item in ["数据", "config.json", "plans.json", "schedule_rules.json", "manual_plans.json"]:
                            if os.path.isdir(item_path): shutil.rmtree(item_path)
                            elif os.path.isfile(item_path): os.remove(item_path)
                    for item in os.listdir(temp_dir):
                        src = os.path.join(temp_dir, item)
                        dst = os.path.join(ROOT_DIR, item)
                        if os.path.isdir(src): shutil.copytree(src, dst)
                        else: shutil.copy2(src, dst)
                    self.config = DataCore.load_config()
                    self.overtime_threshold = self.config.get("overtime_threshold", 105)
                    self.whiten_k = self.config.get("whiten_k", 0.6)
                    self.show_seconds = self.config.get("show_seconds", True)
                    self.use_24h = self.config.get("use_24h", True)
                    self.show_ampm = self.config.get("show_ampm", False)
                    self.theme = self.config.get("theme", DEFAULT_THEME)
                    self.apply_theme()
                    self.plans = DataCore.load_plans()
                    messagebox.showinfo("成功", "导入完成（覆盖模式）")
            else:
                if update_config:
                    for fname in ["plans.json", "schedule_rules.json", "manual_plans.json"]:
                        src = os.path.join(temp_dir, fname)
                        dst = os.path.join(ROOT_DIR, fname)
                        if os.path.exists(src):
                            shutil.copy2(src, dst)
                    src_config = os.path.join(temp_dir, "config.json")
                    if os.path.exists(src_config):
                        shutil.copy2(src_config, CONFIG_PATH)
                    self.config = DataCore.load_config()
                    self.overtime_threshold = self.config.get("overtime_threshold", 105)
                    self.whiten_k = self.config.get("whiten_k", 0.6)
                    self.show_seconds = self.config.get("show_seconds", True)
                    self.use_24h = self.config.get("use_24h", True)
                    self.show_ampm = self.config.get("show_ampm", False)
                    self.theme = self.config.get("theme", DEFAULT_THEME)
                    self.apply_theme()
                    self.plans = DataCore.load_plans()
                import_days = set()
                data_dir_import = os.path.join(temp_dir, "数据")
                if os.path.exists(data_dir_import):
                    for day_folder in os.listdir(data_dir_import):
                        import_days.add(day_folder)
                if import_days:
                    local_days = set()
                    if os.path.exists(DATA_DIR):
                        for day_folder in os.listdir(DATA_DIR):
                            local_days.add(day_folder)
                    conflicts = import_days & local_days
                    for day in import_days - conflicts:
                        src_day = os.path.join(data_dir_import, day)
                        dst_day = os.path.join(DATA_DIR, day)
                        if os.path.exists(src_day):
                            os.makedirs(dst_day, exist_ok=True)
                            for f in os.listdir(src_day):
                                src_file = os.path.join(src_day, f)
                                dst_file = os.path.join(dst_day, f)
                                shutil.copy2(src_file, dst_file)
                    for day in conflicts:
                        self._resolve_day_conflict(day, temp_dir)
                messagebox.showinfo("成功", "导入完成（合并模式）")
            shutil.rmtree(temp_dir)
            self.show_setting()
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{str(e)}")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _resolve_day_conflict(self, day, temp_dir):
        local_records = DataCore.load_records(day)
        local_day_plan = DataCore.load_day_plan(day)
        import_records_path = os.path.join(temp_dir, "数据", day, "records.json")
        import_day_plan_path = os.path.join(temp_dir, "数据", day, "day_plan.json")
        import_records = []
        import_day_plan = None
        if os.path.exists(import_records_path):
            with open(import_records_path, 'r', encoding='utf-8') as f:
                import_records = json.load(f)
        if os.path.exists(import_day_plan_path):
            with open(import_day_plan_path, 'r', encoding='utf-8') as f:
                import_day_plan = json.load(f)
        local_plan_name = local_day_plan.get("name") if isinstance(local_day_plan, dict) else None
        import_plan_name = import_day_plan.get("name") if isinstance(import_day_plan, dict) else None
        if local_plan_name == import_plan_name:
            merged_records = local_records.copy()
            for r in import_records:
                if r not in merged_records:
                    merged_records.append(r)
            DataCore.save_all_records(merged_records, day)
            return
        dialog = tk.Toplevel(self.root)
        dialog.title(f"冲突解决 - {day}")
        dialog.geometry("900x600")
        dialog.transient(self.root)
        dialog.grab_set()
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        local_frame = ttk.Frame(notebook)
        notebook.add(local_frame, text="本地数据")
        local_info = ttk.LabelFrame(local_frame, text=f"日计划：{local_plan_name}")
        local_info.pack(fill=tk.X, padx=5, pady=5)
        local_text = tk.Text(local_frame, wrap=tk.WORD, height=15)
        local_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        for r in local_records:
            local_text.insert(tk.END, f"{r.get('标签')} {r.get('开始')}-{r.get('结束')} | {r.get('内容')}\n")
        import_frame = ttk.Frame(notebook)
        notebook.add(import_frame, text="导入数据")
        import_info = ttk.LabelFrame(import_frame, text=f"日计划：{import_plan_name}")
        import_info.pack(fill=tk.X, padx=5, pady=5)
        import_text = tk.Text(import_frame, wrap=tk.WORD, height=15)
        import_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        for r in import_records:
            import_text.insert(tk.END, f"{r.get('标签')} {r.get('开始')}-{r.get('结束')} | {r.get('内容')}\n")
        result = {"choice": None}
        keep_records_var = tk.BooleanVar(value=True)
        def choose_local():
            result["choice"] = "local"
            dialog.destroy()
        def choose_import():
            result["choice"] = "import"
            dialog.destroy()
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="保留本地日计划", command=choose_local).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="使用导入日计划", command=choose_import).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(btn_frame, text="保留所有记录（合并）", variable=keep_records_var).pack(side=tk.LEFT, padx=10)
        self.root.wait_window(dialog)
        if result["choice"] == "local":
            if keep_records_var.get():
                merged = local_records.copy()
                for r in import_records:
                    if r not in merged:
                        merged.append(r)
                DataCore.save_all_records(merged, day)
        elif result["choice"] == "import":
            if keep_records_var.get():
                merged = import_records.copy()
                for r in local_records:
                    if r not in merged:
                        merged.append(r)
                DataCore.save_all_records(merged, day)
            else:
                DataCore.save_all_records(import_records, day)
            if import_plan_name:
                DataCore.save_day_plan(import_plan_name, day)

if __name__ == "__main__":
    root = tk.Tk()
    app = EfficiencyClock(root)
    root.mainloop()