import asyncio
import re
from enum import Enum
from PySide6.QtCore import QObject, Signal, QTimer, Slot
import qasync

# Mock Backend Import
# In real usage: from src.llm_chain import LLMChain
# We will assume LLMChain interface exists

class GameState(Enum):
    IDLE = 0
    GENERATING = 1
    PLAYING = 2
    TYPING = 3
    WAITING_INPUT = 4 # Waiting for user to advance (e.g. after [r] or text finished)
    PAUSED = 5 # General pause
    WAITING_CLEAR = 6 # Waiting for user to confirm clear

import json
import os

class GameEngine(QObject):
    text_updated = Signal(str, str) # name, content
    
    def __init__(self, visual_manager, audio_manager, llm_chain):
        super().__init__()
        self.visual = visual_manager
        self.audio = audio_manager
        self.backend = llm_chain
        
        self.state = GameState.IDLE
        self.is_auto_mode = False
        self.text_speed = 50 # ms per char

        self._execution_queue = []
        self._current_text_segment = ""
        self._current_full_text = ""
        self._typewriter_index = 0
        
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self._type_step)
        
        # Load Registry
        self.registry = {"music": [], "backgrounds": []}
        try:
            with open("assets/registry.json", "r", encoding="utf-8") as f:
                self.registry = json.load(f)
        except Exception as e:
            print(f"Failed to load registry: {e}")

        # Load Sound Map
        self.sound_map = {}
        try:
            with open("assets/sound_map.json", "r", encoding="utf-8") as f:
                self.sound_map = json.load(f)
        except Exception as e:
            print(f"Failed to load sound map: {e}")

        # Sound Timer
        self._sound_timer = QTimer()
        self._sound_timer.setSingleShot(True)
        self._sound_timer.timeout.connect(self._on_sound_timeout)

    def _on_sound_timeout(self):
        print("[GameEngine] Sound timer expired. Stopping loop.")
        self.audio.stop_looping_sfx()

    def set_text_speed(self, speed_ms: int):
        self.text_speed = max(10, speed_ms)

    @Slot(bool)
    def set_auto_mode_slot(self, is_auto: bool):
        self.is_auto_mode = is_auto
        print(f"Auto mode set to: {is_auto}")
        # If we were waiting for input, and auto mode is turned on, advance
        if is_auto and self.state in [GameState.WAITING_INPUT, GameState.WAITING_CLEAR]:
            self.user_advance_slot()

    @Slot()
    def user_advance_slot(self):
        """Called when user clicks, presses space, or auto-mode timer fires."""
        if self.state == GameState.TYPING:
            # Finish typing instantly
            self._typewriter_index = len(self._current_text_segment)
            self._type_step()
        elif self.state == GameState.WAITING_INPUT:
            # Continue execution queue
            self.state = GameState.PLAYING
            self._process_queue()
        elif self.state == GameState.WAITING_CLEAR:
            self._perform_clear()
            self.state = GameState.PLAYING
            self._process_queue()

    @qasync.asyncSlot(str)
    async def handle_turn(self, user_input: str):
        if self.state not in [GameState.IDLE, GameState.WAITING_INPUT]:
            return
            
        self.state = GameState.GENERATING
        self.text_updated.emit("Thinking...", "")
        
        try:
            # Execute backend turn (handles blocking check internally)
            raw_response = await self.backend.execute_turn(user_input)
            
            # Check for blocking or error message
            if raw_response.startswith("[System"):
                 self.text_updated.emit("System", raw_response)
                 self.state = GameState.IDLE
                 return

            self._start_sequence(raw_response)
            
        except Exception as e:
            print(f"Error: {e}")
            self.state = GameState.IDLE

    def _start_sequence(self, response_text: str):
        self.state = GameState.PLAYING
        
        # 1. Execute instant commands (backgrounds, music, etc.)
        tag_pattern = re.compile(r"\[(.*?)\]")
        tags = tag_pattern.findall(response_text)
        
        for tag in tags:
            self._execute_asset_command(tag)
            
        # 2. Prepare text sequence for playback
        # Remove asset tags, but keep flow-control tags [r] and [C]
        text_with_flow_tags = response_text
        for tag in tags:
            if not tag.upper() in ["R", "C"]:
                 text_with_flow_tags = text_with_flow_tags.replace(f"[{tag}]", "")
        
        # Tokenize by flow-control tags
        tokens = re.split(r'(\[r\]|\[C\])', text_with_flow_tags, flags=re.IGNORECASE)
        
        self._execution_queue = [token.strip() for token in tokens if token.strip()]
        self._current_full_text = ""
        self._process_queue()

    def _process_queue(self):
        if not self._execution_queue:
            # End of sequence, wait for user to start next turn
            self.state = GameState.WAITING_INPUT 
            return

        segment = self._execution_queue.pop(0)
        
        if segment.upper() == "[R]":
            self.state = GameState.WAITING_INPUT
            if self.is_auto_mode:
                QTimer.singleShot(1000, self.user_advance_slot)
        
        elif segment.upper() == "[C]":
            if self.is_auto_mode:
                self._perform_clear()
                # Continue processing after a delay in auto mode
                QTimer.singleShot(5000, self._process_queue)
            else:
                # Manual mode: Wait for user input to clear
                self.state = GameState.WAITING_CLEAR

        else: # It's a text segment
            self.state = GameState.TYPING
            self._current_text_segment = segment
            self._typewriter_index = 0
            self.typing_timer.start(self.text_speed)

    def _perform_clear(self):
        self._current_full_text = "" # Clear visual text
        self._sound_timer.stop() # Cancel any pending sound stop
        self.audio.stop_looping_sfx() # Stop any looping sounds
        self.text_updated.emit("System", self._current_full_text)

    def _type_step(self):
        if self._typewriter_index < len(self._current_text_segment):
            self._typewriter_index += 1
            new_char = self._current_text_segment[self._typewriter_index-1]
            self._current_full_text += new_char
            self.text_updated.emit("System", self._current_full_text)
        else:
            self.typing_timer.stop()
            # Finished typing this segment, move to the next
            self._process_queue()

    def _execute_asset_command(self, tag: str):
        parts = tag.split("-")
        category = parts[0]
        
        if category == "Background" and len(parts) > 1:
            self.visual.set_background(parts[1])
        elif category == "Music" and len(parts) > 1:
            self._play_music(parts[1])
        elif category == "StopBGM":
            self.audio.stop_bgm()
        elif category == "sound" and len(parts) > 1:
            self._play_sound(parts)
        elif category == "StopSound":
            self.audio.stop_sfx()
        elif category == "立绘" and len(parts) > 2:
            name, action = parts[1], parts[2]
            if hasattr(self.visual, "presets") and action in self.visual.presets:
                self.visual.apply_preset(name, action)
            else:
                self.visual.animate_sprite(name, action.lower())
        elif category == "Sprite" and len(parts) > 2:
            self.visual.apply_preset(parts[1], parts[2])
        elif category == "fg" and len(parts) > 2:
            self.visual.set_expression(parts[1], parts[2])
        elif category in ["Join", "Enter"] and len(parts) > 1:
            preset = parts[2] if len(parts) > 2 else "pos_center"
            self.visual.join_character(parts[1], preset)
        elif category in ["Leave", "Exit"] and len(parts) > 1:
            self.visual.remove_sprite(parts[1])
            
    def _play_music(self, music_name: str):
        found_entry = next((item for item in self.registry.get("music", []) if item["name"] == music_name), None)
        if found_entry:
            file_path = os.path.join("assets/bgm", found_entry["file"])
            if os.path.exists(file_path):
                self.audio.play_bgm(file_path)
            else:
                print(f"Music file missing: {file_path}")
        else:
            # Fallback search (not recommended)
            print(f"Music not found in registry: {music_name}")

    def _play_sound(self, parts):
        # [sound-name-duration]
        sound_name = parts[1]
        duration_ms = 0
        if len(parts) > 2:
            try:
                duration_ms = int(parts[2])
            except:
                pass
        
        # Look up in sound_map
        if sound_name in self.sound_map:
            file_path = self.sound_map[sound_name]["file"]
        else:
            # Fallback: Check if file exists in assets/sound/sound_name.ogg
            file_path = os.path.join("assets/sound", f"{sound_name}.ogg")
            if not os.path.exists(file_path):
                print(f"Sound not found: {sound_name}")
                return

        # Stop previous timer if any
        self._sound_timer.stop()
        
        print(f"[GameEngine] Playing Sound: {sound_name}, Path: {file_path}, Duration: {duration_ms}ms")

        if duration_ms > 0:
            # Loop with timeout
            self.audio.play_sfx(file_path, loop=True)
            self._sound_timer.setInterval(duration_ms)
            self._sound_timer.start()
        else:
            # One-shot
            self.audio.play_sfx(file_path, loop=False)
