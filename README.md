# 星落小游戏26 - 管道连接益智游戏

一款管道连接益智游戏，玩家通过滑动方块连接管道，在限定步数内从绿色起点连通到红色终点。共 60 个关卡，难度逐步递增。

## 运行方式

### 网页版
1. 直接浏览器打开 `index.html`，或
2. 运行 `start.bat`（通过 `npx serve` 启动本地服务器，访问 `http://localhost:3000`）

### Python 版
```bash
pip install -r "py与exe/py/requirements.txt"
python "py与exe/py/pipegame.py"
```

### 可执行文件
直接运行 `py与exe/exe/管道连接小游戏V1.2.exe`

## 游戏玩法

- 点击并拖动灰色方块来移动管道段
- 深灰色方块为固定障碍物，不可移动
- 目标：在步数限制内，从绿色起点连通到红色终点
- 每走一步会自动检测连通状态

## 操作说明

| 操作 | 方式 |
|------|------|
| 移动方块 | 点击拖动 |
| 后退一步 | 点击"后退一步"按钮 或 `Ctrl+Z` |
| 重置关卡 | 点击"重置关卡"按钮 或 `R` |
| 返回选关 | 点击"返回"按钮 或 `ESC` |

## 项目结构

```
xl_game26/
├── index.html          # 网页版入口
├── css/style.css       # 样式
├── js/
│   ├── app.js          # 网页版游戏逻辑 (Canvas 2D)
│   └── levels.js       # 60 个关卡数据
├── py与exe/
│   ├── py/
│   │   ├── pipegame.py     # Python/Pygame 版源码
│   │   ├── requirements.txt
│   │   └── fonts/          # 字体文件 (微软雅黑, 黑体)
│   └── exe/
│       └── 管道连接小游戏V1.2.exe  # 打包好的 Windows 可执行文件
└── start.bat           # 启动本地服务器
```

## 技术栈

- **网页版**：HTML5 Canvas + 原生 JavaScript（无外部依赖）
- **Python 版**：Pygame
