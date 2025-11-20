from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QLineEdit, QTextEdit, QFileDialog, QComboBox, QFrame, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor
from cli.images import ImageOperations
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
    QLineEdit, QComboBox {{
        background-color: {THEME_INPUT_BG};
        border: 2px solid {THEME_BORDER};
        border-radius: 8px;
        padding: 10px;
        color: {THEME_TEXT};
        font-size: 14px;
    }}
    QLineEdit:focus, QComboBox:focus {{
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
    QPushButton.success {{ background-color: {THEME_SUCCESS}; color: #11111b; }}
    QPushButton.success:hover {{ background-color: #81C995; border: 1px solid {THEME_CARD_BG};}}
    QTextEdit {{
        background-color: {THEME_INPUT_BG};
        border-radius: 8px;
        border: 1px solid {THEME_BORDER};
        padding: 8px;
    }}
"""

class ImagePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(STYLESHEET)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(20)
        
        # Header
        header = QVBoxLayout()
        title = QLabel("Image Converter")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Convert between common image formats")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(title)
        header.addWidget(subtitle)
        content_layout.addLayout(header)
        
        # Supported Types info
        supported = QLabel(f"Supported Formats: {', '.join(ImageOperations._supported)}")
        supported.setStyleSheet(f"color: {THEME_SUBTEXT}; margin-bottom: 10px;")
        supported.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(supported)
        
        # Card
        card = QFrame()
        card.setProperty("class", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)
        
        card_layout.addWidget(QLabel("Source Image:"))
        file_row = QHBoxLayout()
        self.image_path_input = QLineEdit()
        self.image_path_input.setPlaceholderText("Select an image file...")
        browse_btn = QPushButton("Browse")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self.browse_image)
        file_row.addWidget(self.image_path_input)
        file_row.addWidget(browse_btn)
        card_layout.addLayout(file_row)
        
        card_layout.addWidget(QLabel("Convert To:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(ImageOperations._supported)
        card_layout.addWidget(self.format_combo)
        
        process_btn = QPushButton("Convert Image")
        process_btn.setProperty("class", "success")
        process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        process_btn.clicked.connect(self.process_conversion)
        card_layout.addWidget(process_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        content_layout.addWidget(card)
        
        # Console
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("Conversion log...")
        self.result_text.setMaximumHeight(150)
        content_layout.addWidget(self.result_text)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        self.main_layout.addWidget(scroll)
        
    def browse_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Image File", "", 
                                             "Image Files (*.jpg *.jpeg *.png *.webp *.ico *.bmp)")
        if file:
            self.image_path_input.setText(file)
            
    def process_conversion(self):
        image_path = self.image_path_input.text().strip()
        convert_to = self.format_combo.currentText()
        
        if not image_path:
            self.main_window.show_error("Please select an image file")
            return
            
        self.result_text.append(f"⏳ Converting to {convert_to}...")
        
        try:
            img = ImageOperations(image_path)
            result = img.convert_image(convert_to)
            write_log(result, 'Image')
            
            if result.get('State'):
                self.result_text.append(f"✅ {result.get('Message')}")
            else:
                self.result_text.append(f"❌ Error: {result.get('Error')}")
        except Exception as e:
            self.result_text.append(f"❌ Unexpected Error: {str(e)}")
            
    def reset(self):
        self.image_path_input.clear()
        self.result_text.clear()
        self.format_combo.setCurrentIndex(0)