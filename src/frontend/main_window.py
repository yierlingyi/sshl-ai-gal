import sys
import asyncio
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QGraphicsScene
from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QFontDatabase, QFont
import qasync
import re

from .visual_manager import VisualManager
from .audio_manager import AudioManager
from .game_engine import GameEngine
from .pages import MainMenuPage, ConfigPage, SaveLoadPage, GamePage, MemoryPage, EditorPage, DebugPage
from ..llm_chain import LLMChain

import json
import os

class MainWindow(QMainWindow):
    memory_updated_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LLM-Galgame-Engine (LLM Galgame 引擎)")
        self.resize(1280, 720)
        
        # 1. Managers
        self.scene = QGraphicsScene(0, 0, 1920, 1080)
        self.visual = VisualManager(self.scene)
        self.audio = AudioManager()
        
        self.config = {}
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    self.config = json.load(f)
            except:
                pass

        self.backend = LLMChain(config=self.config)
        self.engine = GameEngine(self.visual, self.audio, self.backend)
        
        # 2. Pages Stack
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # 3. Create Pages
        self.page_main = MainMenuPage()
        self.page_config = ConfigPage()
        self.page_save = SaveLoadPage(parent_widget_to_grab=self, memory_manager=self.backend.memory) # Pass self for screenshot
        self.page_game = GamePage(self.visual)
        self.page_memory = MemoryPage()
        self.page_editor = EditorPage()
        self.page_debug = DebugPage(self.visual, self.audio) # Index 8
        
        # In-Game Sub-pages
        self.page_game_config = ConfigPage()
        self.page_game_save = SaveLoadPage(parent_widget_to_grab=self.page_game, memory_manager=self.backend.memory)
        
        self.stack.addWidget(self.page_main) # Index 0
        self.stack.addWidget(self.page_config) # Index 1
        self.stack.addWidget(self.page_save) # Index 2
        self.stack.addWidget(self.page_game) # Index 3
        self.stack.addWidget(self.page_game_config) # Index 4
        self.stack.addWidget(self.page_game_save) # Index 5
        self.stack.addWidget(self.page_memory) # Index 6
        self.stack.addWidget(self.page_editor) # Index 7
        self.stack.addWidget(self.page_debug) # Index 8
        
        # 4. Connect Signals
        # Main Menu
        self.page_main.start_signal.connect(lambda: self.switch_to(3))
        self.page_main.config_signal.connect(lambda: self.switch_to(1))
        self.page_main.load_signal.connect(self.on_main_load)
        self.page_main.editor_signal.connect(lambda: self.switch_to(7))
        self.page_main.debug_signal.connect(lambda: self.switch_to(8))
        self.page_main.exit_signal.connect(self.close)
        
        # Menu Config
        self.page_config.back_signal.connect(self.on_config_back)
        
        # Menu Save/Load
        self.page_save.back_signal.connect(lambda: self.switch_to(0)) # Or previous
        self.page_save.load_game_signal.connect(self.load_game)
        
        # Game Page
        self.page_game.config_signal.connect(lambda: self.switch_to(4))
        self.page_game.save_load_signal.connect(self.on_game_menu)
        self.page_game.save_exit_signal.connect(self.on_save_exit)
        self.page_game.memory_signal.connect(lambda: self.switch_to(6))
        self.page_game.input_signal.connect(self.engine.handle_turn)
        self.page_game.input_advance_signal.connect(self.engine.user_advance_slot)
        self.page_game.auto_mode_signal.connect(self.engine.set_auto_mode_slot)
        self.engine.text_updated.connect(self.page_game.set_text)
        
        # Game Config
        self.page_game_config.back_signal.connect(self.on_game_config_back)
        
        # Game Save/Load
        self.page_game_save.back_signal.connect(lambda: self.switch_to(3))
        self.page_game_save.load_game_signal.connect(self.load_game)
        
        # Memory Page
        self.page_memory.back_signal.connect(lambda: self.switch_to(3))
        
        # Editor Page
        self.page_editor.back_signal.connect(lambda: self.switch_to(0))
        
        # Debug Page
        self.page_debug.back_signal.connect(lambda: self.switch_to(0))
        
        # Memory Observer Setup
        self.memory_updated_signal.connect(self.on_memory_updated)
        self.backend.memory.add_observer(self.memory_updated_signal.emit)
        
        self.reload_config()

    def on_memory_updated(self):
        big = self.backend.memory.big_summary
        small = self.backend.memory.small_summaries
        self.page_memory.update_content(big, small)

    def reload_config(self):
        self.config = {}
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    self.config = json.load(f)
            except:
                pass
        
        # Load Fonts
        font_dir = "assets/fonts"
        if os.path.exists(font_dir):
            for f in os.listdir(font_dir):
                if f.lower().endswith(".ttf"):
                    QFontDatabase.addApplicationFont(os.path.join(font_dir, f))

        # Apply Audio Settings
        self.audio.set_bgm_volume(self.config.get("vol_bgm", 50) / 100.0)
        self.audio.set_sfx_volume(self.config.get("vol_sfx", 50) / 100.0)
        self.audio.set_voice_volume(self.config.get("vol_voice", 50) / 100.0)
        
        # Apply Global Font Settings
        font_family = self.config.get("font_family", "Default")
        font_size = self.config.get("font_size", 16)
        font_bold = self.config.get("font_bold", False)

        app_font = QFont()
        if font_family and font_family != "Default":
            app_font.setFamily(font_family)
        app_font.setPointSize(font_size)
        app_font.setBold(font_bold)
        QApplication.instance().setFont(app_font)

        # Apply Text Settings (Specific to GamePage)
        self.page_game.update_style(
            font_family,
            font_size,
            font_bold
        )

        # Apply text speed
        self.engine.set_text_speed(self.config.get("text_speed", 50))

    def on_config_back(self):
        self.reload_config()
        self.switch_to(0)

    def on_game_config_back(self):
        self.reload_config()
        self.switch_to(3)
        
    def switch_to(self, index):
        print(f"Switching to page index: {index}")
        if index == 1: # Menu Config
            self.page_config.load_config()
        elif index == 2: # Menu Save/Load
            self.page_save.refresh_slots()
        elif index == 4: # Game Config
            self.page_game_config.load_config()
        elif index == 5: # Game Save/Load
            self.page_game_save.refresh_slots()
        elif index == 6: # Memory Page
            self.on_memory_updated() # Force refresh when opening
        elif index == 7: # Editor Page
            self.page_editor.refresh_data()
            
        self.stack.setCurrentIndex(index)

    def on_game_menu(self):
        self.page_game_save.set_temp_screenshot(self.page_game.grab())
        self.switch_to(5) # Switch to In-Game Save Page
        
    def on_save_exit(self):
        self.page_game_save.set_temp_screenshot(self.page_game.grab())
        
        # Determine next slot ID
        max_id = 0
        save_dir = "saves"
        if os.path.exists(save_dir):
            for f in os.listdir(save_dir):
                match = re.match(r"save_(\d+)\.json", f)
                if match:
                    max_id = max(max_id, int(match.group(1)))
                    
        next_slot = max_id + 1
        print(f"Auto-saving to slot {next_slot} and exiting...")
        self.page_game_save.save_game(next_slot)
        
        # Stop Music
        self.audio.stop_bgm()
        
        self.switch_to(0)

    def on_main_load(self):
        self.page_save.set_temp_screenshot(None)
        self.switch_to(2)
        
    def load_game(self, filename):
        print(f"Loading {filename}...")
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            state_data = None
            if "game_state" in data:
                state_data = data["game_state"]
            else:
                # Fallback for old/mock format? Or just ignore
                print("Invalid save file format (missing game_state).")
                return

            if state_data:
                self.backend.memory.load_from_dict(state_data)
                # Refresh UI
                self.page_game.set_text("系统", "游戏已读取。")
                self.on_memory_updated()
                self.switch_to(3) # Go to Game
                
        except Exception as e:
            print(f"Error loading game: {e}")

def main():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = MainWindow()
    window.show()
    
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
