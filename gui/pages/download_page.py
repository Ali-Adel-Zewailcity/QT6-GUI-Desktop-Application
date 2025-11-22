from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QComboBox, QCheckBox, QTextEdit,
                             QGroupBox, QScrollArea, QFrame, QTableWidget, QTableWidgetItem,
                             QProgressBar, QDialog, QDialogButtonBox, QSpinBox, QMessageBox,
                             QHeaderView, QAbstractItemView, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QItemSelectionModel
from PyQt6.QtGui import QFont, QColor, QCursor, QFontMetrics
import yt_dlp
import re
import os
import winsound  # For sound notifications
from time import ctime
from cli.logs import write_log
from cli.File import Directory
from .history_page import HistoryPage
from .fetch_info_worker import FetchInfoWorker

# --- GLOBAL STYLESHEET VARIABLES ---
THEME_BG = "#1e1e2e"
THEME_CARD_BG = "#2b2b3b"
THEME_TEXT = "#cdd6f4"
THEME_ACCENT = "#89b4fa"
THEME_PRIMARY = "#74c7ec"
THEME_SUCCESS = "#a6e3a1"
THEME_ERROR = "#f38ba8"
THEME_INPUT_BG = "#313244"
THEME_BORDER = "#A6ADC8"

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
    QLabel.title {{
        font-size: 45px;
        font-weight: bold;
        color: {THEME_PRIMARY};
        background: transparent;
    }}
    QLabel {{ background: transparent; }}
    QLineEdit, QSpinBox, QComboBox {{
        background-color: {THEME_INPUT_BG};
        border: 2px solid {THEME_BORDER};
        border-radius: 8px;
        padding: 10px;
        color: {THEME_TEXT};
        font-size: 14px;
    }}
    QLineEdit:disabled, QSpinBox:disabled {{
        background-color: #252630;
        color: #6c7086;
        border: 2px solid #45475a;
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 2px solid {THEME_ACCENT};
    }}

    /* --- SPINBOX ARROWS FIX --- */
    QSpinBox::up-button {{
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 15px;
        border-left: 1px solid {THEME_BORDER};
        border-top-right-radius: 6px;
        background: {THEME_INPUT_BG};
    }}
    QSpinBox::down-button {{
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 15px;
        border-left: 1px solid {THEME_BORDER};
        border-bottom-right-radius: 6px;
        background: {THEME_INPUT_BG};
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: {THEME_BORDER};
    }}
    QSpinBox::up-arrow {{
        image: url(assets/arrow-up.svg);
        width: 12px;
        height: 12px;
    }}
    QSpinBox::down-arrow {{
        image: url(assets/arrow-down.svg);
        width: 12px;
        height: 12px;
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
    QPushButton:pressed {{ background-color: {THEME_ACCENT}; color: {THEME_BG}; }}
    QPushButton.primary {{ background-color: {THEME_PRIMARY}; color: #11111b; }}
    QPushButton.primary:hover {{ background-color: {THEME_ACCENT}; }}
    QPushButton.success {{ background-color: {THEME_SUCCESS}; color: #11111b; }}
    QPushButton.success:hover {{ background-color: #81C995; border: 1px solid {THEME_CARD_BG};}}
    QPushButton.cancel {{
        background-color: #d20f39;
        color: #11111b;
        padding: 8px 15px;
        font-size: 13px;
    }}
    QPushButton.cancel:hover {{ background-color: {THEME_ERROR}; }}
    QPushButton.back {{ background-color: transparent; border: 1px solid {THEME_BORDER}; color: {THEME_TEXT}; }}
    QPushButton.back:hover {{ background-color: {THEME_BORDER}; }}
    QTableWidget {{
        background-color: {THEME_INPUT_BG};
        border-radius: 8px;
        gridline-color: {THEME_BORDER};
        border: 1px solid {THEME_BORDER};
    }}
    QHeaderView::section {{
        background-color: {THEME_CARD_BG};
        padding: 8px;
        border: none;
        font-weight: bold;
    }}
    QTableWidget::item:selected {{ background-color: {THEME_ACCENT}; color: #11111b; }}
    QScrollArea {{ border: none; background: transparent; }}
    QTextEdit {{
        background-color: {THEME_INPUT_BG};
        border-radius: 8px;
        border: 1px solid {THEME_BORDER};
        padding: 8px;
    }}
    QProgressBar {{
        border: 2px solid {THEME_BORDER};
        border-radius: 10px;
        background-color: {THEME_INPUT_BG};
        font-weight: bold;
        color: white; /* default visible text */
        padding: 0px;
        text-align: center;
    }}

    /* Filled part */
    QProgressBar::chunk {{
        background-color: {THEME_ACCENT};
        border-radius: 8px;
    }}

    QCheckBox {{
        spacing: 8px;
        background: transparent;
        color: {THEME_TEXT};
    }}
    QCheckBox::indicator {{
        width: 14px;
        height: 14px;
        border: 2px solid {THEME_BORDER};
        border-radius: 4px;
        background: transparent;
    }}
    QCheckBox::indicator:checked {{
        background-color: {THEME_ACCENT};
        border-color: {THEME_ACCENT};
        image: none;
    }}
"""

class YtdlpLogger:
    """Custom logger to capture yt-dlp output and emit it as a signal."""
    def __init__(self, log_signal):
        self.log_signal = log_signal

    def debug(self, msg):
        if msg.startswith('[download]'):
            return
        self.log_signal.emit(msg)

    def warning(self, msg):
        self.log_signal.emit(f"⚠️ {msg}")

    def error(self, msg):
        self.log_signal.emit(f"❌ {msg}")

class DownloadWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(dict)
    log_message = pyqtSignal(str)

    def __init__(self, url, ydl_opts):
        super().__init__()
        self.url = url
        self.ydl_opts = ydl_opts

    def run(self):
        try:
            self.ydl_opts['logger'] = YtdlpLogger(self.log_message)
            self.ydl_opts['quiet'] = False
            self.ydl_opts['progress_hooks'] = [self.progress_hook]
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([self.url])
            self.finished.emit({'State': True, 'Message': 'Download completed successfully'})
        except yt_dlp.utils.DownloadError as e:
            self.finished.emit({'State': False, 'Error': f'Download Error: {str(e)}'})
        except Exception as e:
            self.finished.emit({'State': False, 'Error': f'Unexpected error: {str(e)}'})

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            self.progress.emit(d)

class FormatSelectionDialog(QDialog):
    def __init__(self, formats, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Format")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(STYLESHEET)
        self.available_ids = set()

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        header = QLabel("Select Download Format")
        header.setProperty("class", "title")
        layout.addWidget(header)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['ID', 'Ext', 'Resolution', 'Note', 'Codec', 'Size'])
        self.table.setRowCount(len(formats))
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

        for row, fmt in enumerate(formats):
            fmt_id = str(fmt[0])
            self.available_ids.add(fmt_id)
            for col, value in enumerate(fmt):
                item = QTableWidgetItem(str(value) if value else '-')
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table)

        # Manual Input
        input_frame = QFrame()
        input_frame.setProperty("class", "card")
        input_layout = QVBoxLayout(input_frame)

        lbl_row = QHBoxLayout()
        lbl_row.addWidget(QLabel("Manual Format ID:"))
        self.format_input = QLineEdit()
        self.format_input.setPlaceholderText("e.g. 137+140 or bestvideo+bestaudio")
        lbl_row.addWidget(self.format_input)
        input_layout.addLayout(lbl_row)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {THEME_ERROR}; font-weight: bold; font-size: 13px;")
        self.error_label.setVisible(False)
        input_layout.addWidget(self.error_label)

        layout.addWidget(input_frame)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "back")
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("Confirm Selection")
        ok_btn.setProperty("class", "primary")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.confirm_selection)

        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(ok_btn)
        layout.addLayout(buttons_layout)

    def on_selection_changed(self):
        selected_rows = self.table.selectionModel().selectedRows()

        # Limit selection to 2 rows
        if len(selected_rows) > 2:
            self.table.blockSignals(True) # Prevent recursion
            to_deselect = selected_rows[-1]
            self.table.selectionModel().select(
                to_deselect,
                QItemSelectionModel.SelectionFlag.Deselect | QItemSelectionModel.SelectionFlag.Rows
            )
            self.table.blockSignals(False)
            selected_rows = self.table.selectionModel().selectedRows()

        # Sort by the original row index to maintain a consistent order
        sorted_rows = sorted(selected_rows, key=lambda item: item.row())
        format_ids = [self.table.item(row.row(), 0).text() for row in sorted_rows]

        self.format_input.setText('+'.join(format_ids))
        self.error_label.setVisible(False)

    def confirm_selection(self):
        text = self.format_input.text().strip()
        if not text:
            self.accept()
            return

        if (re.match(r'^[0-9+]+$', "+".join([i.strip() for i in text.split("+") if i.strip() not in self.available_ids]))):
            ids = text.split('+')
            invalid_ids = []

            for fmt_id in ids:
                clean_id = fmt_id.strip()
                if clean_id and clean_id not in self.available_ids:
                    invalid_ids.append(clean_id)

            if invalid_ids:
                self.error_label.setText(f"❌ Invalid Format IDs: {', '.join(invalid_ids)}. Please select valid formats from the table.")
                self.error_label.setVisible(True)
                return

        self.accept()

    def get_selected_format(self):
        if self.format_input.text():
            return self.format_input.text()
        return "bestvideo+bestaudio"

class DownloadOptionsDialog(QDialog):
    def __init__(self, media_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Options")
        self.setMinimumWidth(550)
        self.setStyleSheet(STYLESHEET)
        self.media_type = media_type

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        layout.addWidget(QLabel("Configuration", objectName="title_label"))

        card = QFrame()
        card.setProperty("class", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)

        # Merge Options
        merge_layout = QHBoxLayout()
        merge_layout.addWidget(QLabel("Merge/Convert to:"))
        self.merge_combo = QComboBox()
        self.merge_combo.addItems(['original', 'mp4', 'mp3'])
        merge_layout.addWidget(self.merge_combo, 1)
        card_layout.addLayout(merge_layout)

        # Subtitles
        sub_layout = QVBoxLayout()
        self.subtitle_check = QCheckBox("Embed Subtitles")
        sub_layout.addWidget(self.subtitle_check)

        self.subtitle_input = QLineEdit()
        self.subtitle_input.setPlaceholderText("Languages (e.g., en,ar)")
        self.subtitle_input.setEnabled(False)
        sub_layout.addWidget(self.subtitle_input)
        card_layout.addLayout(sub_layout)

        self.subtitle_check.toggled.connect(self.subtitle_input.setEnabled)
        layout.addWidget(card)

        # Playlist Specific Options
        if media_type == "playlist":
            playlist_card = QFrame()
            playlist_card.setProperty("class", "card")
            p_layout = QVBoxLayout(playlist_card)
            p_layout.addWidget(QLabel("Playlist Settings"))

            self.playlist_option = QComboBox()
            self.playlist_option.addItems(['Download All', 'Limit Count (playlistend)', 'Specific Items (playlist_items)'])
            p_layout.addWidget(self.playlist_option)

            self.playlist_limit_spin = QSpinBox()
            self.playlist_limit_spin.setRange(1, 9999)
            self.playlist_limit_spin.setValue(10)
            self.playlist_limit_spin.setEnabled(False)

            self.playlist_items_input = QLineEdit()
            self.playlist_items_input.setPlaceholderText("Index e.g. 1,2,5-10")
            self.playlist_items_input.setEnabled(False)

            stack_layout = QVBoxLayout()
            stack_layout.addWidget(self.playlist_limit_spin)
            stack_layout.addWidget(self.playlist_items_input)
            p_layout.addLayout(stack_layout)

            quality_layout = QHBoxLayout()
            quality_layout.addWidget(QLabel("Type / Quality:"))
            self.quality_combo = QComboBox()
            self.quality_combo.addItems(['Audio Only (Best)', '2160p', '1440p', '1080p', '720p', '480p', '360p'])
            self.quality_combo.setCurrentText('1080p')
            quality_layout.addWidget(self.quality_combo)
            p_layout.addLayout(quality_layout)

            layout.addWidget(playlist_card)

            self.playlist_option.currentIndexChanged.connect(self.toggle_playlist_inputs)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "back")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("Start Download")
        ok_btn.setProperty("class", "success")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    def toggle_playlist_inputs(self, index):
        self.playlist_limit_spin.setEnabled(index == 1)
        self.playlist_limit_spin.setVisible(index == 1)
        self.playlist_items_input.setEnabled(index == 2)
        self.playlist_items_input.setVisible(index == 2)

    def get_options(self):
        options = {
            'merge_format': self.merge_combo.currentText().split()[0],
            'subtitles': self.subtitle_check.isChecked(),
            'subtitle_langs': [lang.strip() for lang in self.subtitle_input.text().split(',')] if self.subtitle_check.isChecked() else []
        }

        if self.media_type == "playlist":
            options['quality_selection'] = self.quality_combo.currentText()
            idx = self.playlist_option.currentIndex()
            options['playlist_mode'] = idx
            if idx == 1:
                options['playlist_end'] = self.playlist_limit_spin.value()
            elif idx == 2:
                options['playlist_items'] = self.playlist_items_input.text()

        return options

class MetadataDisplayWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setProperty("class", "card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(220)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(10)

        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

    def clear_display(self):
        """
        Recursively clears the content layout.
        Crucial for removing nested layouts (Rows) created in display_metadata.
        """
        if self.content_layout is not None:
            self._clear_layout_recursive(self.content_layout)

    def _clear_layout_recursive(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout_recursive(item.layout())
                item.layout().deleteLater()

    def display_metadata(self, data):
        self.clear_display()

        title_lbl = QLabel("Media Information")
        title_lbl.setStyleSheet(f"color: {THEME_ACCENT}; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        self.content_layout.addWidget(title_lbl)

        for key, value in data.items():
            if key.startswith('_') and key != "_type": continue
            if value is None: continue

            row = QHBoxLayout()

            key_clean = key.replace('_', ' ').title()
            key_label = QLabel(f"{key_clean}:")
            key_label.setStyleSheet(f"color: #f9e2af; font-weight: bold;")
            key_label.setFixedWidth(150)
            key_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

            val_str = str(value)

            value_label = QLabel(val_str)
            value_label.setWordWrap(True)
            value_label.setStyleSheet(f"color: {THEME_TEXT};")
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

            row.addWidget(key_label)
            row.addWidget(value_label, 1)

            self.content_layout.addLayout(row)

        self.content_layout.addStretch()

class DownloadPage(QWidget):

    @staticmethod
    def _format_bytes(byte_count):
        """Helper to format bytes into KB, MB, GB."""
        if byte_count is None:
            return "N/A"
        power = 1024
        n = 0
        power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while byte_count >= power and n < len(power_labels) - 1:
            byte_count /= power
            n += 1
        return f"{byte_count:.2f}{power_labels[n]}B"

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.current_view = "menu"
        self.workers = []
        self.fetch_worker = None
        self.fetched_info = None
        self.playlist_progress_widgets = {}
        self.download_params = {}
        self.init_ui()

    def _update_progress_text_contrast(self, bar, value):
        """
        Dynamically adjusts progress bar text color depending on fill.
        Explicitly sets the full stylesheet to ensure the change applies.
        """
        # Determine the target text color
        target_text_color = "black" if value >= 45 else "white"

        # Optimization: Don't re-set the stylesheet if the color is already correct
        current_style = bar.styleSheet()
        if f"color: {target_text_color}" in current_style:
            return

        # Define colors (matching the global variables in your file)
        # THEME_BORDER="#A6ADC8", THEME_ACCENT="#89b4fa", THEME_INPUT_BG="#313244"

        # Check if this is a Playlist Bar (height was set to 20 in previous code)
        # or Main Bar (standard height)
        if bar.maximumHeight() == 20:
            # --- PLAYLIST BAR STYLE ---
            new_style = f"""
                QProgressBar {{
                    border: 1px solid #A6ADC8;
                    border-radius: 6px;
                    background-color: #262637;
                    padding: 0px;
                    color: {target_text_color};
                    font-weight: bold;
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    background-color: #89b4fa;
                    border-radius: 6px;
                }}
            """
        else:
            # --- MAIN PROGRESS BAR STYLE ---
            new_style = f"""
                QProgressBar {{
                    border: 2px solid #A6ADC8;
                    border-radius: 10px;
                    background-color: #313244;
                    font-weight: bold;
                    color: {target_text_color};
                    padding: 2px;
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    background-color: #89b4fa;
                    border-radius: 10px;
                }}
            """

        bar.setStyleSheet(new_style)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(STYLESHEET)
        self.show_menu()

    def reset_state(self):
        """Matches CLI behavior: cleans up variables/state when procedure ends or is cancelled."""
        self.current_view = "menu"
        self.url_input = None
        self.playlist_url_input = None
        self.fetched_info = None
        self.fetched_formats = None
        self.download_params = {}
        self.playlist_progress_widgets = {}
        self.fetched_url = None

        for w in self.workers:
            if w.isRunning():
                w.terminate()
                w.wait()
        self.workers = []

        if self.fetch_worker and self.fetch_worker.isRunning():
            self.fetch_worker.terminate()
            self.fetch_worker.wait()
        self.fetch_worker = None

    def prepare_new_fetch(self):
        """Clears UI elements and internal state for a new fetch without leaving the page."""
        # Clear metadata
        if hasattr(self, 'metadata_widget'):
            self.metadata_widget.clear_display()

        # Hide configuration/confirmation
        if hasattr(self, 'configure_download_btn'):
            self.configure_download_btn.setVisible(False)
        if hasattr(self, 'confirmation_group'):
            self.confirmation_group.setVisible(False)

        # Hide progress bars
        if hasattr(self, 'progress_container'):
            self.progress_container.setVisible(False)
        if hasattr(self, 'playlist_progress_container'):
            self.playlist_progress_container.setVisible(False)
            # Clear playlist progress items
            while self.playlist_progress_layout.count():
                child = self.playlist_progress_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            self.playlist_progress_widgets.clear()

        # Clear logs
        if hasattr(self, 'status_text'):
            self.status_text.clear()

        # Clear previous internal data
        self.fetched_info = None
        self.fetched_formats = None
        self.download_params = {}

        # Stop any previous workers that might still be lingering
        for w in self.workers:
            if w.isRunning():
                w.terminate()
                w.wait()
        self.workers = []

        if self.fetch_worker and self.fetch_worker.isRunning():
            self.fetch_worker.terminate()
            self.fetch_worker.wait()
        self.fetch_worker = None

    def show_menu(self):
        self.reset_state()
        self.clear_layout()

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(30)

        title = QLabel("Download Manager")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title)

        subtitle = QLabel("Select a download mode to begin")
        subtitle.setStyleSheet(f"color: {THEME_BORDER}; font-size: 16px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(subtitle)

        btn_container = QFrame()
        btn_container.setFixedWidth(400)
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setSpacing(15)

        # --- Video Button ---
        video_btn = QPushButton()
        video_btn.setFixedHeight(80)
        video_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        video_btn.setProperty("class", "primary")
        video_btn.clicked.connect(self.show_video_download)

        video_btn_layout = QHBoxLayout(video_btn)
        video_btn_layout.setContentsMargins(20, 0, 20, 0)
        video_btn_layout.setSpacing(15)
        video_icon = QLabel("🎬")
        video_icon.setStyleSheet("font-size: 36px; background: transparent; color: #11111b;")
        video_text = QLabel("Single Video / Audio")
        video_text.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent; color: #11111b;")
        video_btn_layout.addWidget(video_icon)
        video_btn_layout.addWidget(video_text, 1, Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(video_btn)

        # --- Playlist Button ---
        playlist_btn = QPushButton()
        playlist_btn.setFixedHeight(80)
        playlist_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        playlist_btn.setProperty("class", "primary")
        playlist_btn.clicked.connect(self.show_playlist_download)

        playlist_btn_layout = QHBoxLayout(playlist_btn)
        playlist_btn_layout.setContentsMargins(20, 0, 20, 0)
        playlist_btn_layout.setSpacing(15)
        playlist_icon = QLabel("📑")
        playlist_icon.setStyleSheet("font-size: 36px; background: transparent; color: #11111b;")
        playlist_text = QLabel("Full Playlist")
        playlist_text.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent; color: #11111b;")
        playlist_btn_layout.addWidget(playlist_icon)
        playlist_btn_layout.addWidget(playlist_text, 1, Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(playlist_btn)

        # --- History Button ---
        history_btn = QPushButton()
        history_btn.setFixedHeight(80)
        history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        history_btn.setProperty("class", "primary")
        history_btn.clicked.connect(self.show_history)

        history_btn_layout = QHBoxLayout(history_btn)
        history_btn_layout.setContentsMargins(20, 0, 20, 0)
        history_btn_layout.setSpacing(15)
        history_icon = QLabel("📜")
        history_icon.setStyleSheet("font-size: 36px; background: transparent; color: #11111b;")
        history_text = QLabel("History")
        history_text.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent; color: #11111b;")
        history_btn_layout.addWidget(history_icon)
        history_btn_layout.addWidget(history_text, 1, Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(history_btn)

        center_layout.addWidget(btn_container)
        self.main_layout.addWidget(center_widget)

    def _setup_download_view(self, title_text, placeholder, callback):
        self.clear_layout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_container = QWidget()
        layout = QVBoxLayout(content_container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        header = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(100, 40)
        back_btn.setProperty("class", "back")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.show_menu)
        header.addWidget(back_btn)

        title = QLabel(title_text)
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QWidget())
        layout.addLayout(header)

        input_card = QFrame()
        input_card.setProperty("class", "card")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(20, 20, 20, 20)

        url_layout = QHBoxLayout()
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setMinimumHeight(45)
        url_layout.addWidget(input_field)

        fetch_btn = QPushButton("Fetch Info")
        fetch_btn.setFixedSize(120, 45)
        fetch_btn.setProperty("class", "primary")
        fetch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fetch_btn.clicked.connect(callback)
        input_field.returnPressed.connect(fetch_btn.click)
        url_layout.addWidget(fetch_btn)

        input_layout.addLayout(url_layout)
        layout.addWidget(input_card)

        self.metadata_widget = MetadataDisplayWidget()
        layout.addWidget(self.metadata_widget)

        self.configure_download_btn = QPushButton("Configure Download")
        self.configure_download_btn.setFixedHeight(45)
        self.configure_download_btn.setProperty("class", "success")
        self.configure_download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.configure_download_btn.setVisible(False)
        layout.addWidget(self.configure_download_btn)

        # Confirmation Group
        self.confirmation_group = QFrame()
        self.confirmation_group.setProperty("class", "card")
        confirmation_layout = QVBoxLayout(self.confirmation_group)
        confirmation_layout.setSpacing(15)
        conf_title = QLabel("Download Confirmation")
        conf_title.setStyleSheet(f"color: {THEME_ACCENT}; font-weight: bold; font-size: 16px;")
        confirmation_layout.addWidget(conf_title)

        self.ydl_options_display = QTextEdit()
        self.ydl_options_display.setReadOnly(True)
        self.ydl_options_display.setMinimumHeight(150)
        confirmation_layout.addWidget(self.ydl_options_display)

        conf_btns_layout = QHBoxLayout()

        # Cancel Button
        self.cancel_conf_btn = QPushButton("Cancel Download")
        self.cancel_conf_btn.setFixedSize(140, 35)
        self.cancel_conf_btn.setProperty("class", "cancel")
        self.cancel_conf_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_conf_btn.clicked.connect(self.cancel_process)

        # Confirm Button
        self.confirm_download_btn = QPushButton("Confirm Download")
        self.confirm_download_btn.setFixedHeight(45)
        self.confirm_download_btn.setProperty("class", "success")
        self.confirm_download_btn.setDefault(True)

        conf_btns_layout.addWidget(self.cancel_conf_btn)
        conf_btns_layout.addWidget(self.confirm_download_btn, 1)

        confirmation_layout.addLayout(conf_btns_layout)
        self.confirmation_group.setVisible(False)
        layout.addWidget(self.confirmation_group)

        # Progress Bar Layout
        self.progress_container = QFrame()
        self.progress_container.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_container) # Changed to QVBoxLayout
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(5)

        # Top row for labels (speed, size)
        labels_layout = QHBoxLayout()
        self.download_speed_label = QLabel("Speed: N/A")
        self.download_size_label = QLabel("0MB / 0MB")
        labels_layout.addStretch() # Push labels to the right
        labels_layout.addWidget(self.download_speed_label)
        labels_layout.addWidget(self.download_size_label)
        progress_layout.addLayout(labels_layout)

        # Progress bar below labels
        self.main_progress = QProgressBar()
        progress_layout.addWidget(self.main_progress)
        layout.addWidget(self.progress_container)

        self.playlist_progress_container = QWidget()
        self.playlist_progress_layout = QVBoxLayout(self.playlist_progress_container)
        self.playlist_progress_container.setVisible(False)
        layout.addWidget(self.playlist_progress_container)

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        # Fixed height so output box doesn't collapse when many playlist items appear
        self.status_text.setFixedHeight(120)
        self.status_text.setPlaceholderText("Process logs will appear here...")
        layout.addWidget(self.status_text)

        scroll_area.setWidget(content_container)
        self.main_layout.addWidget(scroll_area)
        return input_field

    def show_video_download(self):
        self.current_view = "video"
        self.url_input = self._setup_download_view(
            "Video Downloader",
            "Paste YouTube URL here (https://www.youtube.com/watch?v=...)",
            self.fetch_video_info
        )

    def show_playlist_download(self):
        self.current_view = "playlist"
        self.playlist_url_input = self._setup_download_view(
            "Playlist Downloader",
            "Paste Playlist URL here (https://www.youtube.com/playlist?list=...)",
            self.fetch_playlist_info
        )

    def show_history(self):
        """Show the history table-only page (reads Download.csv)."""
        self.current_view = "history"
        self.clear_layout()
        history = HistoryPage(self)
        self.main_layout.addWidget(history)

    def cancel_process(self):
        mode = self.current_view
        self.reset_state()
        if mode == "video":
            self.show_video_download()
        elif mode == "playlist":
            self.show_playlist_download()
        else:
            self.show_menu()

    def fetch_video_info(self):
        # Reset state safely before new fetch
        self.prepare_new_fetch()

        url = self.url_input.text().strip()
        if not url:
            self.status_text.append("⚠️ Please enter a valid URL")
            return

        self.status_text.append("⏳ Fetching video information... Please wait.")

        ydl_opts = {'skip_download': True, 'playlistend': 1, 'quiet': True}
        self.fetch_worker = FetchInfoWorker(url, ydl_opts)
        self.fetch_worker.finished.connect(self.on_video_info_fetched)
        self.fetch_worker.error.connect(self.on_fetch_error)
        self.fetch_worker.start()

    def on_video_info_fetched(self, info):
        if info.get('_type') == 'playlist' or info.get('playlist_count'):
            self.status_text.append("❌ This is a playlist. Please use the Playlist mode.")
            winsound.MessageBeep(winsound.MB_ICONHAND) # Sound for error
            return

        data = {
            "title": info.get("title"),
            "description": info.get("description"),
            "view_count": info.get("view_count"),
            "like_count": info.get("like_count"),
            "upload_date": info.get("upload_date"),
            "channel": info.get("channel"),
            "uploader": info.get("uploader"),
            'duration': info.get("duration"),
            'thumbnail': info.get("thumbnail"),
            "webpage_url_domain": info.get("webpage_url_domain"),
            "_type": info.get("_type")
        }
        self.metadata_widget.display_metadata(data)

        formats = []
        for f in info.get('formats', []):
            fs = f.get('filesize')
            fs_str = f"{round(fs / (1024*1024), 2)}MB" if fs else 'N/A'
            formats.append((
                f.get('format_id', 'N/A'),
                f.get('ext', 'N/A'),
                f.get('height', 'N/A'),
                f.get('format_note', 'N/A'),
                f.get('quality', 'N/A'),
                fs_str
            ))

        self.fetched_info = info
        self.fetched_formats = formats
        self.fetched_url = self.sender().url # Access url from worker safely
        self.configure_download_btn.setVisible(True)
        self.configure_download_btn.clicked.disconnect() if self.configure_download_btn.receivers(self.configure_download_btn.clicked) else None
        self.configure_download_btn.clicked.connect(self.show_video_download_options)
        self.status_text.append("✅ Video information fetched successfully.")

    def on_fetch_error(self, error_msg):
        self.status_text.append(f"❌ Error: {error_msg}")
        winsound.MessageBeep(winsound.MB_ICONHAND) # Sound for error

    def fetch_playlist_info(self):
        # Reset state safely before new fetch
        self.prepare_new_fetch()

        url = self.playlist_url_input.text().strip()
        if not url:
            self.status_text.append("⚠️ Please enter a valid URL")
            return

        self.status_text.append("⏳ Fetching playlist information...")

        ydl_opts = {'skip_download': True, 'playlistend': 1, 'quiet': True}
        self.fetch_worker = FetchInfoWorker(url, ydl_opts)
        self.fetch_worker.finished.connect(self.on_playlist_info_fetched)
        self.fetch_worker.error.connect(self.on_fetch_error)
        self.fetch_worker.start()

    def on_playlist_info_fetched(self, info):
        if info.get('_type') != 'playlist' and info.get('playlist_count') is None:
            self.status_text.append("❌ Invalid Object Type! URL don't belong to Playlist.")
            winsound.MessageBeep(winsound.MB_ICONHAND) # Sound for error
            return

        data = {
            "title": info.get("title"),
            "description": info.get("description"),
            "modified_date": info.get("modified_date"),
            "view_count": info.get("view_count"),
            "playlist_count": info.get("playlist_count"),
            "channel": info.get("channel"),
            'uploader': info.get("uploader"),
            'thumbnail': info.get("thumbnail"),
            "webpage_url_domain": info.get("webpage_url_domain"),
            "_type": info.get("_type")
        }
        self.metadata_widget.display_metadata(data)

        self.fetched_info = info
        self.fetched_url = self.sender().url # Access url from worker safely
        self.configure_download_btn.setVisible(True)
        self.configure_download_btn.clicked.disconnect() if self.configure_download_btn.receivers(self.configure_download_btn.clicked) else None
        self.configure_download_btn.clicked.connect(self.show_playlist_download_options)
        self.status_text.append("✅ Playlist information fetched successfully.")

    def show_video_download_options(self):
        format_dialog = FormatSelectionDialog(self.fetched_formats, self)
        if format_dialog.exec():
            fmt_str = format_dialog.get_selected_format()
            opt_dialog = DownloadOptionsDialog('video', self)
            if opt_dialog.exec():
                options = opt_dialog.get_options()
                opts = self._get_base_opts(options)
                # Ensure ignoreerrors is FALSE for single videos
                if 'ignoreerrors' in opts:
                    del opts['ignoreerrors']

                opts['format'] = fmt_str
                base = 'Media Files Manager/Downloads'
                opts['outtmpl'] = f"{base}/%(title)s.%(ext)s"

                self.download_params = {
                    'type': 'video', 'url': self.fetched_url, 'opts': opts,
                    'info': self.fetched_info, 'save_path': base
                }
                self.show_confirmation(opts)

    def show_playlist_download_options(self):
        opt_dialog = DownloadOptionsDialog('playlist', self)
        if opt_dialog.exec():
            options = opt_dialog.get_options()
            opts = self._get_base_opts(options)

            # Add ignoreerrors for playlists
            opts['ignoreerrors'] = True

            base = 'Media Files Manager/Downloads'
            opts['outtmpl'] = f'{base}/%(playlist_title)s/%(playlist_index)s-%(title)s.%(ext)s'

            mode = options.get('playlist_mode', 0)
            if mode == 1: opts['playlistend'] = options['playlist_end']
            elif mode == 2: opts['playlist_items'] = options['playlist_items']

            q_sel = options.get('quality_selection', '1080p')
            if 'Audio Only' in q_sel: opts['format'] = 'bestaudio[ext=m4a]/bestaudio'
            else: opts['format'] = f'bestvideo[height<={q_sel.replace("p", "")}]+bestaudio'

            self.download_params = {
                'type': 'playlist', 'url': self.fetched_url, 'opts': opts,
                'info': self.fetched_info, 'save_path': f"{base}/{self.fetched_info.get('title', 'Playlist')}"
            }
            self.show_confirmation(opts)

    def _get_base_opts(self, options):
        opts = {
            'ffmpeg_location': 'C:\\ffmpeg\\ffmpeg-7.1.1-essentials_build\\bin',
        }

        pp = []
        merge_fmt = options['merge_format']

        if merge_fmt == 'mp3':
            pp.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            })
            pp.append({'key': 'FFmpegMetadata'})

        elif merge_fmt == 'mp4':
            opts['merge_output_format'] = 'mp4'
            pp.append({'key': 'FFmpegMetadata'})
            if options['subtitles'] and options['subtitle_langs']:
                opts['writesubtitles'] = True
                opts['subtitleslangs'] = options['subtitle_langs']
                opts['subtitlesformat'] = 'vtt'
                pp.append({'key': 'FFmpegEmbedSubtitle'})

        elif merge_fmt == 'original':
             pp.append({'key': 'FFmpegMetadata'})
             if options['subtitles'] and options['subtitle_langs']:
                opts['writesubtitles'] = True
                opts['subtitleslangs'] = options['subtitle_langs']
                opts['subtitlesformat'] = 'vtt'
                pp.append({'key': 'FFmpegEmbedSubtitle'})

        opts['postprocessors'] = pp
        return opts

    def show_confirmation(self, opts):
        import json
        self.configure_download_btn.setVisible(False)
        self.confirmation_group.setVisible(True)

        opts_text = json.dumps(opts, indent=4)
        self.ydl_options_display.setText(opts_text)

        try: self.confirm_download_btn.clicked.disconnect()
        except TypeError: pass
        self.confirm_download_btn.clicked.connect(self.execute_download)

    def execute_download(self):
        self.confirmation_group.setVisible(False)
        self.start_download(self.download_params)

    def start_download(self, params):
        url = params['url']
        opts = params['opts']
        save_path = params['save_path']

        if params.get('type') == 'playlist':
            self.progress_container.setVisible(False)
            self.playlist_progress_container.setVisible(True)
            while self.playlist_progress_layout.count():
                self.playlist_progress_layout.takeAt(0).widget().deleteLater()
            self.playlist_progress_widgets.clear()
        else:
            self.progress_container.setVisible(True)
            self.main_progress.setValue(0)
            self.main_progress.setFormat("0%")
            self.download_speed_label.setText("Speed: N/A")
            self.download_size_label.setText("0MB / 0MB")

        self.status_text.append(f"\n🚀 Starting download: {params['info'].get('title')}")

        # Wrap thread creation in try-except for error handling
        try:
            worker = DownloadWorker(url, opts)
            worker.progress.connect(self.update_progress)
            worker.log_message.connect(self.append_log_message)
            worker.finished.connect(lambda r: self.on_finished(r, url, save_path))
            worker.start()
            self.workers.append(worker)
        except Exception as e:
            self.status_text.append(f"❌ Failed to start background process: {str(e)}")
            winsound.MessageBeep(winsound.MB_ICONHAND)

    def update_progress(self, d):
        try:
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes')
            speed = d.get('speed')
            if not (total_bytes and downloaded_bytes and speed is not None):
                return

            percent = int((downloaded_bytes / total_bytes) * 100)
            speed_str = d.get('_speed_str', 'N/A')

            downloaded_str = self._format_bytes(downloaded_bytes)
            total_str = self._format_bytes(total_bytes)

            if self.download_params.get('type') == 'playlist':
                video_info = d.get('info_dict', {})
                video_id = video_info.get('id') or video_info.get('title')

                if video_id not in self.playlist_progress_widgets:
                    title = f"{video_info.get('playlist_index', '?')}. {video_info.get('title', 'Unknown Video')}"

                    item_widget = QFrame()
                    # Horizontal row: title | progress bar | speed/size
                    item_layout = QHBoxLayout(item_widget)
                    item_layout.setContentsMargins(0, 5, 0, 5)
                    item_layout.setSpacing(10)

                    # Title label (left) - will elide long text and show full text on hover
                    title_label = QLabel(title)
                    title_label.setWordWrap(False)
                    title_label.setStyleSheet("color: white; font-size: 13px;")
                    title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                    title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

                    title_label.setToolTip(title)  # always show full title on hover

                    # truncate title based on available playlist width
                    fm = QFontMetrics(title_label.font())
                    max_title_w = int(self.playlist_progress_container.width() * 0.45) if self.playlist_progress_container.width() else 350
                    elided_text = fm.elidedText(title, Qt.TextElideMode.ElideRight, max_title_w)
                    title_label.setText(elided_text)

                    # Slim progress bar (center) with visible percentage and improved contrast
                    progress_bar = QProgressBar()
                    # Increased height to 20px to ensure text fits comfortably
                    progress_bar.setFixedHeight(20)
                    progress_bar.setTextVisible(True)
                    progress_bar.setFormat("%p%")

                    progress_bar.setStyleSheet(f"""
                        QProgressBar {{
                            border: 1px solid {THEME_BORDER};
                            border-radius: 6px;
                            background-color: #262637;     /* darker track */
                            padding: 0px;
                            color: white;                  /* default readable */
                            font-weight: bold;
                            text-align: center;            /* ensure text is centered */
                        }}
                        QProgressBar::chunk {{
                            background-color: {THEME_ACCENT};
                            border-radius: 6px;
                        }}
                    """)

                    progress_bar.setFixedWidth(260)

                    # Right-side small labels (speed, size)
                    right_col = QVBoxLayout()
                    right_col.setContentsMargins(0, 0, 0, 0)
                    right_col.setSpacing(2)
                    speed_label = QLabel(f"Speed: {speed_str}")
                    size_label = QLabel(f"{downloaded_str} / {total_str}")
                    speed_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    right_col.addWidget(speed_label)
                    right_col.addWidget(size_label)

                    item_layout.addWidget(title_label)
                    item_layout.addWidget(progress_bar)
                    item_layout.addLayout(right_col)

                    self.playlist_progress_layout.addWidget(item_widget)
                    # store title_label too so we can update elision when container resizes if needed
                    self.playlist_progress_widgets[video_id] = (progress_bar, speed_label, size_label, title_label)

                # stored tuple: (progress_bar, speed_label, size_label, title_label)
                bar = self.playlist_progress_widgets[video_id][0]
                bar.setValue(percent)
                self._update_progress_text_contrast(bar, percent)
                self.playlist_progress_widgets[video_id][1].setText(f"Speed: {speed_str}")
                self.playlist_progress_widgets[video_id][2].setText(f"{downloaded_str} / {total_str}")
            else:
                self.main_progress.setValue(percent)
                self.main_progress.setFormat(f"{percent}%")
                self._update_progress_text_contrast(self.main_progress, percent)
                self.download_speed_label.setText(f"Speed: {speed_str}")
                self.download_size_label.setText(f"{downloaded_str} / {total_str}")
        except (ValueError, TypeError, ZeroDivisionError, KeyError):
            pass

    def append_log_message(self, msg):
        self.status_text.append(msg)

    def on_finished(self, result, url, save_path):
        # Remove the worker from the list
        self.workers = [w for w in self.workers if w.isRunning()]

        now = ctime()
        is_success = result.get('State')
        abs_path = os.path.abspath(save_path) # Always get absolute path

        # Determine Process Type string
        proc_type_raw = self.download_params.get('type', 'video')
        if proc_type_raw == 'video':
            proc_type_str = 'Video/Audio Download'
            success_msg = "Video/Audio Downloaded Successfully"
        else:
            proc_type_str = 'Playlist Download'
            success_msg = "Playlist Downloaded Successfully"

        if is_success:
            # Prefix with checkmark, use specific success string, show ABSOLUTE path
            self.status_text.append(f"\n✅ {success_msg}")
            self.status_text.append(f"📁 Saved to: {abs_path}")
            self.main_progress.setValue(100)
            self.main_progress.setFormat("Done")
            # REMOVED SUCCESS SOUND (winsound.MessageBeep(winsound.MB_OK)) as requested
        else:
            # Error handling: show exact error, keep error sound
            msg = f"❌ Download failed: {result.get('Error')}"
            self.main_progress.setFormat("Error")
            self.status_text.append(f"\n{msg}")
            winsound.MessageBeep(winsound.MB_ICONHAND) # Error Sound kept

        # Determine Log Message
        log_msg = success_msg if is_success else result.get('Error')

        write_log({
            'URL': url,
            'Process': proc_type_str,
            'State': 1 if is_success else 0,
            'Message': log_msg,
            'Save Location': abs_path if is_success else None, # Use absolute path in logs
            'Datetime': now
        }, 'Download')

    def is_processing(self):
        """Check if there are any active background workers."""
        self.workers = [w for w in self.workers if w.isRunning()]
        is_fetching = self.fetch_worker is not None and self.fetch_worker.isRunning()
        return len(self.workers) > 0 or is_fetching

    def clear_layout(self):
        if self.layout():
            while self.layout().count():
                child = self.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()