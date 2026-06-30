import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from datetime import datetime

#14位时间戳获取
def t14():
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    return now