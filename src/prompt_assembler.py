import json
import os
from datetime import datetime
from typing import List, Dict, Any
from .memory_manager import MemoryManager

class PromptAssembler:
    """
    Constructs payloads for AI agents based on assets/prompts.json configuration.
    """

    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self.config = {}
        self.file_cache = {}
        self.date_guidance = []
        self._load_config()
        self._load_npcs()

    def _load_config(self):
        try:
            with open("assets/prompts.json", "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"[PromptAssembler] Error loading prompts.json: {e}")
            self.config = {"file_map": {}, "sequences": {}}
            
        # Load Date Guidance (Plot Guidance by Date)
        try:
            p_path = "assets/世界设定/剧情指导.json"
            if os.path.exists(p_path):
                with open(p_path, "r", encoding="utf-8") as f:
                    self.date_guidance = json.load(f)
        except Exception as e:
            print(f"[PromptAssembler] Error loading 剧情指导.json: {e}")
            self.date_guidance = []

    def _load_file_content(self, key: str) -> str:
        """Reads file content based on key from file_map."""
        path = self.config.get("file_map", {}).get(key)
        if not path:
            return ""
        
        # Determine if we should cache this file (static assets usually yes)
        # For now, let's read fresh to allow hot-reloading if user edits txt
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"[PromptAssembler] Warning: File not found for key '{key}' at '{path}'")
            return ""

    def _load_npcs(self):
        # Load NPCs (Keep this logic here or move to a dynamic handler?)
        # For now, we pre-load them but we'll access them via dynamic handler
        self.npcs = []
        self.important_npcs = {}
        
        npc_root = "assets/NPC人设"
        if os.path.exists(npc_root):
            # Generic
            for f_name in os.listdir(npc_root):
                if f_name.endswith(".txt"):
                    with open(os.path.join(npc_root, f_name), "r", encoding="utf-8") as f:
                        self.npcs.append(f.read().strip())
            
            # Important
            important_root = os.path.join(npc_root, "重要NPC")
            if os.path.exists(important_root):
                for folder_name in os.listdir(important_root):
                    folder_path = os.path.join(important_root, folder_name)
                    if os.path.isdir(folder_path):
                        profile = ""
                        p_path = os.path.join(folder_path, "人物人设.txt")
                        if os.path.exists(p_path):
                            with open(p_path, "r", encoding="utf-8") as f:
                                profile = f.read().strip()
                        
                        rules = []
                        j_path = os.path.join(folder_path, "好感度提示词.json")
                        if os.path.exists(j_path):
                            try:
                                with open(j_path, "r", encoding="utf-8") as f:
                                    rules = json.load(f)
                                    rules.sort(key=lambda x: x.get("threshold", 0), reverse=True)
                            except: pass
                        
                        self.important_npcs[folder_name] = {"profile": profile, "rules": rules}

    def _get_date_context(self) -> str:
        """Returns context based on current date."""
        date_str = self.memory.state.date
        context_lines = [f"Current Date: {date_str}"]
        
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            weekday = dt.strftime("%A")
            context_lines.append(f"Day of Week: {weekday}")
            
            # Simple Season Check
            month = dt.month
            if month in [12, 1, 2]: season = "Winter"
            elif month in [3, 4, 5]: season = "Spring"
            elif month in [6, 7, 8]: season = "Summer"
            else: season = "Autumn"
            context_lines.append(f"Season: {season}")
            
            # Match with Guidance
            # Currently Guidance uses "Day 1", "Day 2". We need to know start date to map.
            # Assuming start date 2026-01-06 is Day 1.
            start_date = datetime(2026, 1, 6)
            delta = (dt - start_date).days + 1
            day_label = f"Day {delta}"
            
            guidance_found = False
            for item in self.date_guidance:
                if item.get("date") == day_label or item.get("date") == date_str:
                     context_lines.append(f"**Special Event / Guidance for Today:** {item.get('outline', '')}")
                     guidance_found = True
                     break
            
            if not guidance_found:
                context_lines.append("(No specific event guidance for today. Proceed with daily life logic.)")

        except ValueError:
            context_lines.append("(Date format error)")
            
        return "\n".join(context_lines)

    def _get_affection_context(self) -> str:
        """Returns context based on character favorability."""
        lines = ["# Character Affection Status"]
        favs = self.memory.state.favorability
        
        has_entries = False
        for name, value in favs.items():
            if name in self.important_npcs:
                data = self.important_npcs[name]
                attitude = "Neutral"
                
                # Check rules
                best_rule = None
                for rule in data["rules"]:
                    if value >= rule.get("threshold", 0):
                        best_rule = rule
                        break # sorted descending
                
                if best_rule:
                    attitude = best_rule.get("attitude", "Neutral")
                    
                lines.append(f"- **{name.capitalize()}** (Favorability: {value}): {attitude}")
                has_entries = True
            elif value != 0:
                 lines.append(f"- {name.capitalize()}: {value}")
                 has_entries = True
                 
        if not has_entries:
            lines.append("(No significant relationships yet.)")
            
        return "\n".join(lines)

    def _get_world_context(self) -> str:
        """Bundles World View with Current Date Guidance."""
        world_base = self._load_file_content("world_view")
        date_info = self._get_date_context()
        
        return f"# World Setting & Current Timeline\n{world_base}\n\n## Timeline Context\n{date_info}"

    def _get_dynamic_content(self, key: str) -> str:
        """Resolves dynamic keys to actual content."""
        if key == "plot_guidance":
            return self.memory.get_plot_guidance()
        
        elif key == "world_context":
            return self._get_world_context()
            
        elif key == "date_context":
            return self._get_date_context()
            
        elif key == "affection_context":
            return self._get_affection_context()

        elif key == "game_state_dump":
            s = self.memory.state
            lines = ["# Current Game State (Visual/Audio)"]
            lines.append(f"- Date: {s.date}")
            lines.append(f"- BGM: {s.current_bgm}")
            lines.append(f"- Background: {s.current_bg}")
            if s.visible_characters:
                lines.append("- Visible Characters:")
                for name, face in s.visible_characters.items():
                    lines.append(f"  * {name} (Expression: {face})")
            else:
                lines.append("- Visible Characters: None")
            return "\n".join(lines)

        elif key == "big_summary":
            return self.memory.big_summary
            
        elif key == "small_summaries":
            if self.memory.small_summaries:
                return "\n".join([f"- [{s['range']}] {s['content']}" for s in self.memory.small_summaries])
            return "No recent events."
            
        elif key == "npcs":
            blocks = ["# NPC Profiles & Relationships"]
            for name, data in self.important_npcs.items():
                current_fav = self.memory.state.favorability.get(name, 0)
                attitude = "Neutral"
                for rule in data["rules"]:
                    if current_fav >= rule.get("threshold", 0):
                        attitude = rule.get("attitude", "")
                        break
                blocks.append(f"--- Character: {name} ---\n{data['profile']}\n[Current Relationship Status (Favorability: {current_fav})]: {attitude}")
            
            for npc in self.npcs:
                blocks.append(f"--- Other NPC ---\n{npc}")
            return "\n".join(blocks)
            
        elif key == "available_music":
            try:
                with open("assets/registry.json", "r", encoding="utf-8") as f:
                    registry = json.load(f)
                    return "\n".join([f"- {m['name']}" for m in registry.get("music", [])])
            except:
                return "No music available."

        elif key == "available_sounds":
            try:
                with open("assets/sound_map.json", "r", encoding="utf-8") as f:
                    sound_map = json.load(f)
                    # Limit the list if too long? 1000+ sounds might overwhelm context.
                    # Maybe provide categories or just list all?
                    # 1000 lines is a lot.
                    # Let's list keys.
                    keys = list(sound_map.keys())
                    # Format as comma separated or newlines?
                    # Newlines is clearer but longer. Comma separated saves tokens.
                    # "大雨1, 大雨2, ..."
                    return ", ".join(keys)
            except:
                return "No sounds available."
                
        return ""

    def assemble_prompt(self, sequence_name: str) -> str:
        """
        Assembles a single string prompt for tasks like Director, Planner, Summarizer.
        """
        parts = []
        sequence = self.config.get("sequences", {}).get(sequence_name, [])
        
        for item in sequence:
            itype = item.get("type")
            key = item.get("key")
            
            content = ""
            if itype == "file":
                content = self._load_file_content(key)
            elif itype == "text":
                content = item.get("content", "")
            elif itype == "dynamic":
                content = self._get_dynamic_content(key)
                
            if content:
                parts.append(content)
                
        return "\n".join(parts)

    def assemble_storyteller_payload(self) -> List[Dict[str, str]]:
        """
        Special assembly for Storyteller (Chat Completion format).
        Constructs System Prompt + History.
        """
        sequence = self.config.get("sequences", {}).get("storyteller", [])
        system_parts = []
        
        history_msgs = []
        
        for item in sequence:
            itype = item.get("type")
            key = item.get("key")
            
            if key == "history":
                # Special handling for history -> It's a list of messages, not text for system prompt
                history_msgs = self.memory.raw_history
                continue
            
            content = ""
            if itype == "file":
                content = self._load_file_content(key)
            elif itype == "text":
                content = item.get("content", "")
            elif itype == "dynamic":
                content = self._get_dynamic_content(key)
                
            if content:
                system_parts.append(content)
        
        final_system_prompt = "\n".join(system_parts)
        
        messages = [{"role": "system", "content": final_system_prompt}]
        messages.extend(history_msgs)
        
        return messages
    
    def get_current_story_guidance(self) -> str:
         # Legacy support if needed, or move to dynamic content
         # For now, keep it simple
         return self.memory.get_plot_guidance()