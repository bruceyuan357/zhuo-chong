# 🌊 水潭桌宠 (Desktop Water Pond Pet)

一个精美的桌面宠物应用，展示一个充满生机的水潭场景，包含动态天气效果、游鱼、荷叶等元素。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 特色功能

### 🎨 视觉效果
- **动态天空系统** - 根据实际时间自动切换：黎明、早晨、正午、下午、黄昏、夜晚
- **太阳轨迹** - 模拟真实的太阳升落，采用正弦曲线运动
- **月亮与星星** - 夜间显示闪烁的星空和月牙月亮
- **日照金山彩蛋** - 连续运行3天后解锁金山景观
- **水波纹效果** - 逼真的椭圆形水波扩散动画

### 🐟 互动元素
- **游鱼系统** - 水中有小鱼游动，偶尔跃出水面
- **荷叶摇摆** - 水面上漂浮着轻轻摇摆的荷叶
- **水滴跃动** - 按键触发水滴飞溅，带物理重力效果
- **下雨效果** - 非白天时段随机下雨，雨滴落入水面产生波纹

### 🖱️ 交互控制
- **窗口拖动** - 左键按住拖动窗口到任意位置
- **水滴溅起** - 按任意键产生水滴跃动
- **大量水花** - 按空格键产生大量水花
- **手动下雨** - 按 R 键触发下雨
- **点击波纹** - 右键点击水面产生波纹
- **退出程序** - 按 ESC 键退出

## 🚀 快速开始

### 环境要求
- Python 3.8+
- pygame 2.0+

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/richer-richard/zhuo-chong.git
   cd zhuo-chong
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行程序**
   ```bash
   python 桌宠.py
   ```

### 一键运行
```bash
pip install pygame && python 桌宠.py
```

## 🎮 操作指南

| 操作 | 效果 |
|------|------|
| 左键拖动 | 移动窗口位置 |
| 任意键 | 溅起一滴水 |
| 空格键 | 溅起大量水花 |
| R 键 | 触发下雨效果 |
| 右键点击水面 | 产生波纹和水滴 |
| ESC | 退出程序 |

## 🏗️ 项目结构

```
zhuo-chong/
├── 桌宠.py           # 主程序文件
├── requirements.txt  # 依赖清单
├── README.md         # 项目说明
└── LICENSE           # 开源协议
```

## 📐 技术架构

项目采用面向对象设计，主要包含以下组件：

- **Config** - 游戏配置（窗口大小、FPS、各种参数）
- **ColorTheme** - 颜色主题定义
- **游戏对象** - WaterDrop、RainDrop、Ripple、Fish、LotusLeaf、Star
- **GameState** - 游戏状态管理器
- **Renderer** - 渲染器（负责所有绘制逻辑）
- **DesktopPet** - 主程序类（事件处理、主循环）

## 🎯 彩蛋

- 🏔️ **日照金山**：连续运行程序满 3 天，将解锁日照金山彩蛋场景！

## ⚙️ 自定义配置

可以通过修改 `Config` 类来自定义游戏参数：

```python
@dataclass(frozen=True)
class Config:
    WINDOW_WIDTH: int = 320      # 窗口宽度
    WINDOW_HEIGHT: int = 320     # 窗口高度
    FPS: int = 60                # 帧率
    SUN_RISE_HOUR: int = 6       # 日出时间
    SUN_SET_HOUR: int = 18       # 日落时间
    FISH_COUNT: int = 2          # 鱼的数量
    # ... 更多配置
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📜 开源协议

本项目基于 MIT 协议开源，详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- 原作者：[bruceyuan357](https://github.com/bruceyuan357)
- 感谢所有贡献者的支持

---

⭐ 如果你喜欢这个项目，请给它一个 Star！
