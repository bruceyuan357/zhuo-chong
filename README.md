# 栖水 · 水潭桌宠

留一点宁静，也做一点小事。一个完全离线的 Python 桌面陪伴：看游鱼、记小事、专注一刻，再好好休息。

## 这次有什么不同

- **一方小庭院**：原创水潭插画、游动锦鲤、点击喂鱼与右键水花。日间、晨昏、夜色跟随本机时间，也可手动选择光景与细雨。
- **专注与休息**：25 / 45 / 60 分钟专注，5 分钟休息。支持暂停、继续与重新计时；完成后手动开始下一阶段，不会自动连跑。
- **随手记**：中文输入、输入法组合文字和粘贴；添加、完成、恢复、移除，最多 50 件、每件 80 字。超过两行可用滚轮或 Page Up / Page Down 浏览，再用 Tab 逐项操作。
- **小小的正反馈**：今日已完成的专注分钟与次数；累计完成 3 段专注，解锁水潭的金色萤光。
- **迷你陪伴**：按 C 收起到 320 × 286 的小窗，保留计时与水潭互动；展开后待办仍在。
- **轻轻提醒**：运行满 45 分钟时在水潭内提醒喝水与远眺；可选轻声提示和减少动态。提醒仅在应用运行时生效，无系统推送。
- **本机存档**：保存待办、设置、今日记录与剩余计时。退出后重开保持暂停；不会把离线时间算成专注。存档损坏会先备份，保存采用临时文件加原子替换。

## 启动

需要 Python 3.9+ 和带图形桌面的系统。新环境建议使用 Python 3.11 或 3.13；Python 3.14 需要已有可用的 pygame 构建。当前在 macOS / Python 3.14 / pygame 2.6.1 上进行过原生窗口验证；Windows 与 Linux 仍需实机验证。

```bash
git clone https://github.com/bruceyuan357/zhuo-chong.git
cd zhuo-chong
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python 桌宠.py
```

macOS 安装依赖后，也可以双击 `启动栖水.command` 启动。

Windows 激活虚拟环境使用 `.venv\Scripts\activate`。Linux 请安装一个中文字体，例如 Noto Sans CJK，避免中文显示为方框。

也可以作为本地软件包安装，安装后在任意目录启动：

```bash
python -m pip install .
zhuo-chong
```

## 操作

| 操作 | 功能 |
| --- | --- |
| 拖动顶部 | 移动窗口；窗口具有独立的最小化与关闭按钮 |
| 点击水面 / 右键水面 | 喂鱼 / 产生水花 |
| 空格 | 开始或暂停当前专注、休息 |
| N / Enter | 输入小事 / 保存小事；编辑时空格正常输入 |
| Cmd+V / Ctrl+V | 在输入框中粘贴文字 |
| R / C | 切换细雨 / 展开或收起迷你模式 |
| H / F1 | 打开操作指南 |
| Page Up / Page Down | 查看上一页 / 下一页待办 |
| Tab / Shift+Tab / Enter | 移动焦点 / 反向移动 / 操作焦点控件 |
| Esc | 关闭设置或指南、离开输入框；再次按下保存并退出 |

计时运行时，先暂停再切换时长或重置，避免误触丢失进度。左侧专注和休息标签可手动切换。

## 存档与隐私

应用无需账号，不请求网络，不收集遥测。默认存档目录：

- macOS：`~/Library/Application Support/PondPet/state.json`
- Windows：`%APPDATA%/PondPet/state.json`
- Linux：`$XDG_STATE_HOME/pondpet/state.json`，默认 `~/.local/state/pondpet/state.json`

可用 `--data-dir PATH` 或 `PONDPET_DATA_DIR` 指定独立存档目录。剪贴板仅在输入框内主动执行粘贴时读取。

这仍是 pygame 绘制的普通浮动窗口，不支持跨平台的逐像素透明、点击穿透或保证置顶。键盘可操作核心功能，但绘制控件尚未暴露原生屏幕阅读器语义。

## 开发与验证

```bash
python -m unittest discover -s tests -v
python -m pip install ruff
python -m ruff check .
```

无显示环境可检查绘制与打包资源：

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python 桌宠.py --frames 3 --data-dir /tmp/pondpet-check --screenshot /tmp/pondpet-check.png
```

核心逻辑与渲染分离：`pondpet/model.py` 负责计时与待办，`storage.py` 负责存档，`app.py` 负责交互，`scene.py` 负责庭院，`ui.py` 负责控件与字体。原有 `python 桌宠.py` 启动方式继续可用。

[查看本次设计复核与实际截图](docs/REVIEW.md)。[插画提示词与图标来源](pondpet/assets/README.md)。

## 协议

代码遵循仓库原有 [Apache License 2.0](LICENSE)。Lucide 图标保留其独立的 [ISC / MIT 许可证](pondpet/assets/icons/LICENSE)。
