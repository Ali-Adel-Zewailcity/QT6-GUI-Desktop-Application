from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QLineEdit, QTextEdit, QFileDialog, QFrame, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor
from cli.File import Directory
from cli.logs import write_log

# --- THEME CONFIGURATION ---
THEME_BG = "#1e1e2e"       
THEME_CARD_BG = "#2b2b3b"  
THEME_TEXT = "#cdd6f4"     
THEME_SUBTEXT = "#a6adc8"
THEME_ACCENT = "#89b4fa"   
THEME_PRIMARY = "#74c7ec"
THEME_SUCCESS = "#a6e3a1"  
THEME_ERROR = "#f38ba8"    
THEME_INPUT_BG = "#313244" 
THEME_BORDER = "#45475a"
THEME_HOVER = "#45475a"

STYLESHEET = f"""
    QWidget {{
        background-color: {THEME_BG};
        color: {THEME_TEXT};
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
    }}
    QFrame.card {{
        background-color: {THEME_CARD_BG};
        border-radius: 15px;
        border: 1px solid {THEME_BORDER};
    }}
    QFrame.card:hover {{
        border: 1px solid {THEME_ACCENT};
    }}
    QLabel.title {{
        font-size: 28px;
        font-weight: bold;
        color: {THEME_PRIMARY};
        background: transparent;
    }}
    QLabel.subtitle {{
        font-size: 16px;
        color: {THEME_SUBTEXT};
        background: transparent;
    }}
    QLineEdit {{
        background-color: {THEME_INPUT_BG};
        border: 2px solid {THEME_BORDER};
        border-radius: 8px;
        padding: 10px;
        color: {THEME_TEXT};
        font-size: 14px;
    }}
    QLineEdit:focus {{
        border: 2px solid {THEME_ACCENT};
    }}
    QPushButton {{
        background-color: {THEME_INPUT_BG};
        border: none;
        border-radius: 10px;
        padding: 12px 20px;
        color: {THEME_TEXT};
        font-weight: bold;
    }}
    QPushButton:hover {{ background-color: {THEME_BORDER}; }}
    QPushButton.primary {{ background-color: {THEME_PRIMARY}; color: #11111b; }}
    QPushButton.primary:hover {{ background-color: {THEME_ACCENT}; }}
    QPushButton.success {{ background-color: {THEME_SUCCESS}; color: #11111b; }}
    QPushButton.success:hover {{ background-color: #81C995; border: 1px solid {THEME_CARD_BG};}}
    QTextEdit {{
        background-color: {THEME_INPUT_BG};
        border-radius: 8px;
        border: 1px solid {THEME_BORDER};
        padding: 8px;
    }}
"""

class RenamePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(STYLESHEET)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(20)
        
        # Header
        header = QVBoxLayout()
        title = QLabel("Batch Rename Files")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Remove or replace characters in filenames across a folder")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(title)
        header.addWidget(subtitle)
        content_layout.addLayout(header)
        
        # Input Card
        card = QFrame()
        card.setProperty("class", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)
        
        # Folder Selection
        card_layout.addWidget(QLabel("Target Folder:"))
        folder_row = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select a directory...")
        browse_btn = QPushButton("Browse")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self.browse_folder)
        folder_row.addWidget(self.folder_input)
        folder_row.addWidget(browse_btn)
        card_layout.addLayout(folder_row)
        
        # Inputs
        card_layout.addWidget(QLabel("Find Characters (Remove):"))
        self.remove_input = QLineEdit()
        self.remove_input.setPlaceholderText("e.g. _copy")
        card_layout.addWidget(self.remove_input)
        
        card_layout.addWidget(QLabel("Replace With (Optional):"))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Leave empty to just delete")
        card_layout.addWidget(self.replace_input)
        
        # Action Button
        process_btn = QPushButton("Rename Files")
        process_btn.setProperty("class", "success")
        process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        process_btn.clicked.connect(self.process_rename)
        card_layout.addWidget(process_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        content_layout.addWidget(card)
        
        # Result Console
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("Renaming logs will appear here...")
        self.result_text.setMaximumHeight(200)
        content_layout.addWidget(self.result_text)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        self.main_layout.addWidget(scroll)
        
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_input.setText(folder)
            
    def process_rename(self):
        folder_path = self.folder_input.text().strip()
        remove = self.remove_input.text()
        replace = self.replace_input.text()
        
        if not folder_path:
            self.main_window.show_error("Please select a folder")
            return
            
        if not remove:
            self.main_window.show_error("Please specify characters to remove")
            return
            
        self.result_text.append(f"⏳ Processing folder: {folder_path}...")
        
        try:
            dir_obj = Directory(folder_path)
            result = dir_obj.allDirectory(remove, replace)
            write_log(result, "Rename")
            
            if result.get('State'):
                files_changed = result.get('File', [])
                if files_changed:
                    self.result_text.append(f"✅ {result.get('Message')}")
                    self.result_text.append("--- Changes ---")
                    for old, new in files_changed:
                        self.result_text.append(f"• {old} → {new}")
                else:
                    self.result_text.append("✅ Process completed. No matching files found.")
            else:
                self.result_text.append(f"❌ Error: {result.get('Error')}")
        except Exception as e:
            self.result_text.append(f"❌ Unexpected Error: {str(e)}")
            
    def reset(self):
        self.folder_input.clear()
        self.remove_input.clear()
        self.replace_input.clear()
        self.result_text.clear()