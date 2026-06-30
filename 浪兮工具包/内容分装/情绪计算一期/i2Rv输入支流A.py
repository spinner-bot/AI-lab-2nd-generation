# -*- coding: utf-8 -*-
"""
    浪兮 i2Rv输入支流A【AppID:130002】
    功能：全自动提取 DINOv2 图像特征（768维）添加 feature A 列
    依赖：torch, torchvision, pillow, tqdm
    规范：目录构建 | 自动下载模型 | 保留进度条 | 全自动处理 | 安静模式
"""
import os

# 设置模型存放路径到D盘
os.environ['TORCH_HOME'] = r'D:\PyTorchModels'

import csv
import torch
from tqdm import tqdm
from pathlib import Path
from PIL import Image
from torchvision import transforms

# ===================== 强制导入目录构建 =====================
try:
    import 浪兮工具包.辅助工具.目录构建 as lxpb
except ImportError:
    import 目录构建 as lxpb

# ===================== 全局配置 =====================
TOOL_NAME = "i2Rv输入支流A"
APP_ID = "130002"
BASE_RES_DIR = lxpb.R_DIR
SHARE_TOOL_ROOT = os.path.join(BASE_RES_DIR, "图片资源", "110005")  # 沿用支流B的共享ID
PACKAGE_ROOT = os.path.join(SHARE_TOOL_ROOT, "i2Rv整合数据包")

# ===================== 模型加载（单例，只加载一次） =====================
_model = None
_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

def get_model():
    global _model
    if _model is None:
        print("正在加载 DINOv2 ViT-B/14 模型（首次运行会自动下载）...")
        _model = torch.hub.load('facebookresearch/dinov2', 'dinov2_vitb14')
        _model = _model.eval()
        print("模型加载完成。")
    return _model

# ===================== 特征提取（返回空格分隔的768维特征） =====================
def extract_feature_a(image_path):
    """返回空格分隔的768维特征字符串，失败返回空字符串"""
    try:
        img = Image.open(image_path).convert("RGB")
        tensor = _transform(img).unsqueeze(0)          # (1, 3, 224, 224)
        with torch.no_grad():
            out = get_model().forward_features(tensor)
            cls_token = out['x_norm_clstoken']          # (1, 768)
        # 保留6位小数
        return " ".join([f"{v:.6f}" for v in cls_token[0].tolist()])
    except Exception as e:
        # 静默失败或打印警告（避免刷屏）
        # print(f"[警告] 处理 {image_path} 失败: {e}")
        return ""

# ===================== CSV 处理函数 =====================
def has_feature_b(csv_path):
    """检查是否已有 feature B 列"""
    try:
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)
            return "feature B" in header
    except:
        return False

def has_feature_a(csv_path):
    """检查是否已有 feature A 列"""
    try:
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)
            return "feature A" in header
    except:
        return False

def process_csv(csv_path):
    """为已有 feature B 的 CSV 添加 feature A 列"""
    try:
        csv_abs = Path(csv_path).absolute()
        package_root = csv_abs.parent.parent   # i2Rv整合数据包目录
        rows = []
        header = []

        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)
            # 确定插入位置：在 feature B 之后
            try:
                idx_b = header.index("feature B")
            except ValueError:
                # 没有 feature B 列，跳过
                return False
            # 在 feature B 列后面插入 feature A
            header.insert(idx_b + 1, "feature A")
            rows = list(reader)

        temp_file = f"{csv_path}.tmp"
        with open(temp_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in rows:
                # 确保行长度足够
                if len(row) < idx_b + 1:
                    row.extend([""] * (idx_b + 1 - len(row)))
                # 提取图片路径（假设第二列，索引1，可根据实际调整）
                img_rel_path = row[1] if len(row) > 1 else ""
                if img_rel_path:
                    img_full_path = os.path.join(package_root, img_rel_path)
                    feat = extract_feature_a(img_full_path)
                else:
                    feat = ""
                # 在 feature B 之后插入
                row.insert(idx_b + 1, feat)
                writer.writerow(row)

        os.remove(csv_path)
        os.rename(temp_file, csv_path)
        return True
    except Exception as e:
        print(f"处理失败 {csv_path}: {e}")
        return False

# ===================== 主流程（全自动） =====================
def auto_process_all_packages():
    print("🚀 开始执行 i2Rv输入支流A (DINOv2 特征提取)")
    print("=" * 60)

    # 1. 预加载模型（避免在处理时重复加载）
    print("[1/4] 初始化 DINOv2 模型...")
    try:
        get_model()
        print("✅ 模型加载成功")
    except Exception as e:
        print(f"⚠️ 模型加载失败：{e}")
        input("\n按回车键继续...")
        return

    print("[2/4] 校验工作目录")
    if not os.path.exists(PACKAGE_ROOT):
        print(f"⚠️ 未找到 i2Rv整合数据包！路径：{PACKAGE_ROOT}")
        input("\n按回车键继续...")
        return
    print(f"✅ 目录校验完成")

    print("[3/4] 扫描待处理CSV文件")
    all_csv = list(Path(PACKAGE_ROOT).rglob("*.csv"))
    # 筛选：已有 feature B 且没有 feature A 的
    target_files = [f for f in all_csv if has_feature_b(f) and not has_feature_a(f)]

    if not target_files:
        print("✅ 所有符合条件（已有feature B）的CSV均已包含 feature A！")
        input("\n按回车键继续...")
        return
    print(f"✅ 待处理文件总数：{len(target_files)}")

    print("[4/4] 批量提取 DINOv2 特征")
    success_count = 0
    fail_count = 0

    for csv_file in tqdm(target_files, desc="Processing", ncols=70, colour="blue"):
        if process_csv(str(csv_file)):
            success_count += 1
        else:
            fail_count += 1

    print("=" * 60)
    print(f"🎉 处理完成")
    print(f"✅ 成功：{success_count} | ❌ 失败：{fail_count}")
    print("=" * 60)
    input("\n按回车键继续...")

# ===================== 启动接口（兼容启动器） =====================
def run_app(run_app_main, *info):
    auto_process_all_packages()

if __name__ == "__main__":
    run_app(None)