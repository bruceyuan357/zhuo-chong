"""
水潭桌宠 - Desktop Water Pond Pet
A beautiful and interactive desktop pet featuring a water pond with dynamic effects.
"""

from __future__ import annotations

import sys
import time
import random
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

try:
    import pygame  # type: ignore[import-untyped]
except ImportError:
    print("错误: 请先安装 pygame 库")
    print("运行: pip install pygame")
    sys.exit(1)


# ===================== 配置常量 =====================
@dataclass(frozen=True)
class Config:
    """游戏配置"""
    WINDOW_WIDTH: int = 320
    WINDOW_HEIGHT: int = 320
    FPS: int = 60
    
    # 太阳配置
    SUN_RISE_HOUR: int = 6
    SUN_SET_HOUR: int = 18
    SUN_RADIUS: int = 28
    
    # 水滴配置
    DROP_MIN_SIZE: int = 4
    DROP_MAX_SIZE: int = 10
    DROP_INITIAL_VELOCITY: float = -7.0
    DROP_GRAVITY: float = 0.25
    DROP_LIFETIME: int = 40
    
    # 雨滴配置
    RAIN_PROBABILITY: int = 25  # 1/N 的概率
    RAIN_MIN_LENGTH: int = 8
    RAIN_MAX_LENGTH: int = 18
    RAIN_MIN_SPEED: int = 4
    RAIN_MAX_SPEED: int = 8
    
    # 波纹配置
    RIPPLE_PROBABILITY: int = 60
    RIPPLE_MAX_RADIUS: int = 30
    RIPPLE_EXPAND_SPEED: float = 0.8
    
    # 鱼配置
    FISH_COUNT: int = 2
    FISH_PROBABILITY: int = 200  # 1/N 的概率跳出水面
    
    # 彩蛋天数
    EASTER_EGG_DAYS: int = 3


# ===================== 颜色主题 =====================
@dataclass(frozen=True)
class ColorTheme:
    """颜色主题配置"""
    # 水相关
    water_main: Tuple[int, int, int, int] = (70, 170, 255, 200)
    water_shadow: Tuple[int, int, int, int] = (50, 140, 220, 160)
    water_highlight: Tuple[int, int, int, int] = (180, 230, 255, 120)
    drop: Tuple[int, int, int, int] = (150, 220, 255, 230)
    rain: Tuple[int, int, int, int] = (200, 235, 255, 180)
    ripple: Tuple[int, int, int, int] = (200, 240, 255, 150)
    
    # 天空相关
    sky_dawn: Tuple[int, int, int, int] = (255, 200, 150, 100)
    sky_morning: Tuple[int, int, int, int] = (180, 220, 255, 90)
    sky_noon: Tuple[int, int, int, int] = (135, 206, 250, 70)
    sky_evening: Tuple[int, int, int, int] = (255, 180, 140, 100)
    sky_dusk: Tuple[int, int, int, int] = (255, 140, 100, 110)
    sky_night: Tuple[int, int, int, int] = (30, 50, 80, 120)
    
    # 太阳/月亮
    sun_morning: Tuple[int, int, int] = (255, 240, 130)
    sun_noon: Tuple[int, int, int] = (255, 255, 200)
    sun_evening: Tuple[int, int, int] = (255, 160, 90)
    moon: Tuple[int, int, int, int] = (240, 240, 255, 200)
    star: Tuple[int, int, int, int] = (255, 255, 255, 180)
    
    # 山/景观
    mountain_front: Tuple[int, int, int, int] = (220, 200, 130, 220)
    mountain_back: Tuple[int, int, int, int] = (180, 160, 100, 200)
    
    # 鱼
    fish_body: Tuple[int, int, int, int] = (255, 180, 100, 220)
    fish_tail: Tuple[int, int, int, int] = (255, 150, 80, 200)
    
    # 荷叶
    lotus_leaf: Tuple[int, int, int, int] = (80, 180, 100, 180)
    lotus_flower: Tuple[int, int, int, int] = (255, 180, 200, 220)


COLORS = ColorTheme()
CONFIG = Config()


# ===================== 游戏对象 =====================
@dataclass
class WaterDrop:
    """水滴对象"""
    x: float
    y: float
    size: int
    velocity_y: float
    lifetime: int
    
    def update(self) -> bool:
        """更新水滴状态，返回是否仍然存活"""
        self.y += self.velocity_y
        self.velocity_y += CONFIG.DROP_GRAVITY
        self.lifetime -= 1
        return self.lifetime > 0 and self.y < CONFIG.WINDOW_HEIGHT - 30


@dataclass
class RainDrop:
    """雨滴对象"""
    x: float
    y: float
    length: int
    speed: int
    
    def update(self) -> bool:
        """更新雨滴状态，返回是否仍然存活"""
        self.y += self.speed
        return self.y < CONFIG.WINDOW_HEIGHT


@dataclass
class Ripple:
    """水波纹对象"""
    x: float
    y: float
    radius: float = 2.0
    max_radius: float = field(default_factory=lambda: float(CONFIG.RIPPLE_MAX_RADIUS))
    alpha: int = 200
    
    def update(self) -> bool:
        """更新波纹状态，返回是否仍然存活"""
        self.radius += CONFIG.RIPPLE_EXPAND_SPEED
        self.alpha = max(0, int(200 * (1 - self.radius / self.max_radius)))
        return self.radius < self.max_radius


@dataclass
class Fish:
    """鱼对象"""
    x: float
    y: float
    size: int = 12
    direction: int = 1  # 1 = 右, -1 = 左
    swimming: bool = True
    jumping: bool = False
    jump_velocity: float = 0.0
    base_y: float = 0.0
    swim_offset: float = 0.0
    
    def __post_init__(self) -> None:
        self.base_y = self.y
        self.swim_offset = random.random() * math.pi * 2
    
    def update(self) -> None:
        """更新鱼的状态"""
        if self.jumping:
            self.y += self.jump_velocity
            self.jump_velocity += 0.3
            if self.y >= self.base_y:
                self.y = self.base_y
                self.jumping = False
                self.swimming = True
        else:
            # 游泳时的小幅摆动
            self.swim_offset += 0.05
            self.x += 0.3 * self.direction
            self.y = self.base_y + math.sin(self.swim_offset) * 3
            
            # 边界检测
            if self.x < 60 or self.x > CONFIG.WINDOW_WIDTH - 60:
                self.direction *= -1
            
            # 随机跳跃
            if random.randint(0, CONFIG.FISH_PROBABILITY) == 0:
                self.jumping = True
                self.swimming = False
                self.jump_velocity = -6.0


@dataclass
class LotusLeaf:
    """荷叶对象"""
    x: float
    y: float
    size: int
    wobble_offset: float = 0.0
    
    def update(self) -> None:
        """更新荷叶状态（轻微摇摆）"""
        self.wobble_offset += 0.02
        

@dataclass  
class Star:
    """星星对象"""
    x: float
    y: float
    size: int
    twinkle_offset: float = 0.0
    
    def update(self) -> None:
        """更新星星闪烁"""
        self.twinkle_offset += 0.08


# ===================== 游戏状态管理 =====================
class GameState:
    """游戏状态管理器"""
    
    def __init__(self) -> None:
        self.start_time: float = time.time()
        self.run_days: int = 0
        self.mountain_show: bool = False
        
        # 窗口拖动状态
        self.is_dragging: bool = False
        self.drag_offset_x: int = 0
        self.drag_offset_y: int = 0
        
        # 游戏对象列表
        self.drops: List[WaterDrop] = []
        self.rain: List[RainDrop] = []
        self.ripples: List[Ripple] = []
        self.fish: List[Fish] = []
        self.lotus_leaves: List[LotusLeaf] = []
        self.stars: List[Star] = []
        
        # 初始化游戏对象
        self._init_objects()
    
    def _init_objects(self) -> None:
        """初始化游戏对象"""
        # 创建鱼
        for _ in range(CONFIG.FISH_COUNT):
            self.fish.append(Fish(
                x=random.randint(80, CONFIG.WINDOW_WIDTH - 80),
                y=CONFIG.WINDOW_HEIGHT - 42,
                size=random.randint(10, 14),
                direction=random.choice([-1, 1])
            ))
        
        # 创建荷叶
        self.lotus_leaves = [
            LotusLeaf(x=70, y=CONFIG.WINDOW_HEIGHT - 55, size=25),
            LotusLeaf(x=CONFIG.WINDOW_WIDTH - 90, y=CONFIG.WINDOW_HEIGHT - 50, size=20),
        ]
        
        # 创建星星（夜间显示）
        for _ in range(15):
            self.stars.append(Star(
                x=random.randint(10, CONFIG.WINDOW_WIDTH - 10),
                y=random.randint(10, CONFIG.WINDOW_HEIGHT // 2),
                size=random.randint(1, 3),
                twinkle_offset=random.random() * math.pi * 2
            ))
    
    def update_run_days(self) -> None:
        """更新运行天数"""
        delta = time.time() - self.start_time
        self.run_days = int(delta // (24 * 60 * 60))
        self.mountain_show = self.run_days >= CONFIG.EASTER_EGG_DAYS
    
    def spawn_drop(self, x: Optional[int] = None) -> None:
        """生成水滴"""
        if x is None:
            x = random.randint(70, CONFIG.WINDOW_WIDTH - 70)
        drop = WaterDrop(
            x=float(x),
            y=float(CONFIG.WINDOW_HEIGHT - 45),
            size=random.randint(CONFIG.DROP_MIN_SIZE, CONFIG.DROP_MAX_SIZE),
            velocity_y=CONFIG.DROP_INITIAL_VELOCITY + random.uniform(-1, 1),
            lifetime=CONFIG.DROP_LIFETIME
        )
        self.drops.append(drop)
    
    def spawn_rain(self) -> None:
        """生成雨滴"""
        rain = RainDrop(
            x=float(random.randint(0, CONFIG.WINDOW_WIDTH)),
            y=0.0,
            length=random.randint(CONFIG.RAIN_MIN_LENGTH, CONFIG.RAIN_MAX_LENGTH),
            speed=random.randint(CONFIG.RAIN_MIN_SPEED, CONFIG.RAIN_MAX_SPEED)
        )
        self.rain.append(rain)
    
    def spawn_ripple(self, x: Optional[float] = None, y: Optional[float] = None) -> None:
        """生成水波纹"""
        if x is None:
            x = random.randint(60, CONFIG.WINDOW_WIDTH - 60)
        if y is None:
            y = CONFIG.WINDOW_HEIGHT - 38
        ripple = Ripple(
            x=float(x),
            y=float(y),
            max_radius=float(random.randint(15, CONFIG.RIPPLE_MAX_RADIUS))
        )
        self.ripples.append(ripple)
    
    def update_all(self) -> None:
        """更新所有游戏对象"""
        # 更新运行天数
        self.update_run_days()
        
        # 更新水滴
        self.drops = [d for d in self.drops if d.update()]
        
        # 更新雨滴，雨滴落入水中产生波纹
        new_rain = []
        for rain in self.rain:
            if rain.update():
                new_rain.append(rain)
            elif rain.y >= CONFIG.WINDOW_HEIGHT - 45:
                self.spawn_ripple(rain.x, CONFIG.WINDOW_HEIGHT - 38)
        self.rain = new_rain
        
        # 更新波纹
        self.ripples = [r for r in self.ripples if r.update()]
        
        # 更新鱼
        for fish in self.fish:
            fish.update()
        
        # 更新荷叶
        for leaf in self.lotus_leaves:
            leaf.update()
        
        # 更新星星
        for star in self.stars:
            star.update()


# ===================== 渲染器 =====================
class Renderer:
    """游戏渲染器"""
    
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
    
    @staticmethod
    def get_time_of_day() -> Tuple[int, str]:
        """获取当前时间段"""
        hour = datetime.now().hour
        if 5 <= hour < 7:
            return hour, "dawn"
        elif 7 <= hour < 11:
            return hour, "morning"
        elif 11 <= hour < 14:
            return hour, "noon"
        elif 14 <= hour < 17:
            return hour, "afternoon"
        elif 17 <= hour < 19:
            return hour, "evening"
        elif 19 <= hour < 21:
            return hour, "dusk"
        else:
            return hour, "night"
    
    def get_sky_color(self, time_period: str) -> Tuple[int, int, int, int]:
        """根据时间段获取天空颜色"""
        sky_colors = {
            "dawn": COLORS.sky_dawn,
            "morning": COLORS.sky_morning,
            "noon": COLORS.sky_noon,
            "afternoon": COLORS.sky_morning,
            "evening": COLORS.sky_evening,
            "dusk": COLORS.sky_dusk,
            "night": COLORS.sky_night,
        }
        return sky_colors.get(time_period, COLORS.sky_noon)
    
    def calc_sun_position(self, hour: int) -> Tuple[float, float]:
        """计算太阳位置"""
        if CONFIG.SUN_RISE_HOUR <= hour <= CONFIG.SUN_SET_HOUR:
            # 计算在日出到日落之间的比例
            total_hours = CONFIG.SUN_SET_HOUR - CONFIG.SUN_RISE_HOUR
            elapsed = hour - CONFIG.SUN_RISE_HOUR
            ratio = elapsed / total_hours
            
            # 使用正弦曲线模拟太阳轨迹
            x = CONFIG.WINDOW_WIDTH // 2
            # 日出时y=220, 正午时y=60, 日落时y=220
            y = 220 - 160 * math.sin(ratio * math.pi)
            return (float(x), y)
        return (-50.0, -50.0)
    
    def draw_sky(self, time_period: str) -> None:
        """绘制天空背景"""
        sky_color = self.get_sky_color(time_period)
        sky_surface = pygame.Surface(
            (CONFIG.WINDOW_WIDTH, CONFIG.WINDOW_HEIGHT), 
            pygame.SRCALPHA
        )
        sky_surface.fill(sky_color)
        self.screen.blit(sky_surface, (0, 0))
    
    def draw_stars(self, stars: List[Star], time_period: str) -> None:
        """绘制星星（夜间）"""
        if time_period not in ("night", "dusk", "dawn"):
            return
        
        for star in stars:
            # 闪烁效果
            brightness = int(150 + 50 * math.sin(star.twinkle_offset))
            alpha = min(255, brightness) if time_period == "night" else brightness // 2
            color = (255, 255, 255, alpha)
            
            star_surface = pygame.Surface((star.size * 2, star.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(star_surface, color, (star.size, star.size), star.size)
            self.screen.blit(star_surface, (int(star.x - star.size), int(star.y - star.size)))
    
    def draw_moon(self, hour: int) -> None:
        """绘制月亮"""
        if 21 <= hour or hour < 5:
            # 月亮在夜间显示
            moon_x = CONFIG.WINDOW_WIDTH - 70
            moon_y = 60
            
            # 月亮光晕
            glow_surface = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (240, 240, 255, 30), (40, 40), 40)
            pygame.draw.circle(glow_surface, (240, 240, 255, 50), (40, 40), 30)
            self.screen.blit(glow_surface, (moon_x - 40, moon_y - 40))
            
            # 月亮主体
            pygame.draw.circle(self.screen, COLORS.moon, (moon_x, moon_y), 20)
            # 月亮阴影（月牙效果）
            pygame.draw.circle(self.screen, (200, 200, 230, 150), (moon_x + 8, moon_y - 3), 16)
    
    def draw_sun(self, sun_pos: Tuple[float, float], time_period: str) -> None:
        """绘制太阳"""
        if sun_pos[0] < 0:
            return
        
        # 根据时间选择太阳颜色
        if time_period in ("dawn", "morning"):
            sun_color = COLORS.sun_morning
        elif time_period == "noon":
            sun_color = COLORS.sun_noon
        else:
            sun_color = COLORS.sun_evening
        
        x, y = int(sun_pos[0]), int(sun_pos[1])
        
        # 太阳光晕（多层渐变）
        for i in range(3, 0, -1):
            glow_radius = CONFIG.SUN_RADIUS + i * 15
            glow_alpha = 20 + i * 10
            glow_surface = pygame.Surface(
                (glow_radius * 2, glow_radius * 2), 
                pygame.SRCALPHA
            )
            pygame.draw.circle(
                glow_surface, 
                (*sun_color, glow_alpha), 
                (glow_radius, glow_radius), 
                glow_radius
            )
            self.screen.blit(glow_surface, (x - glow_radius, y - glow_radius))
        
        # 太阳主体
        pygame.draw.circle(self.screen, sun_color, (x, y), CONFIG.SUN_RADIUS)
    
    def draw_mountains(self) -> None:
        """绘制日照金山彩蛋"""
        # 后层山
        pygame.draw.polygon(
            self.screen, 
            COLORS.mountain_back, 
            [(30, 220), (160, 80), (290, 220)]
        )
        # 前层山
        pygame.draw.polygon(
            self.screen, 
            COLORS.mountain_front, 
            [(70, 200), (160, 100), (250, 200)]
        )
        # 山顶光芒
        pygame.draw.polygon(
            self.screen, 
            (255, 240, 180, 150), 
            [(140, 105), (160, 80), (180, 105)]
        )
    
    def draw_pond(self) -> None:
        """绘制水潭"""
        pond_rect = (45, CONFIG.WINDOW_HEIGHT - 55, CONFIG.WINDOW_WIDTH - 90, 45)
        
        # 水潭阴影
        shadow_rect = (48, CONFIG.WINDOW_HEIGHT - 52, CONFIG.WINDOW_WIDTH - 96, 42)
        pygame.draw.ellipse(self.screen, COLORS.water_shadow, shadow_rect)
        
        # 水潭主体
        pygame.draw.ellipse(self.screen, COLORS.water_main, pond_rect)
        
        # 水潭高光
        highlight_rect = (70, CONFIG.WINDOW_HEIGHT - 52, CONFIG.WINDOW_WIDTH - 140, 15)
        highlight_surface = pygame.Surface(
            (CONFIG.WINDOW_WIDTH - 140, 15), 
            pygame.SRCALPHA
        )
        pygame.draw.ellipse(highlight_surface, COLORS.water_highlight, 
                          (0, 0, CONFIG.WINDOW_WIDTH - 140, 15))
        self.screen.blit(highlight_surface, (70, CONFIG.WINDOW_HEIGHT - 52))
    
    def draw_lotus_leaves(self, leaves: List[LotusLeaf]) -> None:
        """绘制荷叶"""
        for leaf in leaves:
            # 荷叶摇摆效果
            wobble = math.sin(leaf.wobble_offset) * 2
            
            leaf_surface = pygame.Surface((leaf.size * 2, leaf.size), pygame.SRCALPHA)
            pygame.draw.ellipse(
                leaf_surface, 
                COLORS.lotus_leaf, 
                (0, 0, leaf.size * 2, leaf.size)
            )
            # 荷叶纹理（简单线条）
            pygame.draw.line(
                leaf_surface, 
                (60, 150, 80, 150),
                (leaf.size, 0), 
                (leaf.size, leaf.size),
                1
            )
            self.screen.blit(leaf_surface, (int(leaf.x - leaf.size + wobble), int(leaf.y)))
    
    def draw_fish(self, fish_list: List[Fish]) -> None:
        """绘制鱼"""
        for fish in fish_list:
            # 鱼身体
            fish_surface = pygame.Surface((fish.size * 2, fish.size), pygame.SRCALPHA)
            
            # 鱼身（椭圆）
            pygame.draw.ellipse(
                fish_surface, 
                COLORS.fish_body,
                (0, 0, fish.size * 1.5, fish.size)
            )
            
            # 鱼尾（三角形）
            if fish.direction > 0:
                tail_points = [
                    (0, fish.size // 2),
                    (fish.size // 3, 0),
                    (fish.size // 3, fish.size)
                ]
            else:
                tail_points = [
                    (fish.size * 1.5, fish.size // 2),
                    (fish.size * 1.2, 0),
                    (fish.size * 1.2, fish.size)
                ]
            pygame.draw.polygon(fish_surface, COLORS.fish_tail, tail_points)
            
            # 鱼眼
            eye_x = fish.size if fish.direction > 0 else fish.size // 2
            pygame.draw.circle(fish_surface, (0, 0, 0, 200), (eye_x, fish.size // 3), 2)
            
            self.screen.blit(
                fish_surface, 
                (int(fish.x - fish.size), int(fish.y - fish.size // 2))
            )
    
    def draw_ripples(self, ripples: List[Ripple]) -> None:
        """绘制水波纹"""
        for ripple in ripples:
            if ripple.alpha > 0:
                ripple_surface = pygame.Surface(
                    (int(ripple.radius * 2) + 4, int(ripple.radius) + 2), 
                    pygame.SRCALPHA
                )
                pygame.draw.ellipse(
                    ripple_surface,
                    (*COLORS.ripple[:3], ripple.alpha),
                    (0, 0, int(ripple.radius * 2), int(ripple.radius * 0.5)),
                    1
                )
                self.screen.blit(
                    ripple_surface,
                    (int(ripple.x - ripple.radius), int(ripple.y - ripple.radius * 0.25))
                )
    
    def draw_rain(self, rain_list: List[RainDrop]) -> None:
        """绘制雨滴"""
        for rain in rain_list:
            pygame.draw.line(
                self.screen,
                COLORS.rain,
                (int(rain.x), int(rain.y)),
                (int(rain.x), int(rain.y + rain.length)),
                1
            )
    
    def draw_drops(self, drops: List[WaterDrop]) -> None:
        """绘制水滴"""
        for drop in drops:
            # 根据生命周期计算透明度
            alpha = int(230 * (drop.lifetime / CONFIG.DROP_LIFETIME))
            drop_surface = pygame.Surface((drop.size * 2, drop.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                drop_surface,
                (*COLORS.drop[:3], alpha),
                (drop.size, drop.size),
                drop.size
            )
            self.screen.blit(drop_surface, (int(drop.x - drop.size), int(drop.y - drop.size)))
    
    def draw_tooltip(self, text: str) -> None:
        """绘制提示文字"""
        try:
            font = pygame.font.SysFont("PingFang SC", 14)
        except Exception:
            font = pygame.font.Font(None, 14)
        
        text_surface = font.render(text, True, (255, 255, 255, 200))
        text_rect = text_surface.get_rect(center=(CONFIG.WINDOW_WIDTH // 2, 20))
        self.screen.blit(text_surface, text_rect)


# ===================== 主游戏类 =====================
class DesktopPet:
    """桌宠主程序"""
    
    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()
        
        # 创建窗口
        self.screen = pygame.display.set_mode(
            (CONFIG.WINDOW_WIDTH, CONFIG.WINDOW_HEIGHT),
            pygame.NOFRAME | pygame.SRCALPHA | pygame.HWSURFACE
        )
        pygame.display.set_caption("水潭桌宠")
        
        # 初始化窗口位置
        screen_info = pygame.display.Info()
        self.win_x = (screen_info.current_w - CONFIG.WINDOW_WIDTH) // 2
        self.win_y = (screen_info.current_h - CONFIG.WINDOW_HEIGHT) // 2
        self._set_window_position(self.win_x, self.win_y)
        
        # 初始化游戏组件
        self.clock = pygame.time.Clock()
        self.state = GameState()
        self.renderer = Renderer(self.screen)
        self.running = True
        self.show_help = True
        self.help_timer = 180  # 显示帮助3秒（60fps * 3）
    
    def _set_window_position(self, x: int, y: int) -> None:
        """设置窗口位置（跨平台兼容）"""
        try:
            # pygame 2.0+ 方法
            pygame.display.set_window_position((x, y))  # type: ignore[attr-defined]
        except AttributeError:
            # 旧版本或不支持的平台
            import os
            os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},{y}"
    
    def handle_events(self) -> None:
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    # 空格键：生成多个水滴
                    for _ in range(random.randint(3, 6)):
                        self.state.spawn_drop()
                elif event.key == pygame.K_r:
                    # R键：触发下雨
                    for _ in range(20):
                        self.state.spawn_rain()
                else:
                    # 其他按键：生成单个水滴
                    self.state.spawn_drop()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    self.state.is_dragging = True
                    self.state.drag_offset_x = event.pos[0]
                    self.state.drag_offset_y = event.pos[1]
                elif event.button == 3:  # 右键
                    # 右键点击水面产生波纹
                    mouse_x, mouse_y = event.pos
                    if CONFIG.WINDOW_HEIGHT - 60 < mouse_y < CONFIG.WINDOW_HEIGHT - 20:
                        self.state.spawn_ripple(float(mouse_x), CONFIG.WINDOW_HEIGHT - 38)
                        self.state.spawn_drop(mouse_x)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.state.is_dragging = False
            
            elif event.type == pygame.MOUSEMOTION:
                if self.state.is_dragging:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    self.win_x += mouse_x - self.state.drag_offset_x
                    self.win_y += mouse_y - self.state.drag_offset_y
                    self._set_window_position(self.win_x, self.win_y)
    
    def update(self) -> None:
        """更新游戏状态"""
        # 更新所有游戏对象
        self.state.update_all()
        
        # 获取当前时间
        hour, time_period = self.renderer.get_time_of_day()
        sun_pos = self.renderer.calc_sun_position(hour)
        
        # 非白天时随机下雨
        if sun_pos[0] < 0 and random.randint(0, CONFIG.RAIN_PROBABILITY) == 0:
            self.state.spawn_rain()
        
        # 随机生成波纹
        if random.randint(0, CONFIG.RIPPLE_PROBABILITY) == 0:
            self.state.spawn_ripple()
        
        # 更新帮助提示计时器
        if self.help_timer > 0:
            self.help_timer -= 1
        else:
            self.show_help = False
    
    def render(self) -> None:
        """渲染画面"""
        # 清空屏幕
        self.screen.fill((0, 0, 0, 0))
        
        # 获取时间信息
        hour, time_period = self.renderer.get_time_of_day()
        sun_pos = self.renderer.calc_sun_position(hour)
        
        # 绘制天空
        self.renderer.draw_sky(time_period)
        
        # 绘制星星（夜间）
        self.renderer.draw_stars(self.state.stars, time_period)
        
        # 绘制月亮（夜间）
        self.renderer.draw_moon(hour)
        
        # 绘制太阳
        self.renderer.draw_sun(sun_pos, time_period)
        
        # 日照金山彩蛋
        if self.state.mountain_show:
            self.renderer.draw_mountains()
        
        # 绘制雨滴
        self.renderer.draw_rain(self.state.rain)
        
        # 绘制荷叶
        self.renderer.draw_lotus_leaves(self.state.lotus_leaves)
        
        # 绘制水潭
        self.renderer.draw_pond()
        
        # 绘制鱼
        self.renderer.draw_fish(self.state.fish)
        
        # 绘制波纹
        self.renderer.draw_ripples(self.state.ripples)
        
        # 绘制水滴
        self.renderer.draw_drops(self.state.drops)
        
        # 显示帮助提示
        if self.show_help:
            self.renderer.draw_tooltip("按任意键溅水 | 空格键大溅 | R键下雨 | ESC退出")
        
        # 更新显示
        pygame.display.update()
    
    def run(self) -> None:
        """运行主循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(CONFIG.FPS)
        
        pygame.quit()
        sys.exit()


# ===================== 程序入口 =====================
def main() -> None:
    """程序入口"""
    pet = DesktopPet()
    pet.run()


if __name__ == "__main__":
    main()
