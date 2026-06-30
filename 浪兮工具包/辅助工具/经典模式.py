# 经典模式【AppID:10004】

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def run_app(run_app_main, *info):
    import json
    try:
        import 浪兮工具包.辅助工具.目录构建 as lxpb
    except ImportError:
        import 目录构建 as lxpb
    APP_STATE_DIR = os.path.join(lxpb.S_DIR, "app_home")
    p = os.path.join(APP_STATE_DIR, "running.json")
    os.makedirs(APP_STATE_DIR, exist_ok=True)
    running = True
    run_app_main(10003)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([True], f)
    while running:
        run_app_main(30001)
        with open(p, "r", encoding="utf-8") as f:
            running = json.load(f)[0]
    print("\n\033[1;36m开发者：\033[1;93m浪兮\033[1;36m （抖音@\033[1;93m浪兮有点浪\033[1;36m）\033[0m")

if __name__ == "__main__":
    pass