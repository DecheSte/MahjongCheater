import time
import requests
import io
import threading
from PIL import ImageGrab
import keyboard
import pygetwindow as gw
import tkinter as tk

API_URL = "http://127.0.0.1:8000/analyze-board"
is_analyzing = False


def show_overlay(thinking, discard_tile, should_call, is_defense):
    """
    🌟 升级版：加长加宽的高容积率科技感半透明悬浮窗
    """

    def create_window():
        root = tk.Tk()
        root.title("AI Overlay")
        root.attributes("-topmost", True)
        root.overrideredirect(True)
        root.attributes("-alpha", 0.9)

        bg_color = "#742a2a" if is_defense else "#2d3748"
        root.configure(bg=bg_color)

        # 📍 调整尺寸：把原本的 400x190 物理升级为 420x280 (加宽加长，专门容纳深度读牌战报)
        screen_width = root.winfo_screenwidth()
        root.geometry(f"420x280+{screen_width - 470}+50")

        # 🎨 头部横幅
        title_text = "🚨 AI 警报：全力防守兜牌！" if is_defense else "🧠 AI 雀圣战术完全体小抄"
        tk.Label(root, text=title_text, font=("Microsoft YaHei", 12, "bold"), fg="#4fd1c5", bg=bg_color).pack(pady=6)

        # 🎯 核心推荐
        rec_tile = f"🔥 切牌推荐: 【 {discard_tile} 】"
        tk.Label(root, text=rec_tile, font=("Microsoft YaHei", 16, "bold"), fg="#f6e05e", bg=bg_color).pack(pady=4)

        # 🎛️ 动作指示
        tk.Label(root, text=f"🎛️ 鸣牌/立直决策: {should_call}", font=("Microsoft YaHei", 11, "bold"), fg="#e2e8f0",
                 bg=bg_color).pack(pady=2)

        # ─── 华丽的分隔线 ───
        tk.Frame(root, height=1, width=380, bg="#4a5568").pack(pady=5)

        # 📋 读牌长考文字区：宽度微调为 390 像素换行，防止右侧文字出界
        # 并且不再做文本截断（彻底删掉了之前的 [:80] 限制），完整展示手顺与筋牌壁牌推导！
        tk.Label(
            root,
            text=f"📋 战术长考分析:\n{thinking}",
            font=("Microsoft YaHei", 9),
            fg="#cbd5e0",
            bg=bg_color,
            wraplength=390,
            justify="left"
        ).pack(pady=4, padx=10)  # 加上内边距，排版更舒适

        # ⏱️ 停留时间稍微延长到 6 秒（6000毫秒），方便你从容读完复杂的防守博弈战报
        root.after(6000, root.destroy)
        root.mainloop()

    threading.Thread(target=create_window, daemon=True).start()


def process_image(img):
    """
    🚀 画质降级神操作：尺寸缩小一倍，体积暴跌75%，抠出大量网络传输时间！
    """
    img = img.convert("RGB")
    new_size = (img.width // 2, img.height // 2)
    resized_img = img.resize(new_size)

    buf = io.BytesIO()
    resized_img.save(buf, format='JPEG', quality=85)  # 用高压缩率的 JPEG 替代 PNG
    buf.seek(0)
    return buf


def capture_and_analyze():
    global is_analyzing
    if is_analyzing: return
    is_analyzing = True

    print("\n⚡ [F8] 触发成功！正在后台剥离窗口并极限压缩图片...")
    try:
        # 模糊定位游戏窗口（支持网页端和微端）
        game_windows = [w for w in gw.getAllWindows() if
                        "雀魂" in w.title or "Mahjong" in w.title or "Chrome" in w.title]

        if game_windows:
            game_win = game_windows[0]
            game_win.activate()
            time.sleep(0.05)  # 极其短暂的等待确保前置

            w, h = game_win.right - game_win.left, game_win.bottom - game_win.top

            full_box = (game_win.left, game_win.top, game_win.right, game_win.bottom)
            img_full = ImageGrab.grab(bbox=full_box)

            # 🚀 [临时拦截器：把整个全图丢进去进行鼠标取点校准手牌]
            #start_pixel_finder(img_full)

            # 📏 完美区域一：精准裁剪底部手牌核心区 (ROI 1)
            hand_box = (
                game_win.left + int(w * 0.135),  # 左边缘
                game_win.top + int(h * 0.854),  # 上边缘
                game_win.left + int(w * 0.941),  # 右边缘（吃满副露区）
                game_win.top + int(h * 0.987)  # 下边缘
            )
            img_hand = ImageGrab.grab(bbox=hand_box)

            # 📏 完美区域二：精准裁剪中间大盘牌河区 (ROI 2)
            center_box = (game_win.left + int(w * 0.25), game_win.top + int(h * 0.18), game_win.right - int(w * 0.25),
                          game_win.bottom - int(h * 0.22))
            img_center = ImageGrab.grab(bbox=center_box)

            dora_box = (
                game_win.left + int(w * 0.089),  # 左边缘
                game_win.top + int(h * 0.251),  # 上边缘
                game_win.left + int(w * 0.771),  # 右边缘
                game_win.top + int(h * 0.534)  # 下边缘
            )
            img_dora = ImageGrab.grab(bbox=dora_box)

            #start_pixel_finder(img_dora)
        else:
            print("⚠️ 未匹配到雀魂窗口，自动全屏降级截取...")
            img_hand = img_center = img_dora = ImageGrab.grab()

        # 极限流处理，转化为轻量级 JPEG 内存流
        hand_buf = process_image(img_hand)
        center_buf = process_image(img_center)

        dora_buf = io.BytesIO()
        img_dora.convert("RGB").save(dora_buf, format='PNG')
        dora_buf.seek(0)

        # 🚨 [终极绝杀：边缘轮廓多边形遮罩算法] 🚨
        import numpy as np
        import cv2

        # 1. 转换为灰度图并进行轻微高斯模糊，消除微小的画面噪点
        open_cv_image = np.array(img_center.convert("RGB"))[:, :, ::-1]
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # 2. ⚡ 核心改动：使用 Canny 算子抓取画面中所有的线条轮廓和异物边缘
        # 平滑的绿桌布在这一步会直接变成完全干净的纯黑色 (0)
        edges = cv2.Canny(blurred, 30, 100)

        cw, ch = img_center.width, img_center.height

        # 3. 🎯 注入你刚才亲自测出的绝对校准轨道顶点
        pts_left = np.array([
            [int(cw * 0.352), int(ch * 0.271)],
            [int(cw * 0.343), int(ch * 0.438)],
            [int(cw * 0.373), int(ch * 0.444)],
            [int(cw * 0.380), int(ch * 0.271)]
        ], np.int32)

        pts_right = np.array([
            [int(cw * 0.622), int(ch * 0.300)],
            [int(cw * 0.627), int(ch * 0.447)],
            [int(cw * 0.659), int(ch * 0.451)],
            [int(cw * 0.651), int(ch * 0.300)]
        ], np.int32)

        pts_top = np.array([
            [int(cw * 0.432), int(ch * 0.216)],
            [int(cw * 0.432), int(ch * 0.244)],
            [int(cw * 0.573), int(ch * 0.246)],
            [int(cw * 0.572), int(ch * 0.216)]
        ], np.int32)

        # 4. 🎭 制作独立纯净的掩膜画布
        mask_left = np.zeros_like(edges)
        mask_right = np.zeros_like(edges)
        mask_top = np.zeros_like(edges)

        cv2.fillPoly(mask_left, [pts_left], 255)
        cv2.fillPoly(mask_right, [pts_right], 255)
        cv2.fillPoly(mask_top, [pts_top], 255)

        # 5. ✂️ 与运算：只保留跑道内部的边缘线条
        roi_left = cv2.bitwise_and(edges, mask_left)
        roi_right = cv2.bitwise_and(edges, mask_right)
        roi_top = cv2.bitwise_and(edges, mask_top)

        # 6. 统计真正落在跑道内的边缘轮廓像素点数
        left_points = np.sum(roi_left > 0)
        right_points = np.sum(roi_right > 0)
        top_points = np.sum(roi_top > 0)

        # 📸 【同时监控三家】：这次生成的图片如果没人立直，绝对是一片死黑！
        cv2.imwrite("debug_track_left.png", roi_left)
        cv2.imwrite("debug_track_right.png", roi_right)
        cv2.imwrite("debug_track_top.png", roi_top)

        print(f"📊 [边缘高频点数] 左侧(上家):{left_points} | 右侧(下家):{right_points} | 上侧(对家):{top_points}")

        # 7. 🏁 精准卡死判定阈值 🏁
        # 因为平滑绿桌布的边缘计数是 0，只有放了立直棒（皮肤）才会产生线条轮廓。
        # 我们将有无立直棒的轮廓点数阈值稳妥设为 15！
        riichi_upstream = "true" if left_points > 550 else "false"
        riichi_downstream = "true" if right_points > 550 else "false"
        riichi_opposite = "true" if top_points > 550 else "false"


        files = {
            "file_hand": ("hand.jpg", hand_buf, "image/jpeg"),
            "file_center": ("center.jpg", center_buf, "image/jpeg"),
            "file_dora": ("dora.png", dora_buf, "image/png")
        }

        payload_data = {
            "riichi_upstream": riichi_upstream,
            "riichi_downstream": riichi_downstream,
            "riichi_opposite": riichi_opposite
        }

        print("📡 封包完毕，向本地 8000 端口发起闪电战轰击...")
        start_time = time.time()
        response = requests.post(API_URL, files=files, data=payload_data, timeout=10)
        result = response.json()
        print(f"⏱️ 本轮全链路闭环耗时仅为: {round(time.time() - start_time, 2)} 秒！")

        if result.get("status") == "success":
            d = result["decision"]
            # 唤醒前端科技浮窗
            show_overlay(d['thinking'], d['discard_tile'], d['should_call'], d['is_defense_mode'])
        else:
            print(f"🚨 后端拒绝响应: {result.get('message')}")

    except Exception as e:
        print(f"🌐 链路中断: {e}")
    finally:
        is_analyzing = False


def on_f8():
    threading.Thread(target=capture_and_analyze, daemon=True).start()


import cv2
import numpy as np


def mouse_click_callback(event, x, y, flags, param):
    """鼠标点击事件回调，用来记录精准像素坐标"""
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"🎯 点击位置绝对坐标: X={x}, Y={y} | 相对比例: X_ratio={x / param[0]:.3f}, Y_ratio={y / param[1]:.3f}")


def start_pixel_finder(img_center):
    """防卡死升级版：取点启动器"""
    # 将 Pillow 图片转为 OpenCV 的 BGR 格式
    open_cv_image = np.array(img_center.convert("RGB"))[:, :, ::-1]

    # 🚨 核心微调一：声明窗口属性为可调整，防止 Windows 直接拉伸卡死
    cv2.namedWindow('Pixel_Finder_Mode', cv2.WINDOW_NORMAL)

    # 将图片的物理宽高传给鼠标回调函数
    cv2.setMouseCallback('Pixel_Finder_Mode', mouse_click_callback,
                         param=(open_cv_image.shape[1], open_cv_image.shape[0]))

    # 🚨 核心微调二：先渲染图片，并强制要求系统刷新事件队列 1 毫秒
    cv2.imshow('Pixel_Finder_Mode', open_cv_image)
    cv2.waitKey(1)  # 👈 这一行是绝杀！强制刷新界面，防止灰色/黑色无响应

    print("\n=== 🔍 鼠标取点调试模式已启动 ===")
    print("👉 操作说明：")
    print("1. 请在弹出的图片窗口中，用鼠标分别点击【上家放置立直棒区域的四个角】（左上、右上、右下、左下）。")
    print("2. 每次点击，下方的控制台终端就会立刻打印出对应的 X 和 Y 绝对坐标。")
    print("3. 取点完成后，在图片窗口上【按键盘任意键】即可关闭窗口，继续后面的数据发送。")
    print("================================\n")

    cv2.waitKey(0)  # 真正等待键盘任意输入退出
    cv2.destroyAllWindows()


if __name__ == "__main__":
    print("==================================================")
    print("   🤖 雀魂 AI 完全体外骨骼系统（极速多图版）已就绪   ")
    print("==================================================")
    print("👉 放心最小化本控制台，回游戏去享受 1.5 秒无感浮窗小抄吧！")

    keyboard.add_hotkey('f8', on_f8)
    keyboard.wait()