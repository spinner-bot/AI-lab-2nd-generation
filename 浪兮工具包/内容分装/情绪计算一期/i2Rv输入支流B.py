# -*- coding: utf-8 -*-
"""
    浪兮 i2Rv输入支流B【AppID:130001】
    功能：全自动提取面部几何特征添加feature B列
    终极修复：采用CLI版正确特征算法 + Task API + 二进制模型加载
    规范：目录构建 | 自动下载模型 | 保留进度条 | 全自动处理 | 安静模式
"""
import os
# 隐藏 MediaPipe / TensorFlow 冗余日志
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["MEDIAPIPE_DISABLE_CLEARCUT"] = "1"
os.environ["MEDIAPIPE_DISABLE_GPU"] = "1"

import csv
import cv2
import numpy as np
import urllib.request
from tqdm import tqdm
from pathlib import Path

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# ===================== MediaPipe Task API 导入 =====================
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe import Image as MpImage

# ===================== 强制导入目录构建（项目可迁移） =====================
try:
    import 浪兮工具包.辅助工具.目录构建 as lxpb
except ImportError:
    import 目录构建 as lxpb

# ===================== 全局配置 =====================
TOOL_NAME = "i2Rv输入支流B"
SHARE_TOOL_ID = "110005"
BASE_RES_DIR = lxpb.R_DIR
SHARE_TOOL_ROOT = os.path.join(BASE_RES_DIR, "图片资源", SHARE_TOOL_ID)
PACKAGE_ROOT = os.path.join(SHARE_TOOL_ROOT, "i2Rv整合数据包")

# 模型文件存放目录及路径（可能包含中文，用二进制方式加载）
MODEL_DIR = os.path.join(os.path.dirname(__file__), ".face_landmarker_model")
MODEL_PATH = os.path.join(MODEL_DIR, "face_landmarker.task")
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"

# ===================== 正确特征点索引（来自CLI版，已验证） =====================
LEFT_PUPIL = 468
RIGHT_PUPIL = 473
LEFT_BROW_IN = 55
RIGHT_BROW_IN = 285
LEFT_MOUTH = 61
RIGHT_MOUTH = 291
NOSE_BASE = 2
LEFT_EYE_TOP = 159
LEFT_EYE_BOTTOM = 145
RIGHT_EYE_TOP = 386
RIGHT_EYE_BOTTOM = 374
UPPER_LIP = 13
LOWER_LIP = 14

# ===================== 辅助函数：两点距离 =====================
def compute_distance(point1, point2):
    return np.hypot(point1[0] - point2[0], point1[1] - point2[1])

# ===================== 自动下载模型文件 =====================
def download_model():
    if os.path.exists(MODEL_PATH):
        return MODEL_PATH
    os.makedirs(MODEL_DIR, exist_ok=True)
    print(f"正在下载模型文件（约 12MB）...\n{MODEL_URL}")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("模型下载完成。")
    except Exception as e:
        raise RuntimeError(f"模型下载失败：{e}\n请手动下载并放入 {MODEL_PATH}")
    return MODEL_PATH

# ===================== 初始化检测器（二进制buffer，兼容中文路径） =====================
_detector = None

def get_face_landmarker():
    global _detector
    if _detector is None:
        model_path = download_model()
        with open(model_path, "rb") as f:
            model_buffer = f.read()
        base_options = python.BaseOptions(model_asset_buffer=model_buffer)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5
        )
        _detector = vision.FaceLandmarker.create_from_options(options)
    return _detector

# ===================== 统一UI样式 =====================
class Colors:
    GREEN = "\033[92m"
    BLUE  = "\033[94m"
    YELLOW= "\033[93m"
    RED   = "\033[91m"
    RESET = "\033[0m"

ICONS = {
    "success": "✅", "start": "🚀", "done": "🎉", "warn": "⚠️"
}

def print_divider(char="=", length=60):
    print(Colors.BLUE + char * length + Colors.RESET)

def log(msg, color=Colors.RESET):
    print(f"{color}{msg}{Colors.RESET}")

# ===================== 核心特征计算（完全采用CLI版正确算法） =====================
def calculate_feature_b(image_path):
    """
    返回格式： "d_brow h_mouth w_eye h_jaw" 四个浮点数，空格分隔
    """
    default_feat = "0.0 0.0 0.0 0.0"

    if not Path(image_path).exists():
        return default_feat

    # 兼容中文路径读取
    img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return default_feat

    h, w = img.shape[:2]
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = MpImage(image_format=mp.ImageFormat.SRGB, data=rgb_img)

    detector = get_face_landmarker()
    result = detector.detect(mp_image)
    if not result.face_landmarks:
        return default_feat

    landmarks = result.face_landmarks[0]

    def get_point(idx):
        return (landmarks[idx].x * w, landmarks[idx].y * h)

    # 瞳孔（用于IPD）
    left_pupil = get_point(LEFT_PUPIL)
    right_pupil = get_point(RIGHT_PUPIL)
    ipd = compute_distance(left_pupil, right_pupil)
    if ipd < 1e-6:
        ipd = 1.0

    # 眉间距
    left_brow_in = get_point(LEFT_BROW_IN)
    right_brow_in = get_point(RIGHT_BROW_IN)
    d_brow = compute_distance(left_brow_in, right_brow_in) / ipd

    # 口鼻距（嘴角中点与鼻根）
    left_mouth = get_point(LEFT_MOUTH)
    right_mouth = get_point(RIGHT_MOUTH)
    mouth_mid = ((left_mouth[0] + right_mouth[0]) / 2, (left_mouth[1] + right_mouth[1]) / 2)
    nose_base = get_point(NOSE_BASE)
    h_mouth = compute_distance(mouth_mid, nose_base) / ipd

    # 眼睑高度（均值）
    left_eye_top = get_point(LEFT_EYE_TOP)
    left_eye_bottom = get_point(LEFT_EYE_BOTTOM)
    right_eye_top = get_point(RIGHT_EYE_TOP)
    right_eye_bottom = get_point(RIGHT_EYE_BOTTOM)
    left_eye_h = compute_distance(left_eye_top, left_eye_bottom)
    right_eye_h = compute_distance(right_eye_top, right_eye_bottom)
    w_eye = (left_eye_h + right_eye_h) / 2 / ipd

    # 唇高
    upper_lip = get_point(UPPER_LIP)
    lower_lip = get_point(LOWER_LIP)
    h_jaw = compute_distance(upper_lip, lower_lip) / ipd

    return f"{d_brow:.4f} {h_mouth:.4f} {w_eye:.4f} {h_jaw:.4f}"

# ===================== CSV处理函数（原版逻辑，仅调用新特征函数） =====================
def has_feature_b(csv_path):
    try:
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            return "feature B" in next(csv.reader(f))
    except:
        return False

def process_csv(csv_path):
    try:
        csv_abs = Path(csv_path).absolute()
        package_root = csv_abs.parent.parent
        rows = []
        header = []

        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)
            header.append("feature B")
            rows = list(reader)

        temp_file = f"{csv_path}.tmp"
        with open(temp_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in rows:
                if len(row) < 2:
                    row.append("0.0 0.0 0.0 0.0")
                else:
                    img_rel_path = row[1]  # 假设第二列是图片相对路径
                    img_full_path = os.path.join(package_root, img_rel_path)
                    feat = calculate_feature_b(img_full_path)
                    row.append(feat)
                writer.writerow(row)

        os.remove(csv_path)
        os.rename(temp_file, csv_path)
        return True
    except Exception as e:
        log(f"处理失败 {csv_path}: {e}", Colors.RED)
        return False

# ===================== 全自动主流程 =====================
def auto_process_all_packages():
    log(f"{ICONS['start']} 开始执行 i2Rv输入支流B (CLI正确算法版)", Colors.BLUE)
    print_divider()

    log("[1/4] 初始化人脸检测模型", Colors.BLUE)
    try:
        get_face_landmarker()
        log(f"{ICONS['success']} 模型加载成功 (二进制方式, 兼容中文路径)", Colors.GREEN)
    except Exception as e:
        log(f"{ICONS['warn']} 模型加载失败：{e}", Colors.RED)
        input("\n按回车键继续...")
        return

    log("[2/4] 校验工作目录", Colors.BLUE)
    if not os.path.exists(PACKAGE_ROOT):
        log(f"{ICONS['warn']} 未找到 i2Rv整合数据包！", Colors.RED)
        input("\n按回车键继续...")
        return
    log(f"{ICONS['success']} 目录校验完成", Colors.GREEN)

    log("[3/4] 扫描待处理CSV文件", Colors.BLUE)
    all_csv = list(Path(PACKAGE_ROOT).rglob("*.csv"))
    target_files = [f for f in all_csv if not has_feature_b(f)]

    if not target_files:
        log(f"{ICONS['success']} 所有CSV均已包含feature B！", Colors.GREEN)
        print_divider()
        input("\n按回车键继续...")
        return
    log(f"{ICONS['success']} 待处理文件总数：{len(target_files)}", Colors.GREEN)

    log("[4/4] 批量提取面部特征", Colors.BLUE)
    success_count = 0
    fail_count = 0

    for csv_file in tqdm(target_files, desc="Processing", ncols=70, colour="blue"):
        if process_csv(str(csv_file)):
            success_count += 1
        else:
            fail_count += 1

    print_divider()
    log(f"{ICONS['done']} 处理完成", Colors.GREEN)
    log(f"✅ 成功：{success_count} | ❌ 失败：{fail_count}", Colors.BLUE)
    print_divider()
    input("\n按回车键继续...")

# ===================== 启动接口 =====================
def run_app(run_app_main, *info):
    try:
        auto_process_all_packages()
    finally:
        global _detector
        if _detector is not None:
            _detector.close()
            _detector = None

if __name__ == "__main__":
    run_app(None)