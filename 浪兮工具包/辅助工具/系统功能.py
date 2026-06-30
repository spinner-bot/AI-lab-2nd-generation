#系统功能（无package内依赖）
#开发者：浪兮

#无视警告
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

#调节
def log(msg,p=True):
    print(msg,end="\n"if p else "")

#优化菜单
def menu3(menu_name,guidance="choice",back="返回",*entrance):
    """涉及同名多选项时，请勿使用优化菜单！"""
    temp=menu2(menu_name,guidance,back,*entrance)
    if temp:
        return entrance[temp-1]

#封装菜单
def menu2(menu_name,guidance="choice",back="返回",*entrance):
    choice=menu(menu_name,guidance,back,entrance)
    if choice==-1:
        log("入口不存在，请重新输入！")
        return menu2(menu_name, guidance, back, entrance)
    if choice==-2:
        log("输入不合法，请重新输入！")
        return menu2(menu_name, guidance, back, entrance)
    if choice==0:
        log("返回上一级：")
    return choice

#通用菜单
def menu(menu_name,guidance="choice",back="返回",*entrance):
    try:
        if len(entrance)==1:
            while isinstance(entrance[0],tuple):
                entrance=entrance[0]
    except:
        entrance=()
    log(f"{menu_name}:0.{back}",False)
    for i in range(len(entrance)):
        log(f" {i+1}.{entrance[i]}",False)
    log(f"\n>>{guidance}：", False)
    choice = input()
    try:
        choice=int(choice)
        if(choice>=0 and choice<=len(entrance)):
            return choice
        else:
            return -1
    except:
        return -2

if __name__ == "__main__":
    print("This file doesn't seem necessary running! ——开发者：浪兮")