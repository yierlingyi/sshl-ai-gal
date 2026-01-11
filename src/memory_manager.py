import json
import os
from typing import List, Dict, Any, Optional
import asyncio
from dataclasses import dataclass, field

@dataclass
class GameState:
    date: str = "2026-01-06"
    favorability: Dict[str, int] = field(default_factory=dict)
    inventory: List[str] = field(default_factory=list)
    current_bgm: str = "None"
    current_bg: str = "None"
    visible_characters: Dict[str, str] = field(default_factory=dict) # Name -> Expression/Face

class MemoryManager:
    def __init__(self):
        # raw_history now stores simple dicts, but we track layers externally or implicitly
        self.raw_history: List[Dict[str, str]] = [] 
        
        # Summaries now stored with range info: [{"range": "1-20", "content": "..."}]
        self.small_summaries: List[Dict[str, str]] = []
        
        # Big summary storage: range -> content
        self.big_summary_storage: Dict[str, str] = {} 
        self._active_big_summary: str = "The story has just begun." 
        
        self.plot_guidance: List[str] = []
        
        self.state = GameState()
        
        # Counters
        self.global_layer_count = 0
        self.last_summary_layer = 0
        self.small_summary_count_since_plan = 0
        
        # Configuration
        self.raw_history_limit = 20
        self.raw_history_buffer_size = 3
        
        self.small_summary_threshold_for_big = 10
        self.small_summary_buffer_size = 3
        self.plot_planning_threshold = 5 # Default, can be updated
        
        self._observers = []
        
        # File Paths
        self.path_summary_big = "assets/剧情总结/大总结.json"
        self.path_summary_small = "assets/剧情总结/小总结.json"
        self.path_history = "assets/剧情总结/未总结内容.json"
        self.path_plot_plan = "assets/剧情规划存储/当前规划.txt"
        self.path_gamestate = "assets/gamestate.json"
        
        self._load_persistent_data()

    @property
    def big_summary(self) -> str:
        if not self.big_summary_storage:
            return self._active_big_summary
        return "\n\n".join(self.big_summary_storage.values())

    def _load_persistent_data(self):
        # Load GameState
        if os.path.exists(self.path_gamestate):
            try:
                with open(self.path_gamestate, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                    self.state = GameState(**state_data)
            except Exception as e:
                print(f"[MemoryManager] Failed to load gamestate: {e}")

        # Load Big Summary
        if os.path.exists(self.path_summary_big):
            try:
                with open(self.path_summary_big, 'r', encoding='utf-8') as f:
                    self.big_summary_storage = json.load(f)
                    if self.big_summary_storage:
                         self._active_big_summary = "\n\n".join(self.big_summary_storage.values())
            except json.JSONDecodeError:
                pass

        # Load Small Summaries
        if os.path.exists(self.path_summary_small):
            try:
                with open(self.path_summary_small, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.small_summaries = []
                    for k, v in data.items():
                        self.small_summaries.append({"range": k, "content": v})
                    
                    def get_start(x):
                        try:
                            return int(x["range"].split('-')[0])
                        except:
                            return 0
                    self.small_summaries.sort(key=get_start)
            except json.JSONDecodeError:
                pass

        # Load Raw History & Layer Count
        if os.path.exists(self.path_history):
            try:
                with open(self.path_history, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.global_layer_count = data.get("current_layer", 0)
                    self.small_summary_count_since_plan = data.get("small_summary_count_since_plan", 0)
                    history_map = data.get("history", {})
                    
                    self.raw_history = []
                    sorted_keys = sorted(history_map.keys(), key=lambda x: int(x))
                    for k in sorted_keys:
                        entry = history_map[k]
                        if "user" in entry:
                            self.raw_history.append({"role": "user", "content": entry["user"]})
                        if "ai" in entry:
                            self.raw_history.append({"role": "assistant", "content": entry["ai"]})
            except json.JSONDecodeError:
                pass

        # Load Plot Plan
        if os.path.exists(self.path_plot_plan):
            with open(self.path_plot_plan, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    self.plot_guidance = [line.strip() for line in content.split('\n') if line.strip()]

    def _save_persistent_data(self):
        # Save GameState
        try:
            os.makedirs(os.path.dirname(self.path_gamestate), exist_ok=True)
            with open(self.path_gamestate, 'w', encoding='utf-8') as f:
                json.dump(self.state.__dict__, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[MemoryManager] Failed to save gamestate: {e}")

        # Save Big Summary
        os.makedirs(os.path.dirname(self.path_summary_big), exist_ok=True)
        with open(self.path_summary_big, 'w', encoding='utf-8') as f:
            json.dump(self.big_summary_storage, f, indent=4, ensure_ascii=False)
            
        # Save Small Summaries
        os.makedirs(os.path.dirname(self.path_summary_small), exist_ok=True)
        small_map = {item["range"]: item["content"] for item in self.small_summaries}
        with open(self.path_summary_small, 'w', encoding='utf-8') as f:
            json.dump(small_map, f, indent=4, ensure_ascii=False)
            
        # Save Raw History
        os.makedirs(os.path.dirname(self.path_history), exist_ok=True)
        history_map = {}
        
        pairs = []
        current_pair = {}
        for msg in self.raw_history:
            if msg['role'] == 'user':
                current_pair['user'] = msg['content']
            elif msg['role'] == 'assistant':
                current_pair['ai'] = msg['content']
                pairs.append(current_pair)
                current_pair = {}
        
        if current_pair:
             pairs.append(current_pair)

        # Calculate start layer ID for the current buffer
        start_layer = self.global_layer_count - len(pairs) + 1
        if start_layer < 1: start_layer = 1 
        
        for i, pair in enumerate(pairs):
            layer_id = str(start_layer + i)
            history_map[layer_id] = pair
            
        history_data = {
            "current_layer": self.global_layer_count,
            "small_summary_count_since_plan": self.small_summary_count_since_plan,
            "history": history_map
        }
        
        with open(self.path_history, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=4, ensure_ascii=False)

        # Save Plot Plan
        os.makedirs(os.path.dirname(self.path_plot_plan), exist_ok=True)
        with open(self.path_plot_plan, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.plot_guidance))

    def clear_memory(self):
        self.raw_history = []
        self.small_summaries = []
        self.big_summary_storage = {}
        self._active_big_summary = "The story has just begun."
        self.plot_guidance = []
        self.state = GameState()
        self.global_layer_count = 0
        self.last_summary_layer = 0
        self.small_summary_count_since_plan = 0
        self._save_persistent_data()
        self._notify_observers()

    def add_observer(self, callback):
        """Register a callback to be called when memory updates."""
        self._observers.append(callback)

    def _notify_observers(self):
        for callback in self._observers:
            callback()

    def add_message(self, role: str, content: str):
        """Adds a message to raw history."""
        self.raw_history.append({"role": role, "content": content})
        if role == "assistant":
            self.global_layer_count += 1
            self._save_persistent_data()

    def get_context(self) -> str:
        """
        Assembles context: [Big Summary] + [Recent Small Summaries] + [Raw History]
        """
        context_parts = []
        
        # 1. Big Summary
        context_parts.append(f"## Previous Story Summary\n{self.big_summary}")
        
        # 2. Small Summaries
        if self.small_summaries:
            context_parts.append("## Recent Events")
            for item in self.small_summaries:
                context_parts.append(f"- [{item['range']}] {item['content']}")
        
        # 3. Raw History
        context_parts.append("## Current Dialogue")
        for msg in self.raw_history:
            role = msg['role'].capitalize()
            content = msg['content']
            context_parts.append(f"{role}: {content}")
            
        return "\n\n".join(context_parts)

    def get_plot_guidance(self) -> str:
        """Returns the latest plot guidance or a default."""
        if self.plot_guidance:
            return "\n".join([f"- {g}" for g in self.plot_guidance])
        return "No specific guidance. Develop the story naturally."

    def check_for_triggers(self) -> Dict[str, Any]:
        """
        Checks if any background tasks need to be triggered.
        Returns a dict indicating tasks to run.
        """
        triggers = {
            "needs_small_summary": False,
            "needs_big_summary": False,
            "needs_plot_planning": False,
            "messages_to_summarize": []
        }
        
        if len(self.raw_history) >= self.raw_history_limit + self.raw_history_buffer_size:
            triggers["needs_small_summary"] = True
            
        if len(self.small_summaries) >= self.small_summary_threshold_for_big + self.small_summary_buffer_size:
            triggers["needs_big_summary"] = True
            
        if self.small_summary_count_since_plan >= self.plot_planning_threshold:
            triggers["needs_plot_planning"] = True
        
        return triggers
        
    def consume_raw_history(self) -> List[Dict[str, str]]:
        """Returns history to summarize and KEEPS buffer."""
        if len(self.raw_history) <= self.raw_history_buffer_size:
            return []
            
        to_summarize = self.raw_history[:-self.raw_history_buffer_size]
        self.raw_history = self.raw_history[-self.raw_history_buffer_size:] # Keep only buffer
        self._save_persistent_data()
        return to_summarize
        
    def consume_small_summaries_for_big_merge(self) -> List[str]:
        """Returns small summaries to merge and KEEPS buffer."""
        if len(self.small_summaries) <= self.small_summary_buffer_size:
            return []
            
        to_merge_objs = self.small_summaries[:-self.small_summary_buffer_size]
        to_merge_content = [f"[{obj['range']}] {obj['content']}" for obj in to_merge_objs]
        
        self.small_summaries = self.small_summaries[-self.small_summary_buffer_size:]
        self._save_persistent_data()
        self._notify_observers()
        return to_merge_content
        
    def append_small_summary(self, summary: str):
        """Callback when small summary is generated."""
        start_layer = self.last_summary_layer + 1
        end_layer = self.global_layer_count
        if end_layer < start_layer: end_layer = start_layer
        
        range_str = f"{start_layer}-{end_layer}"
        self.last_summary_layer = end_layer
        
        self.small_summaries.append({"range": range_str, "content": summary})
        
        # Increment counter for plot planning
        self.small_summary_count_since_plan += 1
        
        self._save_persistent_data()
        self._notify_observers()
    
    def reset_plot_plan_counter(self):
        self.small_summary_count_since_plan = 0
        self._save_persistent_data()
        
    def update_big_summary(self, summary: str):
        """Callback when big summary is generated."""
        range_str = f"1-{self.global_layer_count}"
        self.big_summary_storage = {range_str: summary}
        self._active_big_summary = summary
        
        self._save_persistent_data()
        self._notify_observers()

    def update_plot_guidance(self, guidance: List[str]):
        self.plot_guidance = guidance
        self.reset_plot_plan_counter() # Reset counter after update
        self._save_persistent_data()

    def save_gamestate(self):
        """Public method to trigger persistence (e.g. after direct state modification)."""
        self._save_persistent_data()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_history": self.raw_history,
            "small_summaries": self.small_summaries,
            "big_summary": self.big_summary_storage,
            "plot_guidance": self.plot_guidance,
            "state": self.state.__dict__,
            "global_layer_count": self.global_layer_count,
            "last_summary_layer": self.last_summary_layer,
            "small_summary_count_since_plan": self.small_summary_count_since_plan
        }

    def load_from_dict(self, data: Dict[str, Any]):
        self.raw_history = data.get("raw_history", [])
        
        # Rehydrate small summaries
        smalls_data = data.get("small_summaries", [])
        if smalls_data and isinstance(smalls_data[0], str):
             self.small_summaries = [{"range": "?", "content": s} for s in smalls_data]
        else:
             self.small_summaries = smalls_data

        # Rehydrate big summary
        big_data = data.get("big_summary", {})
        if isinstance(big_data, str):
             self.big_summary_storage = {"1-?": big_data}
             self._active_big_summary = big_data
        else:
             self.big_summary_storage = big_data
             if self.big_summary_storage:
                  self._active_big_summary = "\n\n".join(self.big_summary_storage.values())

        self.plot_guidance = data.get("plot_guidance", [])
        state_data = data.get("state", {})
        self.state = GameState(**state_data)
        self.global_layer_count = data.get("global_layer_count", 0)
        self.last_summary_layer = data.get("last_summary_layer", 0)
        self.small_summary_count_since_plan = data.get("small_summary_count_since_plan", 0)