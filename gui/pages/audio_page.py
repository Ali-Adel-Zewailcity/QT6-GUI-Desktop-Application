from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QLineEdit, QTextEdit, QFileDialog, QComboBox, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import time
from PyQt6.QtGui import QFont, QCursor
from cli.File import Directory
from cli.video import Audio, embed_thumbnail_in_folder
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

class AudioPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.active_workers = []
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
        title = QLabel("Audio Tools")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Embed thumbnails into audio files or entire albums")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(title)
        header.addWidget(subtitle)
        content_layout.addLayout(header)
        
        # Card
        card = QFrame()
        card.setProperty("class", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)
        
        # Mode Selection (Replaced Radio Buttons with ComboBox)
        card_layout.addWidget(QLabel("Operation Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Single File", "Batch (Folder)"])
        self.mode_combo.currentIndexChanged.connect(self._update_placeholders)
        card_layout.addWidget(self.mode_combo)
        
        # Audio Path
        card_layout.addWidget(QLabel("Source:"))
        audio_row = QHBoxLayout()
        self.audio_path_input = QLineEdit()
        self._update_placeholders(0) # Init text
        browse_btn = QPushButton("Browse")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self.browse_audio_or_folder)
        audio_row.addWidget(self.audio_path_input)
        audio_row.addWidget(browse_btn)
        card_layout.addLayout(audio_row)
        
        # Image Path
        card_layout.addWidget(QLabel("Thumbnail Image:"))
        img_row = QHBoxLayout()
        self.image_path_input = QLineEdit()
        self.image_path_input.setPlaceholderText("Select image (JPG, PNG)... or Enter URL of Image")
        browse_img_btn = QPushButton("Browse Image")
        browse_img_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_img_btn.clicked.connect(lambda: self.browse_file(self.image_path_input, "Image"))
        img_row.addWidget(self.image_path_input)
        img_row.addWidget(browse_img_btn)
        card_layout.addLayout(img_row)
        
        # Action Button
        process_btn = QPushButton("Embed Thumbnail")
        process_btn.setProperty("class", "success")
        process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        process_btn.clicked.connect(self.process_thumbnail)
        card_layout.addWidget(process_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        content_layout.addWidget(card)
        
        # Console
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("Log output...")
        self.result_text.setMaximumHeight(150)
        content_layout.addWidget(self.result_text)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        self.main_layout.addWidget(scroll)

    def _update_placeholders(self, index):
        if index == 0:
            self.audio_path_input.setPlaceholderText("Select an audio file (MP3, FLAC, M4A)...")
        else:
            self.audio_path_input.setPlaceholderText("Select a folder containing audio files...")
            
    def browse_audio_or_folder(self):
        # 0: Single, 1: Batch
        if self.mode_combo.currentIndex() == 0:
            file, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", 
                                                  "Audio Files (*.mp3 *.flac *.m4a *.mka)")
            if file:
                self.audio_path_input.setText(file)
        else:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder")
            if folder:
                self.audio_path_input.setText(folder)
                
    def browse_file(self, input_widget, file_type="Image"):
        file, _ = QFileDialog.getOpenFileName(self, "Select Image File", "", 
                                             "Image Files (*.jpg *.jpeg *.png *.webp)")
        if file:
            input_widget.setText(file)
            
    def process_thumbnail(self):
        audio_path = self.audio_path_input.text().strip()
        image_path = self.image_path_input.text().strip()
        
        if not all([audio_path, image_path]):
            self.main_window.show_error("Please fill in all fields")
            return
            
        self.result_text.append("⏳ Processing...")
        try:
            image = ImageOperations(image_path)

            if self.mode_combo.currentIndex() == 0:
                audio = Audio(audio_path)
                result = audio.embed_thumbnail_audio(image)
                write_log(result, 'Audio')

                if result.get('State'):
                    self.result_text.append(f"✅ {result.get('Message')}\nSaved to: {result.get('Save Location')}")
                else:
                    self.result_text.append(f"❌ Error: {result.get('Error')}")
            else:
                folder = Directory(audio_path)
                self.result_text.append(f"📂 Batch processing folder: {folder.basename}...")

                # Run batch embedding in background
                class AudioBatchWorker(QThread):
                    progress = pyqtSignal(str)
                    finished = pyqtSignal(dict)

                    def __init__(self, folder_path: str, image_path: str):
                        super().__init__()
                        self.folder_path = folder_path
                        self.image_path = image_path

                    def run(self):
                        try:
                            folder = Directory(self.folder_path)
                            image = ImageOperations(self.image_path)
                            res = embed_thumbnail_in_folder(folder, image, 'Audio', progress_callback=lambda m: self.progress.emit(m))
                            self.finished.emit(res)
                        except Exception as e:
                            now = time.ctime()
                            self.finished.emit({'File': self.folder_path, 'Process': 'Embed Thumbnail in Audio', 'State': 0,
                                                'Error': str(e), 'Datetime': now})

                worker = AudioBatchWorker(audio_path, image_path)
                self.active_workers.append(worker)
                worker.progress.connect(lambda m: self.result_text.append(m))

                def on_finished(res):
                    write_log(res, 'Audio')
                    if res.get('State'):
                        self.result_text.append(f"✅ {res.get('Message')}\nSaved to: {res.get('Save Location')}")
                    else:
                        self.result_text.append(f"❌ Error: {res.get('Error')}")
                    try:
                        self.active_workers.remove(worker)
                    except ValueError:
                        pass

                worker.finished.connect(on_finished)
                worker.start()
        except Exception as e:
             self.result_text.append(f"❌ Unexpected Error: {str(e)}")
            
    def reset(self):
        self.audio_path_input.clear()
        self.image_path_input.clear()
        self.result_text.clear()
