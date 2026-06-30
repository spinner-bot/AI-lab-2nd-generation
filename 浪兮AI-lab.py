# 浪兮AI-lab

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
print(f"\n\033[1;36m浪兮AI-lab启动初始化……\033[0m ")
try:
    import torch
    import numpy as np
    import tkinter as tk
except Exception as e:
    print(f"\n\033[1;36m初始化异常：缺少重要的系统组件（{type(e).__name__}：{str(e)}）\033[0m ")
try:
    import 浪兮工具包.辅助工具.系统功能 as lxsf
    import 浪兮工具包.辅助工具.目录构建 as lxpb
    import 浪兮工具包.辅助工具.输出封装 as lxow
    import 浪兮工具包.辅助工具.通用计时 as lxgt
    import 浪兮工具包.辅助工具.模块管理 as lxmm
    import 浪兮工具包.辅助工具.用户管理 as lxum
except Exception as e:
    print(f"\n\033[1;36m初始化失败：缺少必要的系统组件（{type(e).__name__}：{str(e)}）\033[0m ")
    exit()

""" 系统初始化 """

lxow.p(f"\n系统启动：{lxgt.t14()}",False)#启动记录
print()
LAB_DIR = lxpb.build_lab_dirs() #文件系统初始化
lxmm.mm_reset() #软件系统初始化
hid = lxum.u_reset() #用户系统初始化
# 注册用户信息
if not lxum.user_mgr.check_device_registered(hid):
    lxum.user_mgr.register_device_user(hid, input(f"欢迎，新用户{hid}！请设置用户名："))
username = lxum.user_mgr.get_username_by_hardware_id(hid)
lxow.p(f" 用户：{username} 硬件ID：{hid}",True,"utf-8",False)
print(f"\n\033[1;32m欢迎回来，\033[1;93m{username}\033[1;32m！\033[0m")

# 软件启动器
def run_app(app_input,hide=False, *info):
    # 刷新注册表
    lxmm.mm._load_from_json()

    # 输入处理
    input_str = str(app_input).strip()

    # 自动识别
    if input_str.isdigit():
        # 数字 → 作为AppID
        target_app_id = input_str
    else:
        # 名称 → 转为AppID
        target_app_id = lxmm.n2id(input_str)

    # 校验AppID是否有效
    if not target_app_id or not lxmm.mm.is_module_exist(target_app_id):
        print("\n【软件启动器】无效App_ID / 软件名称")
        return

    # 启动软件
    app_name = lxmm.id2n(target_app_id)
    if not hide:
        print(f"\n\033[1;36m【软件启动器：App_ID[{target_app_id}]{app_name}】\033[0m ")
    match app_name:
        case "虚拟测试软件":
            print("该虚拟软件用于系统测试，已退出。")
        case "多用户":
            lxum.start_user_management()
        case "浪兮效率时钟":
            try:
                import 浪兮工具包.微软件包.浪兮效率时钟 as lxtmc
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            print("正在启动浪兮效率时钟……")
            try:
                root = tk.Tk()
                app = lxtmc.EfficiencyClock(root)
                root.mainloop()
            except Exception as e:
                print(f"浪兮效率时钟运行异常：{type(e).__name__}，已退出")
        case "应用桌面":
            try:
                import 浪兮工具包.辅助工具.应用桌面 as lxah
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxah.app_desktop(run_app)
        case "词表管理":
            try:
                import 浪兮工具包.辅助工具.词表系统 as lxvs
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxvs.start_vocab_manager()
        case "文库管理":
            try:
                import 浪兮工具包.辅助工具.文库系统 as lxls
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxls.start_library(run_app)
        case "词义推理":
            try:
                import 浪兮工具包.辅助工具.词义推理 as lxtr
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxtr.start_logic_matcher()
        case "JSON阅读器":
            try:
                import 浪兮工具包.辅助工具.JSON阅读器 as lxjr
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxjr.start_json_reader(run_app, info[0] if info else input("请输入JSON文件地址："))
        case "快速词表切换":
            try:
                import 浪兮工具包.辅助工具.快速词表切换 as lxvq
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxvq.start_fast_vocab_switch()
        case "软件数据恢复":
            try:
                import 浪兮工具包.辅助工具.软件数据恢复 as lxar
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxar.repair_data()
        case "平行语料处理":
            try:
                import 浪兮工具包.辅助工具.平行语料处理 as lxpc
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxpc.run()
        case "翻译训练配置器":
            try:
                import 浪兮工具包.内容分装.翻译训练配置器 as lxtc
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxtc.start_configurator(run_app)
        case "Non-Attention 翻译训练器":
            try:
                import 浪兮工具包.内容分装.Non_Attention翻译训练器 as lxtn
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxtn.start_trainer(run_app)
        case "csv绘图器":
            try:
                import 浪兮工具包.辅助工具.csv绘图器 as lxcp
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxcp.run_app(run_app)
        case "csv150528工具":
            try:
                import 浪兮工具包.内容分装.情绪计算一期.csv150528工具 as lxcp2
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxcp2.run_app(run_app)
        case "csv转图i2Rv适配":
            try:
                import 浪兮工具包.内容分装.情绪计算一期.csv转图i2Rv适配 as lxcp3
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxcp3.run_app(run_app)
        case "csv数据i2Rv切分":
            try:
                import 浪兮工具包.内容分装.情绪计算一期.csv数据i2Rv切分 as lxcp4
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxcp4.run_app(run_app)
        case "i2Rv数据包整合":
            try:
                import 浪兮工具包.内容分装.情绪计算一期.i2Rv数据包整合 as lxcp5
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxcp5.run_app(run_app)
        case "i2Rv情绪映射":
            try:
                import 浪兮工具包.内容分装.情绪计算一期.i2Rv情绪映射 as lxcp6
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxcp6.run_app(run_app)
        case "i2Rv输入支流B":
            try:
                import 浪兮工具包.内容分装.情绪计算一期.i2Rv输入支流B as lxcp7
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            try:
                lxcp7.run_app(run_app)
            except Exception as e:
                print(f"软件启动失败（{type(e).__name__}：{str(e)}）")
        case "i2Rv支流B清洗":
            try:
                import 浪兮工具包.内容分装.情绪计算一期.i2Rv支流B清洗 as lxcp8
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
            lxcp8.run_app(run_app)
        case "i2Rv输入支流A":
            try:
                import 浪兮工具包.内容分装.情绪计算一期.i2Rv输入支流A as lxcp9
                try:
                    lxcp9.run_app(run_app)
                except Exception as e:
                    print(f"软件启动失败（{type(e).__name__}：{str(e)}）")
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
        case "文件导入":
            try:
                import 浪兮工具包.辅助工具.文件导入 as lxfi
                try:
                    lxfi.run_app(run_app)
                except Exception as e:
                    print(f"软件启动失败（{type(e).__name__}：{str(e)}）")
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
        case "i2Rv数据初始化":
            try:
                import 浪兮工具包.内容分装.情绪计算一期.i2Rv数据初始化 as lxi2Rv1
                try:
                    lxi2Rv1.run_app(run_app)
                except Exception as e:
                    print(f"软件启动失败（{type(e).__name__}：{str(e)}）")
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
        case "系统补丁":
            try:
                import 浪兮工具包.辅助工具.系统补丁 as lxsp
                try:
                    lxsp.run_app(run_app)
                except Exception as e:
                    print(f"软件启动失败（{type(e).__name__}：{str(e)}）")
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
        case "经典模式":
            try:
                import 浪兮工具包.辅助工具.经典模式 as lxm1
                try:
                    lxm1.run_app(run_app)
                except Exception as e:
                    print(f"软件启动失败（{type(e).__name__}：{str(e)}）")
            except Exception as e:
                print(f"软件加载失败（{type(e).__name__}：{str(e)}）")
        case _:
            print("无效App_ID，无法启动")

run_app(10004)