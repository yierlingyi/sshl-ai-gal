# LLM-Galgame-Engine 开发报告与使用教程

## 1. 项目概述

**LLM-Galgame-Engine** 是一款基于大语言模型（LLM）驱动的下一代视觉小说引擎。采用 **"Three-AI Architecture"** 和 **"3-API Grouping"** 设计，实现剧情无限生成与自动演出。

## 2. 核心架构解析

### 2.1 三智体协作 (Three-AI System)

1.  **AI-1: Storyteller (剧作家)**: 生成对话与旁白。
2.  **AI-2: Director (导演)**: 插入视听指令 (`[Music]`, `[bg]`)。
3.  **AI-3: Architect (架构师)**: 规划宏观剧情。

### 2.2 3-API 分组架构 (New)

为防止上下文混淆，系统将 API 客户端分为三组，可在设置中独立配置：
1.  **Story Client**: 专用于 Storyteller。
2.  **Summary Client**: 专用于生成大小总结。
3.  **Logic Client**: 专用于 Director 和 Architect (JSON/指令生成)。

### 2.3 记忆与提示词系统

*   **MemoryManager**: 采用 JSON 格式存储 (`未总结内容.json`, `小总结.json`, `大总结.json`)。支持按“层级” (Turn) 追踪历史。
*   **PromptAssembler**: 通用组装器。读取 `assets/prompts.json` 配置，动态拼接文件内容 (`file`)、静态文本 (`text`) 和动态数据 (`dynamic`)。
*   **Universal Editor**: 内置编辑器，可实时调整所有 Prompt 文件及拼接顺序。

## 3. 开发者教程

### 3.1 运行游戏
```bash
python -m src.frontend.main_window
```

### 3.2 关键机制

*   **XML 验证与重试**: 系统强制要求 AI 输出包裹在 XML 标签中 (`<game>`, `<summary_big>` 等)。若标签缺失或解析失败，后端会自动重试。
*   **阻塞式后台任务**: 当生成“大总结”等关键数据时，游戏会进入 **[System Paused]** 状态，确保数据一致性。
*   **音频管理**: BGM 默认无限循环。提供 `[StopBGM]` 和 `[StopSound]` 指令。

## 4. 扩展指南

### 自定义 Prompt 结构
1.  进入游戏 -> Editor (Dev)。
2.  切换到 "Prompt Sequences" 标签。
3.  选择功能模块（如 `storyteller`），拖拽调整提示词顺序或查看内容。
4.  点击保存，立即生效。

### 接入不同模型
在 **Config** 页面，为 Story, Summary, Logic 分别设置不同的 Base URL 和 API Key。例如，用更聪明的模型（如 GPT-4）做 Logic/Summary，用更便宜快速的模型做 Story。