#浪兮工具包\辅助工具\输出封装.py
"""
    依赖：目录构建
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

try:
    import 目录构建 as lxpb
except:
    from 浪兮工具包.辅助工具 import 目录构建 as lxpb

LOG_DIR = os.path.join(lxpb.L_DIR, "default")
os.makedirs(LOG_DIR, exist_ok=True)

def switch_dir(dir,p=False):
    global LOG_DIR
    LOG_DIR = os.path.join(lxpb.L_DIR, dir)
    os.makedirs(LOG_DIR, exist_ok=True)
    if p:
        print(f"日志目录已切换为{LOG_DIR}")
    return LOG_DIR

FILE_NAME="default"
FILE_FORMAT="txt"
FILE_MODE="a+"

def get_enc(encoding):
    global FILE_tryMODE
    m = ''
    if encoding in (-2, 0):
        if FILE_MODE in ("r", "r+", "w", "w+", "a", "a+"):
            m = "utf-8"
    else:
        if encoding in (-1, 1):
            m = "utf-8"
        else:
            m = encoding
    return m

def switch_file(file_name,file_format,file_mode,encoding=-2,p=False):
    global LOG_DIR,FILE_NAME,FILE_FORMAT,FILE_MODE
    FILE_NAME = file_name
    FILE_FORMAT = file_format
    FILE_MODE = file_mode
    m = get_enc(encoding)
    if m:
        with open(os.path.join(LOG_DIR, FILE_NAME + "." + FILE_FORMAT), FILE_MODE, encoding = m) as f:
            pass
    else:
        with open(os.path.join(LOG_DIR, FILE_NAME + "." + FILE_FORMAT), FILE_MODE) as f:
            pass
    if p:
        print(f"日志文件已切换为{FILE_NAME + "." + FILE_FORMAT}")
        print(f"读写方式已切换为{FILE_MODE}")

def switch_mode(mode,p=False):
    global FILE_MODE
    FILE_MODE=mode
    if p:
        print(f"读写方式已切换为{FILE_MODE}")
        return FILE_MODE

def p(content, nl=1, encoding=-2, p=True):
    global LOG_DIR,FILE_NAME,FILE_FORMAT,FILE_MODE
    if p:
        print(content+'\n'*nl, end='')
    try:
        m = get_enc(encoding)
        if m:
            with open(os.path.join(LOG_DIR, FILE_NAME + "." + FILE_FORMAT), FILE_MODE, encoding=m) as f:
                f.write(content+'\n'*nl)
        else:
            with open(os.path.join(LOG_DIR, FILE_NAME + "." + FILE_FORMAT), FILE_MODE) as f:
                f.write(content+'\n'*nl)
        return content+'\n'*nl
    except Exception as e:
        if p:
            print(f"日志记录失败：{str(e)}（日志文件：{FILE_NAME}.{FILE_FORMAT}，读写方式：{FILE_MODE}）")
        return str(e)

if __name__ == "__main__":
    print("This file doesn't seem necessary running! ——开发者：浪兮")