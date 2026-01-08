# 开发者指南 (LLM-Galgame-Engine)

欢迎查阅 AI 驱动的 Galgame 引擎开发文档。本指南涵盖了项目架构、设置说明以及资源管理系统。

## 1. 项目概述

本项目是一个由大语言模型 (LLM) 驱动的视觉小说引擎。它具有 Python 后端（编排 AI 智能体）和 PySide6 (Qt) 前端，用于渲染游戏界面。

### 关键组件

*   **`main.py`**: 入口点。启动 PySide6 应用程序。
*   **`src/frontend/`**: 包含 GUI 逻辑、游戏渲染引擎和页面管理。
*   **`src/llm_chain.py`**: 核心逻辑链，管理与 LLM API 的交互。采用 3-API 架构 (Story, Summary, Logic)。
*   **`src/memory_manager.py`**: 管理游戏记忆、历史记录及存档。
*   **`src/prompt_assembler.py`**: 通用提示词组装器，基于 `assets/prompts.json` 动态构建 Prompt。
*   **`assets/`**: 存储所有游戏资源（图像、音频、文本配置、提示词）。

## 2. 目录结构

```text
root/
├── main.py                 # 游戏启动器
├── scan_characters.py      # 工具：更新 assets/character_map.json
├── scan_backgrounds.py     # 工具：更新 assets/background_map.json
├── scan_sounds.py          # 工具：更新 assets/sound_map.json (按描述映射)
├── assets/
│   ├── bg/                 # 背景图片
│   ├── bgm/                # 背景音乐
│   ├── fg/                 # 角色立绘 (每个角色一个文件夹)
│   ├── character_map.json  # 映射角色名称/表情到文件
│   ├── background_map.json # 映射背景 ID 到文件
│   ├── sound_map.json      # 映射音效描述到文件
│   ├── prompts.json        # 提示词文件路径映射与组装顺序配置
│   ├── 提示词/             # 各类 Prompt 文本文件
│   └── ... (配置, 用户设定)
└── src/
    ├── frontend/           # UI 代码
    │   ├── game_engine.py  # 解析标签 -> 视觉/音频动作
    │   ├── pages.py        # 页面逻辑 (含通用提示词编辑器)
    │   └── ...
    └── ...
```

## 3. 资源管理系统

引擎使用 JSON 映射文件将脚本中使用的“标签”与磁盘上的“文件路径”解耦。

### A. 角色 (`assets/fg/` & `character_map.json`)
*   **工作流:**
    1.  将新的角色文件夹放入 `assets/fg/`。
    2.  运行 `python scan_characters.py`。
    3.  编辑 `assets/character_map.json` 重命名键值（如 `happy`）。
    4.  游戏中使用: `[fg-Name-happy]`.

### B. 背景 (`assets/bg/` & `background_map.json`)
*   **工作流:**
    1.  将图片放入 `assets/bg/`。
    2.  运行 `python scan_backgrounds.py`。
    3.  游戏中使用: `[Background-Filename]`.

### C. 音乐 (`assets/bgm/` & `registry.json`)
*   **工作流:**
    1.  将音频文件放入 `assets/bgm/`。
    2.  游戏中使用: `[Music-TrackName]` (自动循环)。使用 `[StopBGM]` 停止。

### D. 音效 (`assets/sound/` & `sound_map.json`)
*   **工作流:**
    1.  将音频文件放入 `assets/sound/`。
    2.  运行 `python scan_sounds.py` (或手动编辑 JSON)。
    3.  确保 `assets/sound_map.json` 中的键是中文描述（如 "大雨1"）。
    4.  游戏中使用: `[sound-大雨1-0]`。使用 `[StopSound]` 停止所有音效。

## 4. 提示词系统 (Prompt System)

系统采用高度可配置的提示词组装机制。

*   **配置**: `assets/prompts.json` 定义了所有提示词文件的路径 (`file_map`) 和各个 AI 功能的组装顺序 (`sequences`)。
*   **编辑**: 在游戏主菜单点击 **Editor (Dev)** 进入 **Universal Prompt Editor**。
    *   **Resource Files**: 直接编辑提示词文本、世界观、NPC 设定。
    *   **Prompt Sequences**: 拖拽调整提示词的拼接顺序。

## 5. 开发工具

*   **`scan_characters.py`**: 更新角色映射。
*   **`scan_backgrounds.py`**: 更新背景映射。
*   **`scan_sounds.py`**: 更新音效映射。

## 6. 添加新功能

*   **新指令**:
    1.  更新 `src/frontend/game_engine.py` 中的 `_execute_asset_command`。
    2.  更新 `DIRECTOR_MANUAL.md`。

*   **UI 更改**:
    *   编辑 `src/frontend/pages.py`。