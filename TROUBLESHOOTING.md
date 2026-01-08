# 故障排除指南

LLM-Galgame-Engine 的常见问题和解决方案。

## 1. 启动崩溃或脚本错误

### "无法进入程序" / 启动闪退
*   **原因:** 配置文件损坏或 Python 环境问题。
*   **修复:** 
    1.  删除 `config.json` (程序会自动重建默认值)。
    2.  确保安装了所有依赖: `pip install -r requirements.txt` (特别是 `qasync`, `pyside6`, `openai`)。

## 2. 资源问题

### "Character/Background not showing"
*   **检查:** 文件是否在 `assets/fg` 或 `assets/bg`，并已运行扫描工具更新映射文件。

### "Expression not changing"
*   **修复:** 检查 `assets/character_map.json` 中的键名是否匹配指令。

## 3. 音频问题

### "Music/Sound not playing" (无声)
*   **原因 1:** 路径问题。引擎已更新为使用绝对路径，请确保文件名在 `json` 映射中正确。
*   **原因 2:** 格式问题。控制台若显示 `OGG header` 警告通常无碍，但若完全无法播放，尝试转为 WAV。
*   **原因 3:** 音量为 0。检查设置页面。

### "程序死机/卡死" (切换音效时)
*   **修复:** 这是一个已知问题，已通过在 `AudioManager` 中添加 `player.stop()` 强制释放资源得到修复。请确保使用的是最新代码。

## 4. AI 与 逻辑问题

### "System Paused: Generating Big Summary..."
*   **现象:** 游戏暂停，显示系统消息。
*   **解释:** 这是正常机制。后台正在进行关键的总结生成任务，为防止记忆错乱，暂时阻塞游戏进程。任务完成后（通常几十秒）会自动恢复。如果长时间卡住，请检查 API 连接。

### "XML Tag Error" / "Invalid JSON"
*   **原因:** AI 输出格式错误。
*   **修复:** 系统会自动重试。如果频繁发生，请在编辑器中微调 `assets/提示词/` 下的相关 Prompt，强化 XML/JSON 格式要求。
