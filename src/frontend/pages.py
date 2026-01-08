from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QStackedWidget, 
    QLineEdit, QSlider, QGridLayout, QFrame, QHBoxLayout, QGraphicsView,
    QTabWidget, QGroupBox, QFormLayout, QComboBox, QFileDialog, QSpinBox, 
    QCheckBox, QTextEdit, QInputDialog, QDoubleSpinBox, QGraphicsProxyWidget
)
from PySide6.QtCore import Qt, Signal, QDateTime
from PySide6.QtGui import QPixmap, QFontDatabase, QFont, QPainter
import json
import os
import shutil
import re
import qasync
from ..infrastructure import APIClient
from .game_engine import GameEngine

# --- Main Menu ---
class MainMenuPage(QWidget):
    start_signal = Signal()
    load_signal = Signal()
    config_signal = Signal()
    editor_signal = Signal() 
    debug_signal = Signal() # New signal
    exit_signal = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("LLM-Galgame-Engine")
        title.setStyleSheet("font-size: 32px; font-weight: bold; margin-bottom: 50px;")
        layout.addWidget(title)
        
        btn_start = QPushButton("Start Game")
        btn_start.clicked.connect(self.start_signal.emit)
        
        btn_load = QPushButton("Load Game")
        btn_load.clicked.connect(self.load_signal.emit)
        
        btn_config = QPushButton("Config")
        btn_config.clicked.connect(self.config_signal.emit)
        
        btn_editor = QPushButton("Editor (Dev)")
        btn_editor.clicked.connect(self.editor_signal.emit)

        btn_debug = QPushButton("Debug Console")
        btn_debug.clicked.connect(self.debug_signal.emit)
        
        btn_exit = QPushButton("Exit")
        btn_exit.clicked.connect(self.exit_signal.emit)
        
        for btn in [btn_start, btn_load, btn_config, btn_editor, btn_debug, btn_exit]:
            btn.setFixedSize(200, 50)
            layout.addWidget(btn)
            
        self.setLayout(layout)

# --- Config Page ---
class ConfigPage(QWidget):
    back_signal = Signal()

    def __init__(self):
        super().__init__()
        self.config_file = "config.json"
        
        main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # --- Tab 1: AI Settings ---
        self.tab_ai = QWidget()
        layout_ai = QVBoxLayout()
        
        # 1. Storyteller (AI-1)
        group_story = QGroupBox("AI Group 1: Storyteller (剧情生成)")
        form_story = QFormLayout()
        self.url_story = QLineEdit("https://api.openai.com/v1")
        self.key_story = QLineEdit()
        self.key_story.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.model_story_combo = QComboBox()
        self.model_story_combo.setEditable(True)
        self.btn_fetch_story = QPushButton("Fetch Models")
        self.btn_fetch_story.clicked.connect(self.fetch_story_models)
        
        layout_model_story = QHBoxLayout()
        layout_model_story.addWidget(self.model_story_combo)
        layout_model_story.addWidget(self.btn_fetch_story)
        
        self.btn_test_story = QPushButton("Test Connection")
        self.lbl_status_story = QLabel("")
        self.btn_test_story.clicked.connect(self.test_storyteller)
        
        form_story.addRow("Base URL:", self.url_story)
        form_story.addRow("API Key:", self.key_story)
        form_story.addRow("Model:", layout_model_story)
        form_story.addRow(self.btn_test_story, self.lbl_status_story)
        group_story.setLayout(form_story)
        layout_ai.addWidget(group_story)

        # 2. Summary (New)
        group_summary = QGroupBox("AI Group 2: Summary (大小总结)")
        form_summary = QFormLayout()
        self.url_summary = QLineEdit("https://api.openai.com/v1")
        self.key_summary = QLineEdit()
        self.key_summary.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.model_summary_combo = QComboBox()
        self.model_summary_combo.setEditable(True)
        self.btn_fetch_summary = QPushButton("Fetch Models")
        self.btn_fetch_summary.clicked.connect(self.fetch_summary_models)
        
        layout_model_summary = QHBoxLayout()
        layout_model_summary.addWidget(self.model_summary_combo)
        layout_model_summary.addWidget(self.btn_fetch_summary)
        
        self.btn_test_summary = QPushButton("Test Connection")
        self.lbl_status_summary = QLabel("")
        self.btn_test_summary.clicked.connect(self.test_summary)
        
        form_summary.addRow("Base URL:", self.url_summary)
        form_summary.addRow("API Key:", self.key_summary)
        form_summary.addRow("Model:", layout_model_summary)
        form_summary.addRow(self.btn_test_summary, self.lbl_status_summary)
        group_summary.setLayout(form_summary)
        layout_ai.addWidget(group_summary)

        # 3. Logic (Director + Architect)
        group_logic = QGroupBox("AI Group 3: Logic (指令 + 剧情规划)")
        form_logic = QFormLayout()
        self.url_logic = QLineEdit("https://api.openai.com/v1")
        self.key_logic = QLineEdit()
        self.key_logic.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.model_logic_combo = QComboBox()
        self.model_logic_combo.setEditable(True)
        self.btn_fetch_logic = QPushButton("Fetch Models")
        self.btn_fetch_logic.clicked.connect(self.fetch_logic_models)
        
        layout_model_logic = QHBoxLayout()
        layout_model_logic.addWidget(self.model_logic_combo)
        layout_model_logic.addWidget(self.btn_fetch_logic)

        self.btn_test_logic = QPushButton("Test Connection")
        self.lbl_status_logic = QLabel("")
        self.btn_test_logic.clicked.connect(self.test_logic)
        
        form_logic.addRow("Base URL:", self.url_logic)
        form_logic.addRow("API Key:", self.key_logic)
        form_logic.addRow("Model:", layout_model_logic)
        form_logic.addRow(self.btn_test_logic, self.lbl_status_logic)
        group_logic.setLayout(form_logic)
        layout_ai.addWidget(group_logic)
        
        layout_ai.addStretch()
        self.tab_ai.setLayout(layout_ai)
        self.tabs.addTab(self.tab_ai, "AI Configuration")
        
        # --- Tab 2: Audio Settings ---
        self.tab_audio = QWidget()
        layout_audio = QVBoxLayout()
        
        group_vol = QGroupBox("Volume Control")
        form_vol = QFormLayout()
        
        self.bgm_slider = QSlider(Qt.Orientation.Horizontal)
        self.bgm_slider.setRange(0, 100)
        self.sfx_slider = QSlider(Qt.Orientation.Horizontal)
        self.sfx_slider.setRange(0, 100)
        self.voice_slider = QSlider(Qt.Orientation.Horizontal)
        self.voice_slider.setRange(0, 100)
        
        form_vol.addRow("BGM:", self.bgm_slider)
        form_vol.addRow("SFX:", self.sfx_slider)
        form_vol.addRow("Voice:", self.voice_slider)
        group_vol.setLayout(form_vol)
        layout_audio.addWidget(group_vol)
        
        layout_audio.addStretch()
        self.tab_audio.setLayout(layout_audio)
        self.tabs.addTab(self.tab_audio, "Audio")

        # --- Tab 3: Text Settings ---
        self.tab_text = QWidget()
        layout_text = QVBoxLayout()

        group_font = QGroupBox("Font Settings")
        form_font = QFormLayout()

        self.combo_font = QComboBox()
        self.btn_import_font = QPushButton("Import Font (.ttf)")
        self.btn_import_font.clicked.connect(self.import_font)

        layout_font_import = QHBoxLayout()
        layout_font_import.addWidget(self.combo_font)
        layout_font_import.addWidget(self.btn_import_font)

        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(8, 72)
        self.spin_font_size.setValue(16)

        self.chk_font_bold = QCheckBox("Bold")
        
        self.spin_text_speed = QSpinBox()
        self.spin_text_speed.setRange(10, 200)
        self.spin_text_speed.setValue(50)
        self.spin_text_speed.setSuffix(" ms")

        form_font.addRow("Font Family:", layout_font_import)
        form_font.addRow("Font Size:", self.spin_font_size)
        form_font.addRow("Style:", self.chk_font_bold)
        form_font.addRow("Text Speed:", self.spin_text_speed)
        
        group_font.setLayout(form_font)
        layout_text.addWidget(group_font)
        layout_text.addStretch()
        
        self.tab_text.setLayout(layout_text)
        self.tabs.addTab(self.tab_text, "Text")
        
        # --- Tab 4: Prompt Settings ---
        self.tab_prompts = QWidget()
        layout_prompts = QHBoxLayout()
        
        # Left: Summary AI
        layout_p_summary = QVBoxLayout()
        layout_p_summary.addWidget(QLabel("Summary AI Prompt:"))
        self.txt_prompt_summary = QTextEdit()
        layout_p_summary.addWidget(self.txt_prompt_summary)
        layout_prompts.addLayout(layout_p_summary)
        
        # Right: Planner AI
        layout_p_planner = QVBoxLayout()
        layout_p_planner.addWidget(QLabel("Plot Planning AI Prompt:"))
        self.txt_prompt_planner = QTextEdit()
        layout_p_planner.addWidget(self.txt_prompt_planner)
        layout_prompts.addLayout(layout_p_planner)
        
        self.tab_prompts.setLayout(layout_prompts)
        self.tabs.addTab(self.tab_prompts, "Prompts")

        # --- Tab 5: Developer (Presets) ---
        self.tab_dev = QWidget()
        self._init_dev_tab()
        self.tabs.addTab(self.tab_dev, "Developer")

        # --- Footer ---
        btn_back = QPushButton("Save & Back")
        btn_back.clicked.connect(self.save_and_back)
        main_layout.addWidget(btn_back)
        
        self.setLayout(main_layout)
        self.refresh_font_list()
        self.load_config()

    def _init_dev_tab(self):
        layout = QVBoxLayout()
        group_presets = QGroupBox("Sprite Transform Presets (assets/presets.json)")
        form_presets = QFormLayout()
        
        # Zoom Half
        self.spin_zoom = QDoubleSpinBox()
        self.spin_zoom.setRange(0.1, 5.0)
        self.spin_zoom.setSingleStep(0.1)
        form_presets.addRow("Zoom Scale (zoom_half):", self.spin_zoom)
        
        # Center
        self.spin_cx = QSpinBox()
        self.spin_cx.setRange(-2000, 2000)
        self.spin_cy = QSpinBox()
        self.spin_cy.setRange(-2000, 2000)
        l_c = QHBoxLayout()
        l_c.addWidget(QLabel("X:"))
        l_c.addWidget(self.spin_cx)
        l_c.addWidget(QLabel("Y:"))
        l_c.addWidget(self.spin_cy)
        form_presets.addRow("Center Pos (pos_center):", l_c)
        
        # Left
        self.spin_lx = QSpinBox()
        self.spin_lx.setRange(-2000, 2000)
        self.spin_ly = QSpinBox()
        self.spin_ly.setRange(-2000, 2000)
        l_l = QHBoxLayout()
        l_l.addWidget(QLabel("X:"))
        l_l.addWidget(self.spin_lx)
        l_l.addWidget(QLabel("Y:"))
        l_l.addWidget(self.spin_ly)
        form_presets.addRow("Left Pos (pos_left):", l_l)
        
        # Right
        self.spin_rx = QSpinBox()
        self.spin_rx.setRange(-2000, 2000)
        self.spin_ry = QSpinBox()
        self.spin_ry.setRange(-2000, 2000)
        l_r = QHBoxLayout()
        l_r.addWidget(QLabel("X:"))
        l_r.addWidget(self.spin_rx)
        l_r.addWidget(QLabel("Y:"))
        l_r.addWidget(self.spin_ry)
        form_presets.addRow("Right Pos (pos_right):", l_r)
        
        group_presets.setLayout(form_presets)
        layout.addWidget(group_presets)
        layout.addStretch()
        self.tab_dev.setLayout(layout)

    def load_dev_presets(self):
        try:
            with open("assets/presets.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Zoom
                if "zoom_half" in data:
                    self.spin_zoom.setValue(data["zoom_half"].get("scale", 0.5))
                    
                # Center
                if "pos_center" in data:
                    self.spin_cx.setValue(data["pos_center"].get("x", 400))
                    self.spin_cy.setValue(data["pos_center"].get("y", 100))
                
                # Left
                if "pos_left" in data:
                    self.spin_lx.setValue(data["pos_left"].get("x", 100))
                    self.spin_ly.setValue(data["pos_left"].get("y", 100))
                    
                # Right
                if "pos_right" in data:
                    self.spin_rx.setValue(data["pos_right"].get("x", 800))
                    self.spin_ry.setValue(data["pos_right"].get("y", 100))
        except:
            pass

    def save_dev_presets(self):
        data = {
            "zoom_half": {
                "description": "Scale sprite to value",
                "scale": self.spin_zoom.value()
            },
            "pos_center": {
                "description": "Move to Center",
                "x": self.spin_cx.value(),
                "y": self.spin_cy.value()
            },
            "pos_left": {
                "description": "Move to Left",
                "x": self.spin_lx.value(),
                "y": self.spin_ly.value()
            },
            "pos_right": {
                "description": "Move to Right",
                "x": self.spin_rx.value(),
                "y": self.spin_ry.value()
            }
        }
        try:
            with open("assets/presets.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving presets: {e}")

    def import_font(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Font", "", "TrueType Fonts (*.ttf)")
        if file_path:
            try:
                dest_dir = "assets/fonts"
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                
                shutil.copy(file_path, dest_dir)
                self.refresh_font_list()
                
                # Auto select the imported font
                # Need to load it to get family name, or just select by filename logic if simple
                # For now, just refresh list
                
            except Exception as e:
                print(f"Error importing font: {e}")

    def refresh_font_list(self):
        self.combo_font.clear()
        self.combo_font.addItem("Default")
        
        # 1. System Fonts (Optional, maybe too many)
        # db = QFontDatabase()
        # self.combo_font.addItems(db.families())
        
        # 2. Local Assets Fonts
        font_dir = "assets/fonts"
        if os.path.exists(font_dir):
            for f in os.listdir(font_dir):
                if f.lower().endswith(".ttf"):
                    # Try to load application font to get family name
                    font_id = QFontDatabase.addApplicationFont(os.path.join(font_dir, f))
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families:
                        self.combo_font.addItem(families[0])
                    else:
                        # Fallback to filename
                        self.combo_font.addItem(f)

    @qasync.asyncSlot()
    async def fetch_story_models(self):
        await self._fetch_and_populate(self.url_story.text(), self.key_story.text(), self.model_story_combo)

    @qasync.asyncSlot()
    async def fetch_summary_models(self):
        await self._fetch_and_populate(self.url_summary.text(), self.key_summary.text(), self.model_summary_combo)

    @qasync.asyncSlot()
    async def fetch_logic_models(self):
        await self._fetch_and_populate(self.url_logic.text(), self.key_logic.text(), self.model_logic_combo)

    async def _fetch_and_populate(self, url, key, combo_box: QComboBox):
        try:
            combo_box.clear()
            combo_box.addItem("Fetching...")
            client = APIClient(api_keys=[key], base_url=url)
            models = await client.list_models()
            
            combo_box.clear()
            if models:
                combo_box.addItems(models)
            else:
                combo_box.addItem("No models found")
                
        except Exception as e:
            combo_box.clear()
            combo_box.addItem(f"Error: {str(e)}")

    @qasync.asyncSlot()
    async def test_storyteller(self):
        await self._run_test(
            self.url_story.text(), 
            self.key_story.text(), 
            self.model_story_combo.currentText(), 
            self.lbl_status_story
        )

    @qasync.asyncSlot()
    async def test_summary(self):
        await self._run_test(
            self.url_summary.text(), 
            self.key_summary.text(), 
            self.model_summary_combo.currentText(), 
            self.lbl_status_summary
        )

    @qasync.asyncSlot()
    async def test_logic(self):
        await self._run_test(
            self.url_logic.text(), 
            self.key_logic.text(), 
            self.model_logic_combo.currentText(), 
            self.lbl_status_logic
        )

    async def _run_test(self, url, key, model, label_widget):
        label_widget.setText("Testing...")
        label_widget.setStyleSheet("color: blue;")
        
        client = APIClient(api_keys=[key], base_url=url)
        try:
            # Send a simple ping message
            messages = [{"role": "user", "content": "Ping"}]
            response = await client.chat_completion(messages, model=model)
            
            if response:
                label_widget.setText("Success!")
                label_widget.setStyleSheet("color: green; font-weight: bold;")
            else:
                label_widget.setText("Empty Response")
                label_widget.setStyleSheet("color: orange;")
                
        except Exception as e:
            label_widget.setText(f"Failed: {str(e)}")
            label_widget.setStyleSheet("color: red;")

    def save_and_back(self):
        data = {
            # AI 1: Story
            "url_story": self.url_story.text(),
            "key_story": self.key_story.text(),
            "model_story": self.model_story_combo.currentText(),
            # AI 2: Summary
            "url_summary": self.url_summary.text(),
            "key_summary": self.key_summary.text(),
            "model_summary": self.model_summary_combo.currentText(),
            # AI 3: Logic
            "url_logic": self.url_logic.text(),
            "key_logic": self.key_logic.text(),
            "model_logic": self.model_logic_combo.currentText(),
            # Audio
            "vol_bgm": self.bgm_slider.value(),
            "vol_sfx": self.sfx_slider.value(),
            "vol_voice": self.voice_slider.value(),
            # Text
            "font_family": self.combo_font.currentText(),
            "font_size": self.spin_font_size.value(),
            "font_bold": self.chk_font_bold.isChecked(),
            "text_speed": self.spin_text_speed.value(),
            # Prompts
            "prompt_summary": self.txt_prompt_summary.toPlainText(),
            "prompt_planner": self.txt_prompt_planner.toPlainText()
        }
        with open(self.config_file, 'w') as f:
            json.dump(data, f)
            
        self.save_dev_presets()
        self.back_signal.emit()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    # AI 1
                    self.url_story.setText(data.get("url_story", "https://api.openai.com/v1"))
                    self.key_story.setText(data.get("key_story", ""))
                    self.model_story_combo.setCurrentText(data.get("model_story", "gpt-3.5-turbo"))
                    # AI 2
                    self.url_summary.setText(data.get("url_summary", "https://api.openai.com/v1"))
                    self.key_summary.setText(data.get("key_summary", ""))
                    self.model_summary_combo.setCurrentText(data.get("model_summary", "gpt-3.5-turbo"))
                    # AI 3
                    self.url_logic.setText(data.get("url_logic", "https://api.openai.com/v1"))
                    self.key_logic.setText(data.get("key_logic", ""))
                    self.model_logic_combo.setCurrentText(data.get("model_logic", "gpt-4"))
                    
                    # Audio
                    self.bgm_slider.setValue(data.get("vol_bgm", 50))
                    self.sfx_slider.setValue(data.get("vol_sfx", 50))
                    self.voice_slider.setValue(data.get("vol_voice", 50))
                    
                    # Text
                    self.combo_font.setCurrentText(data.get("font_family", "Default"))
                    self.spin_font_size.setValue(data.get("font_size", 16))
                    self.chk_font_bold.setChecked(data.get("font_bold", False))
                    self.spin_text_speed.setValue(data.get("text_speed", 50))
                    
                    # Prompts
                    self.txt_prompt_summary.setText(data.get("prompt_summary", "Summarize this conversation briefly in 2-3 sentences."))
                    default_planner = ("You are the Lead Writer (Architect) for a visual novel. \n"
                                       "Your goal is to analyze the current story state and propose 3 distinct, interesting plot developments.\n"
                                       "Output STRICTLY in JSON format with a key 'options' containing a list of 3 strings.")
                    self.txt_prompt_planner.setText(data.get("prompt_planner", default_planner))
            except:
                pass
        
        self.load_dev_presets()



# --- Save/Load Page ---
class SaveLoadPage(QWidget):
    back_signal = Signal()
    load_game_signal = Signal(str) # filename

    def __init__(self, parent_widget_to_grab=None, memory_manager=None):
        super().__init__()
        self.parent_widget_to_grab = parent_widget_to_grab # Reference to GamePage or MainWindow
        self.memory_manager = memory_manager
        self.temp_screenshot = None
        self.current_page = 1
        self.slots_per_page = 16 # 4x4
        self.save_dir = "saves"
        
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # Header (Back + Pagination)
        header = QHBoxLayout()
        btn_back = QPushButton("Back")
        btn_back.clicked.connect(self.back_signal.emit)
        btn_back.setFixedSize(100, 40)
        
        self.btn_prev = QPushButton("< Prev")
        self.btn_prev.clicked.connect(self.prev_page)
        self.lbl_page = QLabel("Page 1")
        self.lbl_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_next = QPushButton("Next >")
        self.btn_next.clicked.connect(self.next_page)
        
        header.addWidget(btn_back)
        header.addStretch()
        header.addWidget(self.btn_prev)
        header.addWidget(self.lbl_page)
        header.addWidget(self.btn_next)
        
        self.main_layout.addLayout(header)
        
        # Grid for Slots
        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout)
        
        self.refresh_slots()

    def set_temp_screenshot(self, pixmap):
        self.temp_screenshot = pixmap

    def get_file_path(self, slot_id, ext="json"):
        return os.path.join(self.save_dir, f"save_{slot_id}.{ext}")

    def save_game(self, slot_id: int):
        json_path = self.get_file_path(slot_id, "json")
        img_path = self.get_file_path(slot_id, "png")
        
        # 1. Grab Screenshot
        if self.temp_screenshot:
            screenshot = self.temp_screenshot
            screenshot = screenshot.scaled(320, 180, Qt.AspectRatioMode.KeepAspectRatio)
            screenshot.save(img_path)
        elif self.parent_widget_to_grab:
            screenshot = self.parent_widget_to_grab.grab()
            screenshot = screenshot.scaled(320, 180, Qt.AspectRatioMode.KeepAspectRatio)
            screenshot.save(img_path)
        
        # 2. Save Data (Real)
        if self.memory_manager:
            state_data = self.memory_manager.to_dict()
            # Wrap with metadata
            save_data = {
                "meta": {
                    "date": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss"),
                    "summary": self.memory_manager.big_summary[:100] + "..." if self.memory_manager.big_summary else "No summary"
                },
                "game_state": state_data
            }
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=4, ensure_ascii=False)
                print(f"Game saved to {json_path}")
            except Exception as e:
                print(f"Error saving game: {e}")
        else:
            print("Error: Memory Manager not linked, cannot save state.")
            
        self.refresh_slots()

    def load_game(self, slot_id: int):
        json_path = self.get_file_path(slot_id, "json")
        if os.path.exists(json_path):
            self.load_game_signal.emit(json_path)

    def delete_game(self, slot_id: int):
        json_path = self.get_file_path(slot_id, "json")
        img_path = self.get_file_path(slot_id, "png")
        if os.path.exists(json_path):
            os.remove(json_path)
        if os.path.exists(img_path):
            os.remove(img_path)
        self.refresh_slots()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_slots()

    def next_page(self):
        self.current_page += 1
        self.refresh_slots()

    def refresh_slots(self):
        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.lbl_page.setText(f"Page {self.current_page}")
        
        start_index = (self.current_page - 1) * self.slots_per_page + 1
        end_index = start_index + self.slots_per_page
        
        for i in range(start_index, end_index):
            slot_id = i
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.Box)
            f_layout = QVBoxLayout()
            
            # Load Screenshot
            img_path = self.get_file_path(slot_id, "png")
            lbl_img = QLabel()
            if os.path.exists(img_path):
                lbl_img.setPixmap(QPixmap(img_path))
            else:
                lbl_img.setText(f"Slot {slot_id}\n(Empty)")
                lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_img.setFixedSize(160, 90) # Smaller for 4x4
            lbl_img.setScaledContents(True)
            f_layout.addWidget(lbl_img)
            
            # Load Meta
            json_path = self.get_file_path(slot_id, "json")
            
            btn_layout = QHBoxLayout()
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Handle new format vs mock/old format
                    if "meta" in data:
                        date_str = data["meta"].get("date", "Unknown")
                    else:
                        date_str = data.get("date", "Unknown")
                        
                    f_layout.addWidget(QLabel(date_str))
                except:
                    f_layout.addWidget(QLabel("Error"))

                btn_load = QPushButton("Load")
                btn_load.clicked.connect(lambda checked=False, s=slot_id: self.load_game(s))
                
                btn_del = QPushButton("X")
                btn_del.setFixedSize(30, 30)
                btn_del.setStyleSheet("color: red; font-weight: bold;")
                btn_del.clicked.connect(lambda checked=False, s=slot_id: self.delete_game(s))
                
                btn_layout.addWidget(btn_load)
                btn_layout.addWidget(btn_del)
            else:
                f_layout.addWidget(QLabel("--/--/--"))
                btn_save = QPushButton("Save")
                btn_save.clicked.connect(lambda checked=False, s=slot_id: self.save_game(s))
                btn_layout.addWidget(btn_save)
            
            f_layout.addLayout(btn_layout)
            frame.setLayout(f_layout)
            
            # 4x4 Grid Calculation
            local_index = i - start_index
            row = local_index // 4
            col = local_index % 4
            self.grid_layout.addWidget(frame, row, col)

# --- Editor Page ---
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTextEdit, QTreeWidget, QTreeWidgetItem, QSplitter, QMessageBox,
    QHeaderView, QTabWidget, QListWidget, QListWidgetItem, QComboBox,
    QAbstractItemView
)

class EditorPage(QWidget):
    back_signal = Signal()

    def __init__(self):
        super().__init__()
        
        # Main Layout
        main_layout = QVBoxLayout()
        
        # Header
        header = QHBoxLayout()
        lbl_title = QLabel("Universal Prompt Editor")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(lbl_title)
        header.addStretch()
        
        btn_back = QPushButton("Back to Menu")
        btn_back.clicked.connect(self.back_signal.emit)
        btn_back.setFixedSize(120, 40)
        header.addWidget(btn_back)
        
        main_layout.addLayout(header)
        
        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tab 1: File Editor
        self.tab_files = QWidget()
        self._init_file_editor_tab()
        self.tabs.addTab(self.tab_files, "Resource Files")
        
        # Tab 2: Sequence Editor
        self.tab_sequences = QWidget()
        self._init_sequence_editor_tab()
        self.tabs.addTab(self.tab_sequences, "Prompt Sequences")
        
        self.setLayout(main_layout)
        
        # Initial Load
        self.refresh_tree()
        self.refresh_sequences()

    # --- Tab 1: File Editor Logic ---
    def _init_file_editor_tab(self):
        self.current_file_path = None
        layout = QVBoxLayout(self.tab_files)
        
        # Sub-header
        sub_header = QHBoxLayout()
        btn_refresh = QPushButton("Refresh File List")
        btn_refresh.clicked.connect(self.refresh_tree)
        sub_header.addWidget(btn_refresh)
        sub_header.addStretch()
        layout.addLayout(sub_header)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Asset Files")
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tree.setFixedWidth(300)
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        splitter.addWidget(self.tree)
        
        # Right: Editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_current_file = QLabel("No file selected")
        self.lbl_current_file.setStyleSheet("color: gray; font-style: italic;")
        
        self.txt_editor = QTextEdit()
        self.txt_editor.setStyleSheet("font-family: Consolas, monospace; font-size: 14px;")
        
        self.btn_save = QPushButton("Save Changes")
        self.btn_save.setEnabled(False)
        self.btn_save.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_save.clicked.connect(self.save_current_file)
        
        editor_layout.addWidget(self.lbl_current_file)
        editor_layout.addWidget(self.txt_editor)
        editor_layout.addWidget(self.btn_save)
        
        splitter.addWidget(editor_widget)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

    # --- Tab 2: Sequence Editor Logic ---
    def _init_sequence_editor_tab(self):
        layout = QHBoxLayout(self.tab_sequences)
        
        # Left: Sequence Selector & List
        left_layout = QVBoxLayout()
        
        l_header = QHBoxLayout()
        l_header.addWidget(QLabel("Select Function:"))
        self.combo_sequences = QComboBox()
        self.combo_sequences.currentIndexChanged.connect(self.load_selected_sequence)
        l_header.addWidget(self.combo_sequences)
        left_layout.addLayout(l_header)
        
        self.list_sequence = QListWidget()
        self.list_sequence.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        left_layout.addWidget(self.list_sequence)
        
        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("Refresh/Reload")
        btn_refresh.clicked.connect(self.refresh_sequences)
        btn_save = QPushButton("Save Sequence Order")
        btn_save.setStyleSheet("background-color: #2196F3; color: white;")
        btn_save.clicked.connect(self.save_sequence_order)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addWidget(btn_save)
        left_layout.addLayout(btn_layout)
        
        layout.addLayout(left_layout, stretch=2)
        
        # Right: Item Details (Read-only for now, mainly context)
        right_group = QGroupBox("Selected Item Details")
        right_layout = QVBoxLayout()
        self.lbl_item_type = QLabel("Type: -")
        self.lbl_item_key = QLabel("Key/Content: -")
        self.lbl_item_key.setWordWrap(True)
        right_layout.addWidget(self.lbl_item_type)
        right_layout.addWidget(self.lbl_item_key)
        right_layout.addStretch()
        right_group.setLayout(right_layout)
        
        layout.addWidget(right_group, stretch=1)
        
        self.list_sequence.itemClicked.connect(self.show_item_details)

    def refresh_sequences(self):
        self.prompts_data = {}
        try:
            with open("assets/prompts.json", "r", encoding="utf-8") as f:
                self.prompts_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load prompts.json: {e}")
            return

        current_text = self.combo_sequences.currentText()
        self.combo_sequences.blockSignals(True)
        self.combo_sequences.clear()
        
        sequences = self.prompts_data.get("sequences", {})
        for key in sequences.keys():
            self.combo_sequences.addItem(key)
            
        if current_text:
            index = self.combo_sequences.findText(current_text)
            if index >= 0:
                self.combo_sequences.setCurrentIndex(index)
        
        self.combo_sequences.blockSignals(False)
        self.load_selected_sequence()

    def load_selected_sequence(self):
        key = self.combo_sequences.currentText()
        if not key: return
        
        items = self.prompts_data.get("sequences", {}).get(key, [])
        
        self.list_sequence.clear()
        for item_data in items:
            itype = item_data.get("type", "unknown")
            ikey = item_data.get("key") or item_data.get("content", "")[:20] + "..."
            
            display_text = f"[{itype.upper()}] {ikey}"
            
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.ItemDataRole.UserRole, item_data)
            self.list_sequence.addItem(list_item)

    def show_item_details(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        self.lbl_item_type.setText(f"Type: {data.get('type')}")
        content = data.get('key') or data.get('content')
        self.lbl_item_key.setText(f"Key/Content:\n{content}")

    def save_sequence_order(self):
        key = self.combo_sequences.currentText()
        if not key: return
        
        new_list = []
        for i in range(self.list_sequence.count()):
            item = self.list_sequence.item(i)
            new_list.append(item.data(Qt.ItemDataRole.UserRole))
            
        # Update in memory
        self.prompts_data["sequences"][key] = new_list
        
        # Write to file
        try:
            with open("assets/prompts.json", "w", encoding="utf-8") as f:
                json.dump(self.prompts_data, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Success", f"Sequence '{key}' updated.")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    # --- Shared / Tab 1 Implementation ---
    def refresh_tree(self):
        self.tree.clear()
        
        # 1. System Prompts (assets/提示词)
        root_prompts = QTreeWidgetItem(self.tree, ["System Prompts"])
        root_prompts.setExpanded(True)
        self._add_files_to_tree(root_prompts, "assets/提示词")

        # 2. World Setting (assets/世界设定)
        root_world = QTreeWidgetItem(self.tree, ["World Setting"])
        root_world.setExpanded(True)
        self._add_files_to_tree(root_world, "assets/世界设定")

        # 3. User Setting (assets/用户设定)
        root_user = QTreeWidgetItem(self.tree, ["User Setting"])
        root_user.setExpanded(True)
        self._add_files_to_tree(root_user, "assets/用户设定")

        # 4. NPCs
        root_npc = QTreeWidgetItem(self.tree, ["NPCs"])
        root_npc.setExpanded(True)
        
        # Generic NPCs
        node_generic = QTreeWidgetItem(root_npc, ["Generic NPCs"])
        self._add_files_to_tree(node_generic, "assets/NPC人设")
        
        # Important NPCs
        node_important = QTreeWidgetItem(root_npc, ["Important NPCs"])
        imp_path = "assets/NPC人设/重要NPC"
        if os.path.exists(imp_path):
            for folder in os.listdir(imp_path):
                folder_full_path = os.path.join(imp_path, folder)
                if os.path.isdir(folder_full_path):
                    npc_node = QTreeWidgetItem(node_important, [folder])
                    self._add_files_to_tree(npc_node, folder_full_path)

    def _add_files_to_tree(self, parent_item, folder_path):
        if not os.path.exists(folder_path):
            return
            
        for f in sorted(os.listdir(folder_path)):
            full_path = os.path.join(folder_path, f)
            if os.path.isfile(full_path):
                # Only add text/json files
                if f.endswith(('.txt', '.json', '.md')):
                    item = QTreeWidgetItem(parent_item, [f])
                    # Store full path in UserRole
                    item.setData(0, Qt.ItemDataRole.UserRole, full_path)

    def on_tree_item_clicked(self, item, column):
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path:
            self.load_file(file_path)
        else:
            # Clicked a folder item
            self.current_file_path = None
            self.lbl_current_file.setText("Select a file to edit")
            self.txt_editor.clear()
            self.btn_save.setEnabled(False)

    def load_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            self.current_file_path = file_path
            self.lbl_current_file.setText(f"Editing: {file_path}")
            self.txt_editor.setText(content)
            self.btn_save.setEnabled(True)
            
        except Exception as e:
            self.txt_editor.setText(f"Error reading file:\n{e}")
            self.btn_save.setEnabled(False)

    def save_current_file(self):
        if not self.current_file_path:
            return
            
        content = self.txt_editor.toPlainText()
        
        # Simple JSON validation if .json
        if self.current_file_path.endswith(".json"):
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Invalid JSON", f"Format Error: {e}")
                return

        try:
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Flash status or message
            self.lbl_current_file.setText(f"Saved: {self.current_file_path} (Last saved: {QDateTime.currentDateTime().toString('HH:mm:ss')})")
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def refresh_data(self):
        # Called when switching to this page
        self.refresh_tree()
        self.refresh_sequences()


# --- Memory Page ---
class MemoryPage(QWidget):
    back_signal = Signal()
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        # Header
        header = QHBoxLayout()
        lbl_title = QLabel("Memory Review (Story Summaries)")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        header.addWidget(lbl_title)
        header.addStretch()
        
        btn_back = QPushButton("Back")
        btn_back.clicked.connect(self.back_signal.emit)
        btn_back.setFixedSize(100, 40)
        header.addWidget(btn_back)
        
        layout.addLayout(header)
        
        # Content Area (Splitter or just two areas)
        content_layout = QHBoxLayout()
        
        # Left: Big Summary
        group_big = QGroupBox("The Story So Far (Big Summary)")
        group_big.setStyleSheet("QGroupBox { color: white; font-weight: bold; }")
        layout_big = QVBoxLayout()
        self.txt_big = QTextEdit()
        self.txt_big.setReadOnly(True)
        self.txt_big.setStyleSheet("background-color: rgba(0, 0, 0, 0.5); color: white; font-size: 16px;")
        layout_big.addWidget(self.txt_big)
        group_big.setLayout(layout_big)
        
        # Right: Small Summaries
        group_small = QGroupBox("Recent Events (Small Summaries)")
        group_small.setStyleSheet("QGroupBox { color: white; font-weight: bold; }")
        layout_small = QVBoxLayout()
        self.txt_small = QTextEdit()
        self.txt_small.setReadOnly(True)
        self.txt_small.setStyleSheet("background-color: rgba(0, 0, 0, 0.5); color: #ddd; font-size: 14px;")
        layout_small.addWidget(self.txt_small)
        group_small.setLayout(layout_small)
        
        content_layout.addWidget(group_big, stretch=2)
        content_layout.addWidget(group_small, stretch=1)
        
        layout.addLayout(content_layout)
        self.setLayout(layout)
        
    def update_content(self, big_summary, small_summaries):
        self.txt_big.setText(big_summary)
        
        # Format small summaries with bullet points
        lines = []
        for s in small_summaries:
            if isinstance(s, dict):
                lines.append(f"• [{s.get('range', '?')}] {s.get('content', '')}")
            else:
                lines.append(f"• {s}")
        formatted_small = "\n\n".join(lines)
        self.txt_small.setText(formatted_small)


# --- Game Page ---
class GamePage(QWidget):
    config_signal = Signal()
    save_load_signal = Signal()
    save_exit_signal = Signal()
    memory_signal = Signal()
    input_signal = Signal(str)
    input_advance_signal = Signal()
    auto_mode_signal = Signal(bool)
    
    def __init__(self, visual_manager):
        super().__init__()
        self.setStyleSheet("background-color: black;")
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Graphics View
        self.view = QGraphicsView(visual_manager.scene)
        self.view.setStyleSheet("border: none; background-color: black;")
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        self.scene = visual_manager.scene
        self.scene.setSceneRect(0, 0, 1920, 1080)
        
        self.layout.addWidget(self.view)
        
        self._init_scene_ui()

    def _init_scene_ui(self):
        # Dialogue Panel
        self.dialogue_widget = QWidget()
        self.dialogue_widget.setStyleSheet("background-color: transparent;")
        d_layout = QVBoxLayout(self.dialogue_widget)
        d_layout.setContentsMargins(100, 0, 100, 30)
        
        # Text Frame
        self.text_frame = QFrame()
        self.text_frame.setStyleSheet("background-color: rgba(0, 0, 0, 0.85); border: 2px solid #555; border-radius: 15px;")
        self.text_frame.setFixedHeight(260)
        tf_layout = QVBoxLayout(self.text_frame)

        # Top Bar on Text Frame (for Auto button)
        tf_top_bar = QHBoxLayout()
        tf_top_bar.addStretch()
        self.btn_auto = QPushButton("Auto")
        self.btn_auto.setCheckable(True)
        self.btn_auto.setStyleSheet("""
            QPushButton { background-color: #333; color: white; border: 1px solid #555; padding: 5px 10px; border-radius: 5px; }
            QPushButton:checked { background-color: #007acc; color: white; }
        """)
        self.btn_auto.clicked.connect(lambda checked: self.auto_mode_signal.emit(checked))
        tf_top_bar.addWidget(self.btn_auto)
        tf_layout.addLayout(tf_top_bar)
        
        self.name_label = QLabel("Loading...")
        self.name_label.setStyleSheet("color: #FFD700; font-family: 'Microsoft YaHei'; font-size: 28px; font-weight: bold; background: transparent; border: none;")
        
        self.content_label = QLabel("")
        self.content_label.setStyleSheet("color: white; font-family: 'Microsoft YaHei'; font-size: 24px; background: transparent; border: none;")
        self.content_label.setWordWrap(True)
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        tf_layout.addWidget(self.name_label)
        tf_layout.addWidget(self.content_label)
        tf_layout.addStretch()
        
        d_layout.addWidget(self.text_frame)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your response here...")
        self.input_field.setStyleSheet("background-color: rgba(255, 255, 255, 0.95); border: 2px solid #888; border-radius: 5px; padding: 5px 10px; font-size: 20px; color: black;")
        self.input_field.returnPressed.connect(self.handle_input)
        d_layout.addWidget(self.input_field)
        
        self.dialogue_widget.resize(1920, 350)
        
        self.proxy_ui = self.scene.addWidget(self.dialogue_widget)
        self.proxy_ui.setPos(0, 1080 - 350)
        self.proxy_ui.setZValue(100)
        
        # Top Menu
        # ... (rest of the UI init is the same)
        self.top_menu_widget = QWidget()
        tm_layout = QHBoxLayout(self.top_menu_widget)
        tm_layout.setContentsMargins(0, 10, 20, 0)
        tm_layout.addStretch()
        
        btn_style = "QPushButton { background-color: rgba(0, 0, 0, 0.6); color: white; border: 1px solid #888; border-radius: 5px; padding: 5px 15px; font-size: 16px; } QPushButton:hover { background-color: rgba(50, 50, 50, 0.9); border-color: white; }"
        
        self.btn_config = QPushButton("Settings")
        self.btn_config.setStyleSheet(btn_style)
        self.btn_config.clicked.connect(self.config_signal.emit)
        
        self.btn_memory = QPushButton("Memory")
        self.btn_memory.setStyleSheet(btn_style)
        self.btn_memory.clicked.connect(self.memory_signal.emit)

        self.btn_sl = QPushButton("Save/Load")
        self.btn_sl.setStyleSheet(btn_style)
        self.btn_sl.clicked.connect(self.save_load_signal.emit)
        
        self.btn_exit = QPushButton("Exit")
        self.btn_exit.setStyleSheet(btn_style)
        self.btn_exit.clicked.connect(self.save_exit_signal.emit)
        
        tm_layout.addWidget(self.btn_config)
        tm_layout.addWidget(self.btn_memory)
        tm_layout.addWidget(self.btn_sl)
        tm_layout.addWidget(self.btn_exit)
        
        self.top_menu_widget.resize(1920, 60)
        self.proxy_menu = self.scene.addWidget(self.top_menu_widget)
        self.proxy_menu.setPos(0, 0)
        self.proxy_menu.setZValue(101)

        self.proxy_ui.setVisible(False)
        self.proxy_menu.setVisible(False)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space or event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.input_advance_signal.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Avoid triggering if clicking on input field or buttons
            if self.input_field.geometry().contains(event.pos()):
                 super().mousePressEvent(event)
                 return
            
            self.input_advance_signal.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.view.fitInView(0, 0, 1920, 1080, Qt.AspectRatioMode.KeepAspectRatio)

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, 'proxy_ui'):
            self.proxy_ui.setVisible(True)
        if hasattr(self, 'proxy_menu'):
            self.proxy_menu.setVisible(True)
        self.view.fitInView(0, 0, 1920, 1080, Qt.AspectRatioMode.KeepAspectRatio)

    def hideEvent(self, event):
        super().hideEvent(event)
        if hasattr(self, 'proxy_ui'):
            self.proxy_ui.setVisible(False)
        if hasattr(self, 'proxy_menu'):
            self.proxy_menu.setVisible(False)

    def set_text(self, name: str, content: str):
        self.name_label.setText(name)
        self.content_label.setText(content)

    def update_style(self, font_family, font_size, font_bold):
        font = QFont()
        if font_family and font_family != "Default":
            font.setFamily(font_family)
        
        font.setPointSize(font_size + 4) 
        if font_bold:
            font.setWeight(QFont.Weight.Black)
        else:
            font.setWeight(QFont.Weight.Bold)
        self.name_label.setFont(font)
        
        font.setPointSize(font_size)
        if font_bold:
            font.setWeight(QFont.Weight.Bold)
        else:
            font.setWeight(QFont.Weight.Normal)
        self.content_label.setFont(font)

    def handle_input(self):
        text = self.input_field.text().strip()
        if text:
            self.input_signal.emit(text)
            self.input_field.clear()

# --- Debug Page ---
class DebugPage(QWidget):
    back_signal = Signal()
    
    def __init__(self, visual_manager, audio_manager):
        super().__init__()
        self.layout = QVBoxLayout()
        
        # Header
        header = QHBoxLayout()
        lbl_title = QLabel("Debug Console (Test Instructions)")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(lbl_title)
        header.addStretch()
        
        btn_back = QPushButton("Back")
        btn_back.clicked.connect(self.on_back)
        header.addWidget(btn_back)
        self.layout.addLayout(header)
        
        # Visual View (Shared Visual Manager)
        self.visual = visual_manager
        self.audio = audio_manager
        
        # Engine (Standalone for debug)
        try:
            self.engine = GameEngine(self.visual, self.audio, None)
            self.engine.text_updated.connect(self.on_text_updated)
        except Exception as e:
            print(f"Error initializing DebugPage engine: {e}")
            self.lbl_output.setText(f"Engine Init Error: {e}")
        
        # Graphics View
        self.view = QGraphicsView(self.visual.scene)
        self.layout.addWidget(self.view, stretch=3)
        
        # Text Output Overlay (Simple Label)
        self.lbl_output = QLabel("Output text will appear here...")
        self.lbl_output.setStyleSheet("background-color: rgba(0,0,0,0.5); color: white; padding: 10px; font-size: 16px;")
        self.lbl_output.setWordWrap(True)
        self.layout.addWidget(self.lbl_output)
        
        # Input Area
        input_layout = QHBoxLayout()
        self.txt_input = QTextEdit()
        self.txt_input.setPlaceholderText("Enter instructions here... (e.g. Hello [fg-chiguo-happy] [Sprite-chiguo-pos_center])")
        self.txt_input.setMaximumHeight(80)
        
        btn_run = QPushButton("Run / Send")
        btn_run.setFixedSize(100, 80)
        btn_run.clicked.connect(self.run_instruction)
        
        input_layout.addWidget(self.txt_input)
        input_layout.addWidget(btn_run)
        self.layout.addLayout(input_layout)
        
        self.setLayout(self.layout)

    def on_back(self):
        if self.audio:
            self.audio.stop_bgm()
        self.back_signal.emit()

    def run_instruction(self):
        text = self.txt_input.toPlainText()
        if not text.strip():
            return
            
        print(f"[Debug] Running: {text}")
        # Call parse directly
        self.engine._start_sequence(text)
        self.txt_input.clear()

    def on_text_updated(self, name, content):
        self.lbl_output.setText(f"{name}: {content}")
