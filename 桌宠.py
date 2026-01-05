import pygame
import sys
import time
import random
from datetime import datetime

# ===================== 1. 初始化基础配置 =====================
pygame.init()
pygame.font.init()

# 窗口尺寸（更小巧精致）
window_width = 300
window_height = 300

# 创建无标题栏透明悬浮窗口（置顶）
screen = pygame.display.set_mode(
    (window_width, window_height),
    pygame.NOFRAME | pygame.SRCALPHA | pygame.HWSURFACE
)
pygame.display.set_caption("水潭桌宠")

# 获取屏幕尺寸，初始窗口居中
screen_info = pygame.display.Info()
init_win_x = (screen_info.current_w - window_width) // 2
init_win_y = (screen_info.current_h - window_height) // 2
pygame.display.set_window_position((init_win_x, init_win_y))  # 修复参数为元组

# 美化配色（更自然的渐变/透明色）
COLORS = {
    "water": (80, 180, 255, 180),       # 水潭（半透明淡蓝）
    "drop": (150, 220, 255, 220),       # 水滴（更亮的淡蓝）
    "rain": (200, 230, 255, 150),       # 雨滴（半透明）
    "sun_morning": (255, 230, 100),     # 日出太阳（暖黄）
    "sun_evening": (255, 150, 80),      # 日落太阳（橙红）
    "sky_morning": (180, 220, 255, 100),# 早晨天空（淡蓝透明）
    "sky_evening": (255, 200, 180, 100),# 傍晚天空（橙粉透明）
    "sky_normal": (50, 100, 150, 80),   # 日常天空（深蓝透明）
    "mountain": (200, 180, 100, 200),   # 金山（暖黄不透明）
}

# ===================== 2. 核心状态变量 =====================
# 拖动相关
is_dragging = False
drag_offset_x = 0
drag_offset_y = 0
win_x, win_y = init_win_x, init_win_y

# 特效相关
drop_list = []       # 水滴：[x, y, size, speed, life]
rain_list = []       # 雨滴：[x, y, length, speed]
sun_pos = [-50, -50] # 太阳坐标
sun_radius = 25      # 太阳大小
mountain_show = False# 日照金山彩蛋
run_days = 0         # 运行天数

# ===================== 3. 工具函数 =====================
def get_hour():
    """获取当前系统小时数（24小时制）"""
    return datetime.now().hour

def calc_sun_position(hour):
    """根据小时计算太阳位置：9点升起，17点落下"""
    if 9 <= hour <= 17:
        # 9点在底部，12点在顶部，17点回到底部
        ratio = (hour - 9) / 8  # 0~1的比例
        if ratio <= 0.5:
            # 9-12点：上升（y从250→80）
            y = 250 - (170 * ratio / 0.5)
        else:
            # 12-17点：下降（y从80→250）
            y = 80 + (170 * (ratio - 0.5) / 0.5)
        return [window_width//2, y]
    else:
        return [-50, -50]  # 非时段隐藏太阳

def check_run_days():
    """计算连续运行天数（彩蛋触发：3天）"""
    global run_days, mountain_show
    if hasattr(check_run_days, "start_time"):
        delta = time.time() - check_run_days.start_time
        run_days = delta // (24*60*60)
    else:
        check_run_days.start_time = time.time()
    mountain_show = run_days >= 3

# ===================== 4. 主循环 =====================
running = True
clock = pygame.time.Clock()
check_run_days.start_time = time.time()  # 初始化启动时间

while running:
    current_hour = get_hour()
    sun_pos = calc_sun_position(current_hour)
    check_run_days()  # 更新运行天数

    # ===================== 事件监听 =====================
    for event in pygame.event.get():
        # 退出程序（ESC/关闭窗口）
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            # 任意按键触发水滴跃动（自然物理轨迹）
            else:
                drop_x = random.randint(60, window_width-60)
                drop_y = window_height - 40
                drop_size = random.randint(4, 8)
                # 水滴属性：x,y,大小,上升速度,生命周期
                drop_list.append([drop_x, drop_y, drop_size, -5, 30])

        # 鼠标拖动窗口（修复核心逻辑）
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键按下
                is_dragging = True
                # 记录鼠标相对于窗口的偏移量
                mouse_x, mouse_y = event.pos
                drag_offset_x = mouse_x
                drag_offset_y = mouse_y
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # 左键松开
                is_dragging = False
        if event.type == pygame.MOUSEMOTION and is_dragging:
            # 计算新窗口位置
            mouse_x, mouse_y = pygame.mouse.get_pos()
            win_x = mouse_x - drag_offset_x
            win_y = mouse_y - drag_offset_y
            pygame.display.set_window_position((win_x, win_y))  # 修复参数为元组

    # ===================== 特效更新 =====================
    # 1. 水滴跃动（物理轨迹：先上升减速，再下落消失）
    for drop in drop_list[:]:
        drop[1] += drop[3]  # 移动y坐标
        drop[3] += 0.2      # 重力加速度（上升减速，后下落）
        drop[4] -= 1        # 生命周期减少
        # 水滴落地/生命周期结束则消失
        if drop[1] > window_height - 35 or drop[4] <= 0:
            drop_list.remove(drop)

    # 2. 随机下雨（非日出日落时段触发）
    if sun_pos[0] == -50 and random.randint(0, 30) == 0:
        rain_x = random.randint(0, window_width)
        rain_y = 0
        rain_length = random.randint(8, 15)
        rain_speed = random.randint(3, 6)
        rain_list.append([rain_x, rain_y, rain_length, rain_speed])
    # 雨滴下落更新
    for rain in rain_list[:]:
        rain[1] += rain[3]
        if rain[1] > window_height:
            rain_list.remove(rain)

    # ===================== 绘制渲染 =====================
    # 清空屏幕（全透明背景）
    screen.fill((0, 0, 0, 0))

    # 1. 日照金山彩蛋（运行3天触发）
    if mountain_show:
        # 渐变天空（简化版）
        sky_surface = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
        sky_surface.fill(COLORS["sky_normal"])
        screen.blit(sky_surface, (0, 0))
        # 双层金山（更立体）
        pygame.draw.polygon(screen, COLORS["mountain"], [(50, 200), (150, 100), (250, 200)])
        pygame.draw.polygon(screen, (220, 200, 120, 200), [(80, 180), (150, 80), (220, 180)])

    # 2. 日出/日落天空背景
    elif sun_pos[0] != -50:
        sky_surface = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
        if current_hour < 12:
            sky_surface.fill(COLORS["sky_morning"])
        else:
            sky_surface.fill(COLORS["sky_evening"])
        screen.blit(sky_surface, (0, 0))

    # 3. 绘制太阳（根据时段切换颜色）
    if sun_pos[0] != -50:
        sun_color = COLORS["sun_morning"] if current_hour < 12 else COLORS["sun_evening"]
        pygame.draw.circle(screen, sun_color, (int(sun_pos[0]), int(sun_pos[1])), sun_radius)
        # 太阳光晕（更真实）
        glow_surface = pygame.Surface((sun_radius*4, sun_radius*4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*sun_color, 50), (sun_radius*2, sun_radius*2), sun_radius*2)
        screen.blit(glow_surface, (sun_pos[0]-sun_radius*2, sun_pos[1]-sun_radius*2))

    # 4. 绘制雨滴
    for rain in rain_list:
        pygame.draw.line(
            screen, COLORS["rain"],
            (rain[0], rain[1]),
            (rain[0], rain[1]+rain[2]),
            1
        )

    # 5. 绘制水潭（更圆润的椭圆+双层阴影）
    # 水潭阴影（底层）
    pygame.draw.ellipse(screen, (60, 160, 230, 150), (50, window_height-50, window_width-100, 40))
    # 水潭主体（上层）
    pygame.draw.ellipse(screen, COLORS["water"], (50, window_height-48, window_width-100, 35))

    # 6. 绘制水滴（带轻微透明度变化）
    for drop in drop_list:
        drop_surface = pygame.Surface((drop[2]*2, drop[2]*2), pygame.SRCALPHA)
        alpha = int(220 * (drop[4]/30))  # 生命周期越短越透明
        pygame.draw.circle(drop_surface, (*COLORS["drop"][:3], alpha), (drop[2], drop[2]), drop[2])
        screen.blit(drop_surface, (drop[0]-drop[2], drop[1]-drop[2]))

    # 更新屏幕
    pygame.display.update()
    clock.tick(60)  # 60帧更流畅

# 退出清理
pygame.quit()
sys.exit()