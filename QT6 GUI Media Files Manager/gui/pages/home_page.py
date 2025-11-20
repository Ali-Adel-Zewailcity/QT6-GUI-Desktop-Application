from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor

# --- THEME CONFIGURATION ---
THEME_BG = "#1e1e2e"       
THEME_CARD_BG = "#2b2b3b"  
THEME_TEXT = "#cdd6f4"     
THEME_SUBTEXT = "#a6adc8"
THEME_ACCENT = "#89b4fa"   
THEME_PRIMARY = "#74c7ec"
THEME_HOVER = "#313244"
THEME_BORDER = "#45475a"

STYLESHEET = f"""
    QWidget {{
        background-color: {THEME_BG};
        color: {THEME_TEXT};
        font-family: 'Segoe UI', sans-serif;
    }}
    QLabel.title {{
        font-size: 32px;
        font-weight: bold;
        color: {THEME_PRIMARY};
        background: transparent;
    }}
    QLabel.subtitle {{
        font-size: 16px;
        color: {THEME_SUBTEXT};
        background: transparent;
    }}
    QFrame.card {{
        background-color: {THEME_CARD_BG};
        border-radius: 15px;
        border: 1px solid {THEME_BORDER};
    }}
    QFrame.card:hover {{
        background-color: {THEME_HOVER};
        border: 1px solid {THEME_ACCENT};
    }}
    QLabel.card_title {{
        font-size: 18px;
        font-weight: bold;
        color: {THEME_TEXT};
        background: transparent;
    }}
    QLabel.card_desc {{
        font-size: 13px;
        color: {THEME_SUBTEXT};
        background: transparent;
    }}
    QLabel.card_icon {{
        font-size: 40px;
        background: transparent;
    }}
"""

class HomeCard(QFrame):
    """A clickable card widget for the home dashboard."""
    clicked = pyqtSignal()

    def __init__(self, title, description, icon_text, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(160)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(10)
        
        # Icon (Emoji or text based for now)
        icon_lbl = QLabel(icon_text)
        icon_lbl.setProperty("class", "card_icon")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(icon_lbl)
        
        # Text Container
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        
        title_lbl = QLabel(title)
        title_lbl.setProperty("class", "card_title")
        
        desc_lbl = QLabel(description)
        desc_lbl.setProperty("class", "card_desc")
        desc_lbl.setWordWrap(True)
        
        text_layout.addWidget(title_lbl)
        text_layout.addWidget(desc_lbl)
        layout.addLayout(text_layout)
        
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class HomePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(STYLESHEET)
        
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(30)
        
        # --- Header Section ---
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)
        
        title = QLabel("Welcome to Media Files Manager")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Your all-in-one solution for managing, editing, and converting media files.")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)
        
        main_layout.addSpacing(20)
        
        # --- Dashboard Grid Section ---
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        
        # Define actions
        actions = [
            {
                "title": "Download Media",
                "desc": "Download videos, audio, and playlists from YouTube.",
                "icon": "📥",
                "callback": self.main_window.show_download
            },
            {
                "title": "Edit Videos",
                "desc": "Add thumbnails, create GIFs, and extract audio.",
                "icon": "🎬",
                "callback": self.main_window.show_video
            },
            {
                "title": "PDF Tools",
                "desc": "Merge, split, extract images from PDFs.",
                "icon": "📄",
                "callback": self.main_window.show_pdf
            },
            {
                "title": "Edit Audio",
                "desc": "Embed thumbnails and manage audio metadata.",
                "icon": "🎙️",
                "callback": self.main_window.show_audio
            },
            {
                "title": "Rename Files",
                "desc": "Batch rename files and clean up filenames.",
                "icon": "📝",
                "callback": self.main_window.show_rename
            },
            {
                "title": "Image Conversion",
                "desc": "Convert images between formats (JPG, PNG, WEBP).",
                "icon": "🖼️",
                "callback": self.main_window.show_image
            }
        ]
        
        # Create cards and add to grid (2 columns wide)
        row, col = 0, 0
        for action in actions:
            card = HomeCard(action["title"], action["desc"], action["icon"])
            card.clicked.connect(action["callback"])
            grid_layout.addWidget(card, row, col)
            
            col += 1
            if col > 1: # 2 columns
                col = 0
                row += 1
                
        main_layout.addLayout(grid_layout)
        main_layout.addStretch()