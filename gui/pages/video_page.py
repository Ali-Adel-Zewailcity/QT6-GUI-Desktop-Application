from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel,
                             QLineEdit, QTextEdit, QFileDialog, QComboBox, QFrame, QScrollArea, QStackedWidget)
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
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(STYLESHEET)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # Menu
        self.menu_widget = self._create_menu()
        self.stack.addWidget(self.menu_widget)

        # Thumbnail Page
        self.thumbnail_widget, self.thumb_mode, self.thumb_video_input, self.thumb_image_input, self.thumb_result = self._create_thumbnail_page()
        self.stack.addWidget(self.thumbnail_widget)

        # GIF Page
        self.gif_widget, self.gif_video_input, self.gif_start, self.gif_end, self.gif_scale, self.gif_result = self._create_gif_page()
        self.stack.addWidget(self.gif_widget)

        # Extract Audio Page
        self.extract_widget, self.extract_mode, self.extract_input, self.extract_result = self._create_extract_page()
        self.stack.addWidget(self.extract_widget)

    def go_to_menu(self):
        self.stack.setCurrentIndex(0)

    def show_thumbnail(self):
        self.stack.setCurrentIndex(1)

    def show_gif(self):
        self.stack.setCurrentIndex(2)

    def show_extract_audio(self):
        self.stack.setCurrentIndex(3)

    def _create_menu(self):
        widget = QWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(30)

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

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(scroll)

        return widget

    def _create_base_subpage(self, title_text):
        widget = QWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        header = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(100, 40)
        back_btn.setProperty("class", "back")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.go_to_menu)

        title = QLabel(title_text)
        title.setProperty("class", "title")

        header.addWidget(back_btn)
        header.addStretch()
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QWidget())
        layout.addLayout(header)

        card = QFrame()
        card.setProperty("class", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)

        layout.addWidget(card)

        result_text = QTextEdit()
        result_text.setReadOnly(True)
        result_text.setPlaceholderText("Process output will appear here...")
        result_text.setMaximumHeight(150)
        layout.addWidget(result_text)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0,0,0,0)
        outer.addWidget(scroll)

        return widget, card_layout, result_text

    def _create_thumbnail_page(self):
        widget, layout, result_text = self._create_base_subpage("Change Video Thumbnail")

        layout.addWidget(QLabel("Mode:"))
        mode_combo = QComboBox()
        mode_combo.addItems(["Single File", "Batch (Folder)"])
        # Note: We can't easily connect to instance method here before returning,
        # but we can use a lambda or setup connection later.
        # To keep it clean, I'll defer connection or use a wrapper.
        layout.addWidget(mode_combo)

        layout.addWidget(QLabel("Source Path:"))
        source_row = QHBoxLayout()
        video_path_input = QLineEdit()
        video_path_input.setPlaceholderText("Select a video file...")

        # Connect update placeholder
        mode_combo.currentIndexChanged.connect(lambda idx: video_path_input.setPlaceholderText(
            "Select a video file..." if idx == 0 else "Select a folder containing videos..."
        ))

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self.browse_video_or_folder(mode_combo, video_path_input))
        source_row.addWidget(video_path_input)
        source_row.addWidget(browse_btn)
        layout.addLayout(source_row)

        layout.addWidget(QLabel("Thumbnail Image:"))
        img_row = QHBoxLayout()
        image_path_input = QLineEdit()
        image_path_input.setPlaceholderText("Select image (JPG, PNG, WEBP)... or Enter URL of Image")
        browse_img_btn = QPushButton("Browse Image")
        browse_img_btn.clicked.connect(lambda: self.browse_file(image_path_input, "Image"))
        img_row.addWidget(image_path_input)
        img_row.addWidget(browse_img_btn)
        layout.addLayout(img_row)

        process_btn = QPushButton("Embed Thumbnail")
        process_btn.setProperty("class", "success")
        process_btn.clicked.connect(self.process_thumbnail)
        layout.addWidget(process_btn, alignment=Qt.AlignmentFlag.AlignRight)

        return widget, mode_combo, video_path_input, image_path_input, result_text

    def _create_gif_page(self):
        widget, layout, result_text = self._create_base_subpage("Generate GIF")

        layout.addWidget(QLabel("Video File:"))
        file_row = QHBoxLayout()
        video_path_input = QLineEdit()
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self.browse_file(video_path_input, "Video"))
        file_row.addWidget(video_path_input)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        time_row = QHBoxLayout()

        start_layout = QVBoxLayout()
        start_layout.addWidget(QLabel("Start Time:"))
        start_time_input = QLineEdit()
        start_time_input.setPlaceholderText("00:00:10")
        start_layout.addWidget(start_time_input)

        end_layout = QVBoxLayout()
        end_layout.addWidget(QLabel("End Time:"))
        end_time_input = QLineEdit()
        end_time_input.setPlaceholderText("00:00:20")
        end_layout.addWidget(end_time_input)

        time_row.addLayout(start_layout)
        time_row.addLayout(end_layout)
        layout.addLayout(time_row)

        layout.addWidget(QLabel("Scale Width (optional):"))
        scale_input = QLineEdit()
        scale_input.setPlaceholderText("e.g. 480 (Leave empty for original size)")
        layout.addWidget(scale_input)

        process_btn = QPushButton("Generate GIF")
        process_btn.setProperty("class", "success")
        process_btn.clicked.connect(self.process_gif)
        layout.addWidget(process_btn, alignment=Qt.AlignmentFlag.AlignRight)

        return widget, video_path_input, start_time_input, end_time_input, scale_input, result_text

    def _create_extract_page(self):
        widget, layout, result_text = self._create_base_subpage("Extract Audio")

        layout.addWidget(QLabel("Mode:"))
        extract_mode_combo = QComboBox()
        extract_mode_combo.addItems(["Single File", "Batch (Folder)"])
        layout.addWidget(extract_mode_combo)

        layout.addWidget(QLabel("Source Path:"))
        file_row = QHBoxLayout()
        video_path_input = QLineEdit()
        video_path_input.setPlaceholderText("Select a video file...")

        extract_mode_combo.currentIndexChanged.connect(lambda idx: video_path_input.setPlaceholderText(
            "Select a video file..." if idx == 0 else "Select a folder containing videos..."
        ))

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self.browse_extract_source(extract_mode_combo, video_path_input))

        file_row.addWidget(video_path_input)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        process_btn = QPushButton("Extract Audio")
        process_btn.setProperty("class", "success")
        process_btn.clicked.connect(self.process_extract_audio)
        layout.addWidget(process_btn, alignment=Qt.AlignmentFlag.AlignRight)

        return widget, extract_mode_combo, video_path_input, result_text

    # --- Helper Functions ---
    def browse_video_or_folder(self, combo, input_widget):
        # 0: Single File, 1: Batch
        if combo.currentIndex() == 0:
            file, _ = QFileDialog.getOpenFileName(self, "Select Video File", "",
                                                  "Video Files (*.mp4 *.mkv *.avi *.mov)")
            if file:
                input_widget.setText(file)
        else:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder")
            if folder:
                input_widget.setText(folder)

    def browse_file(self, input_widget, file_type="Video"):
        if file_type == "Video":
            file, _ = QFileDialog.getOpenFileName(self, "Select Video File", "",
                                                  "Video Files (*.mp4 *.mkv *.avi *.mov)")
        else:
            file, _ = QFileDialog.getOpenFileName(self, "Select Image File", "",
                                                  "Image Files (*.jpg *.jpeg *.png *.webp)")
        if file:
            input_widget.setText(file)

    def browse_extract_source(self, combo, input_widget):
        if combo.currentIndex() == 0:
            file, _ = QFileDialog.getOpenFileName(self, "Select Video File", "",
                                                  "Video Files (*.mp4 *.mkv *.avi *.mov)")
            if file:
                input_widget.setText(file)
        else:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder")
            if folder:
                input_widget.setText(folder)

    # --- Process Logic ---
    def process_thumbnail(self):
        path = self.thumb_video_input.text().strip()
        image_path = self.thumb_image_input.text().strip()

        if not all([path, image_path]):
            self.main_window.show_error("Please fill in all fields")
            return

        self.thumb_result.append("⏳ Processing thumbnail embedding...")
        image = ImageOperations(image_path)

        if self.thumb_mode.currentIndex() == 0:
            vid = Video(path)
            result = vid.embed_thumbnail_video(image)
            write_log(result, 'Video')

            if result.get('State'):
                self.thumb_result.append(f"✅ {result.get('Message')}\nSaved to: {result.get('Save Location')}")
            else:
                self.thumb_result.append(f"❌ Error: {result.get('Error')}")
        else:
            folder = Directory(path)
            result = embed_thumbnail_in_folder(folder, image, 'Video')
            write_log(result, 'Video')

            if result.get('State'):
                self.thumb_result.append(f"✅ {result.get('Message')}\nSaved to: {result.get('Save Location')}")
            else:
                self.thumb_result.append(f"❌ Error: {result.get('Error')}")

    def process_gif(self):
        video_path = self.gif_video_input.text().strip()
        start_time = self.gif_start.text().strip()
        end_time = self.gif_end.text().strip()
        scale = self.gif_scale.text().strip() or None

        if not all([video_path, start_time, end_time]):
            self.main_window.show_error("Please fill in all required fields")
            return

        self.gif_result.append("⏳ Generating GIF...")
        vid = Video(video_path)
        result = vid.generate_gif(start_time, end_time, scale)
        write_log(result, 'Video')

        if result.get('State'):
            self.gif_result.append(f"✅ {result.get('Message')}\nSaved to: {result.get('Save Location')}")
        else:
            self.gif_result.append(f"❌ Error: {result.get('Error')}")

    def process_extract_audio(self):
        path = self.extract_input.text().strip()

        if not path:
            self.main_window.show_error("Please select a source")
            return

        is_batch = self.extract_mode.currentIndex() == 1

        if not is_batch:
            self.extract_result.append("⏳ Extracting audio...")
            vid = Video(path)
            result = vid.extract_original_audio()
            write_log(result, 'Video')

            if result.get('State'):
                self.extract_result.append(f"✅ {result.get('Message')}\nSaved to: {result.get('Save Location')}")
            else:
                self.extract_result.append(f"❌ Error: {result.get('Error')}")

        else:
            folder = Directory(path)
            if not folder.isdir():
                self.extract_result.append(f"❌ Error: Directory not found at {path}")
                return

            self.extract_result.append(f"📂 Batch processing folder: {folder.basename}...")

            success_count = 0
            fail_count = 0
            supported_exts = Video._supported

            files = folder.list_dir()
            if not files:
                 self.extract_result.append("⚠️ Folder is empty.")
                 return

            for filename in files:
                path_builder = Directory(path)
                path_builder.join(filename)
                vid = Video(str(path_builder))

                if vid.ext.lower() in supported_exts:
                    self.extract_result.append(f"➡️ Processing: {filename}...")
                    result = vid.extract_original_audio()
                    write_log(result, 'Video')

                    if result.get('State'):
                        self.extract_result.append(f"   ✅ Extracted")
                        success_count += 1
                    else:
                        self.extract_result.append(f"   ❌ Failed: {result.get('Error')}")
                        fail_count += 1

            self.extract_result.append(f"\n🏁 Batch Complete. Success: {success_count}, Failed: {fail_count}")

    def reset(self):
        # Optional: Reset inputs only if desired, but user asked to persist state on navigation.
        # The reset() function was previously called by MainWindow to show menu and clear layout.
        # Now MainWindow calls go_to_menu().
        # We can keep reset() as a way to explicitly clear inputs if we add a "Reset" button,
        # or just leave it empty or remove it.
        pass
