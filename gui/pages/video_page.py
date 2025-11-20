from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                             QLineEdit, QTextEdit, QFileDialog, QComboBox, QFrame, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor
from cli.File import Directory
from cli.video import Video, embed_thumbnail_in_folder
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
    QPushButton.primary {{ background-color: {THEME_PRIMARY}; color: #11111b; }}
    QPushButton.primary:hover {{ background-color: {THEME_ACCENT}; }}
    QPushButton.success {{ background-color: {THEME_SUCCESS}; color: #11111b; }}
    QPushButton.success:hover {{ background-color: #81C995; border: 1px solid {THEME_CARD_BG};}}
    QPushButton.back {{ background-color: transparent; border: 1px solid {THEME_BORDER}; color: {THEME_TEXT}; }}
    QPushButton.back:hover {{ background-color: {THEME_BORDER}; }}
    QTextEdit {{
        background-color: {THEME_INPUT_BG};
        border-radius: 8px;
        border: 1px solid {THEME_BORDER};
        padding: 8px;
    }}
"""

class VideoToolCard(QFrame):
    def __init__(self, title, desc, icon, callback, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(150)
        self.callback = callback
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Icon & Title Row
        top_row = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 32px; background: transparent;")
        title_lbl = QLabel(title)
        title_lbl.setProperty("class", "card_title")
        
        top_row.addWidget(icon_lbl)
        top_row.addWidget(title_lbl)
        top_row.addStretch()
        layout.addLayout(top_row)
        
        # Description
        desc_lbl = QLabel(desc)
        desc_lbl.setProperty("class", "card_desc")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.callback()

class VideoPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.current_view = "menu"
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(STYLESHEET)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.show_menu()
        
    def show_menu(self):
        self.clear_layout()
        self.current_view = "menu"
        
        # Scroll Area for Menu
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(30)
        
        # Header
        header = QVBoxLayout()
        title = QLabel("Video Tools")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Manage thumbnails, convert to GIF, and extract audio")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(title)
        header.addWidget(subtitle)
        content_layout.addLayout(header)
        
        # Grid of Tools
        grid = QGridLayout()
        grid.setSpacing(20)
        
        tools = [
            ("Change Thumbnail", "Embed custom thumbnails into video files or batch process folders.", "🖼️", self.show_thumbnail),
            ("Generate GIF", "Create animated GIFs from specific segments of your videos.", "🎞️", self.show_gif),
            ("Extract Audio", "Rip high-quality audio tracks from video files.", "🔊", self.show_extract_audio)
        ]
        
        row, col = 0, 0
        for title, desc, icon, func in tools:
            card = VideoToolCard(title, desc, icon, func)
            grid.addWidget(card, row, col)
            col += 1
            if col > 1: # 2 columns
                col = 0
                row += 1
        
        content_layout.addLayout(grid)
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        self.main_layout.addWidget(scroll)
        
    def _setup_page(self, title_text):
        self.clear_layout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header with Back Button
        header = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(100, 40)
        back_btn.setProperty("class", "back")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.show_menu)
        
        title = QLabel(title_text)
        title.setProperty("class", "title")
        
        header.addWidget(back_btn)
        header.addStretch()
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QWidget()) 
        layout.addLayout(header)
        
        # Card Container for Inputs
        card = QFrame()
        card.setProperty("class", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)
        
        layout.addWidget(card)
        
        # Result Console
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("Process output will appear here...")
        self.result_text.setMaximumHeight(150)
        layout.addWidget(self.result_text)
        
        layout.addStretch()
        scroll.setWidget(content)
        self.main_layout.addWidget(scroll)
        
        return card_layout

    def show_thumbnail(self):
        layout = self._setup_page("Change Video Thumbnail")
        
        layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Single File", "Batch (Folder)"])
        self.mode_combo.currentIndexChanged.connect(self._update_thumbnail_placeholder)
        layout.addWidget(self.mode_combo)
        
        layout.addWidget(QLabel("Source Path:"))
        source_row = QHBoxLayout()
        self.video_path_input = QLineEdit()
        self._update_thumbnail_placeholder(0) # Initialize placeholder
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_video_or_folder)
        source_row.addWidget(self.video_path_input)
        source_row.addWidget(browse_btn)
        layout.addLayout(source_row)
        
        layout.addWidget(QLabel("Thumbnail Image:"))
        img_row = QHBoxLayout()
        self.image_path_input = QLineEdit()
        self.image_path_input.setPlaceholderText("Select image (JPG, PNG, WEBP)... or Enter URL of Image")
        browse_img_btn = QPushButton("Browse Image")
        browse_img_btn.clicked.connect(lambda: self.browse_file(self.image_path_input, "Image"))
        img_row.addWidget(self.image_path_input)
        img_row.addWidget(browse_img_btn)
        layout.addLayout(img_row)
        
        process_btn = QPushButton("Embed Thumbnail")
        process_btn.setProperty("class", "success")
        process_btn.clicked.connect(self.process_thumbnail)
        layout.addWidget(process_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _update_thumbnail_placeholder(self, index):
        if index == 0:
            self.video_path_input.setPlaceholderText("Select a video file...")
        else:
            self.video_path_input.setPlaceholderText("Select a folder containing videos...")

    def show_gif(self):
        layout = self._setup_page("Generate GIF")
        
        layout.addWidget(QLabel("Video File:"))
        file_row = QHBoxLayout()
        self.video_path_input = QLineEdit()
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self.browse_file(self.video_path_input, "Video"))
        file_row.addWidget(self.video_path_input)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)
        
        time_row = QHBoxLayout()
        
        start_layout = QVBoxLayout()
        start_layout.addWidget(QLabel("Start Time:"))
        self.start_time_input = QLineEdit()
        self.start_time_input.setPlaceholderText("00:00:10")
        start_layout.addWidget(self.start_time_input)
        
        end_layout = QVBoxLayout()
        end_layout.addWidget(QLabel("End Time:"))
        self.end_time_input = QLineEdit()
        self.end_time_input.setPlaceholderText("00:00:20")
        end_layout.addWidget(self.end_time_input)
        
        time_row.addLayout(start_layout)
        time_row.addLayout(end_layout)
        layout.addLayout(time_row)
        
        layout.addWidget(QLabel("Scale Width (optional):"))
        self.scale_input = QLineEdit()
        self.scale_input.setPlaceholderText("e.g. 480 (Leave empty for original size)")
        layout.addWidget(self.scale_input)
        
        process_btn = QPushButton("Generate GIF")
        process_btn.setProperty("class", "success")
        process_btn.clicked.connect(self.process_gif)
        layout.addWidget(process_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
    def show_extract_audio(self):
        layout = self._setup_page("Extract Audio")
        
        # 1. Add Mode Selection
        layout.addWidget(QLabel("Mode:"))
        self.extract_mode_combo = QComboBox()
        self.extract_mode_combo.addItems(["Single File", "Batch (Folder)"])
        self.extract_mode_combo.currentIndexChanged.connect(self._update_extract_placeholder)
        layout.addWidget(self.extract_mode_combo)
        
        # 2. Input Selection
        layout.addWidget(QLabel("Source Path:"))
        file_row = QHBoxLayout()
        self.video_path_input = QLineEdit()
        self._update_extract_placeholder(0) # Set initial placeholder
        
        browse_btn = QPushButton("Browse")
        # Connect to a specific browse function that checks the combo box state
        browse_btn.clicked.connect(self.browse_extract_source)
        
        file_row.addWidget(self.video_path_input)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)
        
        process_btn = QPushButton("Extract Audio")
        process_btn.setProperty("class", "success")
        process_btn.clicked.connect(self.process_extract_audio)
        layout.addWidget(process_btn, alignment=Qt.AlignmentFlag.AlignRight)

    # --- Helper Functions ---
    def browse_video_or_folder(self):
        # 0: Single File, 1: Batch
        if self.mode_combo.currentIndex() == 0:
            file, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", 
                                                  "Video Files (*.mp4 *.mkv *.avi *.mov)")
            if file:
                self.video_path_input.setText(file)
        else:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder")
            if folder:
                self.video_path_input.setText(folder)
                
    def browse_file(self, input_widget, file_type="Video"):
        if file_type == "Video":
            file, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", 
                                                  "Video Files (*.mp4 *.mkv *.avi *.mov)")
        else:
            file, _ = QFileDialog.getOpenFileName(self, "Select Image File", "", 
                                                  "Image Files (*.jpg *.jpeg *.png *.webp)")
        if file:
            input_widget.setText(file)

    def _update_extract_placeholder(self, index):
        if index == 0:
            self.video_path_input.setPlaceholderText("Select a video file...")
        else:
            self.video_path_input.setPlaceholderText("Select a folder containing videos...")

    def browse_extract_source(self):
        # Check the specific combo box for audio extraction
        if self.extract_mode_combo.currentIndex() == 0:
            # Single File
            file, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", 
                                                  "Video Files (*.mp4 *.mkv *.avi *.mov)")
            if file:
                self.video_path_input.setText(file)
        else:
            # Batch Folder
            folder = QFileDialog.getExistingDirectory(self, "Select Folder")
            if folder:
                self.video_path_input.setText(folder)

    # --- Process Logic ---
    def process_thumbnail(self):
        path = self.video_path_input.text().strip()
        image_path = self.image_path_input.text().strip()
        
        if not all([path, image_path]):
            self.main_window.show_error("Please fill in all fields")
            return
            
        self.result_text.append("⏳ Processing thumbnail embedding...")
        image = ImageOperations(image_path)
        
        # 0: Single File, 1: Batch
        if self.mode_combo.currentIndex() == 0:
            vid = Video(path)
            result = vid.embed_thumbnail_video(image)
            write_log(result, 'Video')
            
            if result.get('State'):
                self.result_text.append(f"✅ {result.get('Message')}\nSaved to: {result.get('Save Location')}")
            else:
                self.result_text.append(f"❌ Error: {result.get('Error')}")
        else:
            folder = Directory(path)
            result = embed_thumbnail_in_folder(folder, image, 'Video')
            write_log(result, 'Video')
            
            if result.get('State'):
                self.result_text.append(f"✅ {result.get('Message')}\nSaved to: {result.get('Save Location')}")
            else:
                self.result_text.append(f"❌ Error: {result.get('Error')}")
                
    def process_gif(self):
        video_path = self.video_path_input.text().strip()
        start_time = self.start_time_input.text().strip()
        end_time = self.end_time_input.text().strip()
        scale = self.scale_input.text().strip() or None
        
        if not all([video_path, start_time, end_time]):
            self.main_window.show_error("Please fill in all required fields")
            return
        
        self.result_text.append("⏳ Generating GIF...")
        vid = Video(video_path)
        result = vid.generate_gif(start_time, end_time, scale)
        write_log(result, 'Video')
        
        if result.get('State'):
            self.result_text.append(f"✅ {result.get('Message')}\nSaved to: {result.get('Save Location')}")
        else:
            self.result_text.append(f"❌ Error: {result.get('Error')}")
            
    def process_extract_audio(self):
        path = self.video_path_input.text().strip()
        
        if not path:
            self.main_window.show_error("Please select a source")
            return

        # Check Mode: 0 = Single, 1 = Batch
        is_batch = self.extract_mode_combo.currentIndex() == 1

        if not is_batch:
            # --- SINGLE FILE LOGIC (Unchanged) ---
            self.result_text.append("⏳ Extracting audio...")
            vid = Video(path)
            result = vid.extract_original_audio()
            write_log(result, 'Video')
            
            if result.get('State'):
                self.result_text.append(f"✅ {result.get('Message')}\nSaved to: {result.get('Save Location')}")
            else:
                self.result_text.append(f"❌ Error: {result.get('Error')}")

        else:
            # --- BATCH LOGIC (Fixed) ---
            folder = Directory(path)
            if not folder.isdir():
                self.result_text.append(f"❌ Error: Directory not found at {path}")
                return

            self.result_text.append(f"📂 Batch processing folder: {folder.basename}...")
            
            success_count = 0
            fail_count = 0
            
            # Get list of supported extensions directly from Video class
            supported_exts = Video._supported 

            files = folder.list_dir()
            if not files:
                 self.result_text.append("⚠️ Folder is empty.")
                 return

            for filename in files:
                # 1. Build the full path using Directory helper
                path_builder = Directory(path)
                path_builder.join(filename)
                
                # 2. Create a Video object immediately to access .ext
                # (The Video class inherits 'ext' from File)
                vid = Video(str(path_builder))
                
                # 3. Check extension on the Video object, NOT the Directory object
                if vid.ext.lower() in supported_exts:
                    self.result_text.append(f"➡️ Processing: {filename}...")
                    
                    # Perform Extraction
                    result = vid.extract_original_audio()
                    write_log(result, 'Video')
                    
                    if result.get('State'):
                        self.result_text.append(f"   ✅ Extracted")
                        success_count += 1
                    else:
                        self.result_text.append(f"   ❌ Failed: {result.get('Error')}")
                        fail_count += 1
            
            self.result_text.append(f"\n🏁 Batch Complete. Success: {success_count}, Failed: {fail_count}")

    def clear_layout(self):
        if self.main_layout.count():
            for i in reversed(range(self.main_layout.count())):
                item = self.main_layout.takeAt(i)
                if item.widget():
                    item.widget().deleteLater()
                
    def reset(self):
        self.show_menu()