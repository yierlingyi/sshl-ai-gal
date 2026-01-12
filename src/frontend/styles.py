
MAIN_STYLESHEET = """
/* Global */
QWidget {
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 16px;
}

QMainWindow {
    background-color: #121212;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #1e1e1e;
    width: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #444;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    border: none;
    background: #1e1e1e;
    height: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:horizontal {
    background: #444;
    min-width: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #333;
    background: #1e1e1e;
}
QTabBar::tab {
    background: #2b2b2b;
    color: #aaa;
    padding: 8px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #3e3e3e;
    color: white;
    font-weight: bold;
    border-bottom: 2px solid #3498db;
}
QTabBar::tab:hover {
    background: #333;
}

/* Buttons - General */
QPushButton {
    background-color: #2b2b2b;
    border: 1px solid #3e3e3e;
    border-radius: 4px;
    padding: 6px 12px;
    color: #e0e0e0;
}
QPushButton:hover {
    background-color: #3e3e3e;
    border-color: #555;
}
QPushButton:pressed {
    background-color: #1a1a1a;
}
QPushButton:disabled {
    background-color: #1a1a1a;
    color: #555;
    border-color: #222;
}

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: #1a1a1a;
    border: 1px solid #333;
    border-radius: 4px;
    padding: 4px;
    color: #fff;
    selection-background-color: #3498db;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #3498db;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #333;
    border-radius: 6px;
    margin-top: 20px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #bbb;
}

/* List/Tree/Table */
QListWidget, QTreeWidget, QTableWidget {
    background-color: #1a1a1a;
    border: 1px solid #333;
    alternate-background-color: #222;
}
QHeaderView::section {
    background-color: #2b2b2b;
    padding: 4px;
    border: 1px solid #333;
    color: #ddd;
}
QTableWidget::item:selected, QListWidget::item:selected, QTreeWidget::item:selected {
    background-color: #3498db;
    color: white;
}
"""

MENU_BUTTON_STYLE = """
QPushButton {
    background-color: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 10px;
    color: white;
    font-size: 18px;
    text-align: center;
}
QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.3);
    border-color: white;
    font-weight: bold;
}
QPushButton:pressed {
    background-color: rgba(0, 0, 0, 0.8);
}
"""

GAME_TEXT_FRAME_STYLE = """
QFrame {
    background-color: rgba(0, 0, 0, 0.85);
    border: 2px solid #555;
    border-radius: 12px;
}
"""

GAME_INPUT_STYLE = """
QLineEdit {
    background-color: rgba(30, 30, 30, 0.9);
    border: 1px solid #555;
    border-radius: 4px;
    color: white;
    font-size: 18px;
    padding: 5px;
}
QLineEdit:focus {
    border: 1px solid #3498db;
    background-color: rgba(40, 40, 40, 0.95);
}
"""

SAVE_SLOT_STYLE = """
QFrame {
    background-color: #2a2a2a;
    border: 1px solid #333;
    border-radius: 8px;
}
QFrame:hover {
    border: 1px solid #3498db;
    background-color: #333;
}
"""
