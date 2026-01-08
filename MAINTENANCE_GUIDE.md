# LLM-Galgame-Engine 维护与架构指南

## 1. 总体架构
本项目采用 **前后端分离的异步架构**：
*   **后端 (Core)**: 处理逻辑、记忆管理、API 调用、剧情规划。使用 `asyncio` 驱动。
*   **前端 (GUI)**: 处理渲染、动画、音频播放、用户交互。使用 `PySide6 (Qt)`，通过 `qasync` 与后端异步桥接。

## 2. 目录结构与文件详情

### 根目录
*   `main.py`: 后端逻辑测试入口。
*   `scan_backgrounds.py`: 扫描 `assets/bg` 并更新 `background_map.json`。
*   `scan_characters.py`: 扫描 `assets/fg` 并更新 `character_map.json`。
*   `scan_sounds.py`: 扫描 `assets/sound` 并更新 `sound_map.json` (处理 GBK 编码说明文件)。
*   `config.json`: 存储 API 密钥、音量、字体、流速等用户配置。

### `src/` (核心代码)
*   `infrastructure.py`: API 客户端、存档读写、工具类。
*   `memory_manager.py`: 核心记忆系统（短期对话、中期小总结、长期大总结）。
*   `plot_planner.py`: AI-3 架构师逻辑，负责宏观剧情规划。
*   `prompt_assembler.py`: 动态组装复杂的 System Prompt。
*   `llm_chain.py`: 连接 Storyteller 和 Director 的工作流流水线。

### `src/frontend/` (图形界面)
*   `main_window.py`: 主窗口容器，管理页面切换 (`QStackedWidget`) 和全局设置。
*   `game_engine.py`: **核心驱动器**。负责顺序解析 AI 输出的文本与标签，管理打字机效果、流控 (`[r]`, `[C]`) 及音效计时。
*   `visual_manager.py`: 视觉演播器。实现背景双缓冲淡入淡出、立绘层级管理、动画逻辑。
*   `audio_manager.py`: 音频管理器。支持 BGM 交叉淡入淡出、单次音效播放、循环环境音播放。
*   `pages.py`: 各个 UI 页面（主菜单、设置、存读档、游戏主界面、调试台）。

### `assets/` (资源与配置)
*   `bg/`, `bgm/`, `fg/`, `sound/`, `fonts/`: 原始素材库。
*   `*_map.json`: 索引素材的 key 与实际文件路径的映射表。
*   `提示词/`: 存储各个 AI 智体的 Prompt 模板。

## 3. 指令系统汇总 (Tags)

### 3.1 视觉指令
*   `[Join-角色名-位置]` / `[Leave-角色名]`: 角色登场与退场。
*   `[fg-角色名-表情]`: 切换立绘表情。
*   `[Sprite-角色名-预设]`: 移动或缩放角色。
*   `[Background-背景名]`: 切换场景背景。

### 3.2 音频指令
*   `[Music-曲名]`: 播放 BGM（自动淡入淡出）。
*   `[sound-音效名-持续时间]`: 播放音效。`0` 为单次，`>0` 为循环指定毫秒。

### 3.3 文本流控 (Flow Control)
*   `[r]`: 暂停。等待用户点击或 1 秒自动继续。
*   `[C]`: 清屏。清除对话框，停止当前循环音效。自动模式下延时 5 秒。

## 4. 关键逻辑流维护
1.  **AI 输出解析**: 修改 `game_engine.py` 中的 `_start_sequence`。
2.  **新指令添加**: 在 `game_engine.py` 的 `_execute_asset_command` 中增加分支，并在 `audio`/`visual_manager` 中实现底层接口。
3.  **UI 布局调整**: 修改 `pages.py` 中的 `GamePage` 类。当前固定为 1920x1080 场景，自适应缩放。
