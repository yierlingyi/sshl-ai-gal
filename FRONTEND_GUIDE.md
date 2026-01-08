# 前端架构指南

本文档详细介绍了使用 PySide6 (Qt) 实现的前端部分。

## 1. 核心架构

前端围绕一个 `QMainWindow` (`main_window.py` 中的 `MainWindow`) 构建，它托管了一个 `QStackedWidget`。

### 页面系统 (`src/frontend/pages.py`)
*   **`MainMenuPage`**: 主菜单。
*   **`ConfigPage`**: 设置页面。包含 **3-API 分组设置** (Story, Summary, Logic)、音频、文本设置。
*   **`SaveLoadPage`**: 存读档页面。支持新版 JSON 存档结构（含元数据和完整游戏状态）。
*   **`GamePage`**: 游戏主界面。包含 `QGraphicsView` 和对话框。
*   **`MemoryPage`**: 记忆回顾页面。
*   **`EditorPage`**: **通用提示词编辑器 (Universal Prompt Editor)**。
    *   **Tab 1 (Resource Files)**: 文件树 + 文本编辑器，用于修改所有 `assets` 下的文本/JSON 资源。
    *   **Tab 2 (Prompt Sequences)**: 可视化排序编辑器，用于调整 `assets/prompts.json` 中的提示词组装顺序。

## 2. 视觉渲染 (`src/frontend/visual_manager.py`)

渲染由 `QGraphicsScene` 处理。
*   **图层**: 背景层 (双缓冲淡入淡出)、精灵层 (角色)。
*   **组合精灵**: 身体 + 表情。

## 3. 游戏引擎 (`src/frontend/game_engine.py`)

连接后端与前端的核心。
*   **指令解析**: 解析 `[Tag]` 指令。
    *   支持 `[StopBGM]`, `[StopSound]` 等新指令。
    *   支持 `[C]` 指令的非自动模式等待逻辑。
*   **系统消息**: 处理后端返回的 `[System Paused]` 等阻塞状态消息。

## 4. 音频系统 (`src/frontend/audio_manager.py`)

*   **BGM**: 双播放器交叉淡入淡出，**默认无限循环**。
*   **SFX**: 支持单次播放和循环播放。
*   **资源管理**: 播放前自动停止旧资源，防止死锁。使用绝对路径解决加载问题。

## 5. 关键流程

### 添加新的 UI 页面
1.  在 `pages.py` 中创建类 `NewPage(QWidget)`。
2.  在 `MainWindow.__init__` 中实例化它。
3.  添加到 `self.stack.addWidget(self.new_page)`.