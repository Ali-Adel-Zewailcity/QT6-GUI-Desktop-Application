from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QStackedWidget, QFrame, 
                             QMessageBox, QToolButton, QButtonGroup)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor, QCloseEvent
import os
try:
    import winsound
except ImportError:
    winsound = None
from cli.logs import initialize_env

# Pages
from gui.pages.home_page import HomePage
from gui.pages.download_page import DownloadPage
from gui.pages.pdf_page import PDFPage
from gui.pages.video_page import VideoPage
from gui.pages.image_page import ImagePage
from gui.pages.audio_page import AudioPage
from gui.pages.rename_page import RenamePage

# --- THEME CONFIGURATION (Matching DownloadPage) ---
THEME_BG = "#1e1e2e"       
THEME_SIDEBAR_BG = "#11111b" 
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

MAIN_STYLESHEET = f"""
    QMainWindow {{
        background-color: {THEME_BG};
    }}
    QWidget {{
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
        color: {THEME_TEXT};
    }}
    /* Sidebar Styling */
    QFrame#sidebar {{
        background-color: {THEME_SIDEBAR_BG};
        border-right: 1px solid {THEME_BORDER};
    }}
    QToolButton {{
        background-color: transparent;
        color: {THEME_SUBTEXT};
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-weight: bold;
        text-align: left;
    }}
    QToolButton:hover {{
        background-color: {THEME_HOVER};
        color: {THEME_TEXT};
    }}
    QToolButton:checked {{
        background-color: {THEME_INPUT_BG};
        color: {THEME_ACCENT};
        border-left: 3px solid {THEME_ACCENT};
    }}
    /* Scrollbar Styling */
    QScrollBar:vertical {{
        border: none;
        background: {THEME_BG};
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {THEME_BORDER};
        min-height: 20px;
        border-radius: 4px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    /* Message Box */
    QMessageBox {{
        background-color: {THEME_CARD_BG};
        color: {THEME_TEXT};
    }}
    QPushButton {{
        padding: 8px 16px;
        border-radius: 6px;
        background-color: {THEME_INPUT_BG};
        color: {THEME_TEXT};
        border: 1px solid {THEME_BORDER};
    }}
    QPushButton:hover {{ background-color: {THEME_BORDER}; }}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Files Manager")
        self.setWindowIcon(QIcon("assets/Logo 64x64.png"))
        # Ensure the window size fits the available screen and center after showing
        desired_w, desired_h = 1280, 720
        try:
            from PyQt6.QtGui import QGuiApplication
            screen = self.screen() or QGuiApplication.primaryScreen()
            if screen is not None:
                avail = screen.availableGeometry()
                # Set size to be 90% of available screen, but no more than desired size
                w = min(desired_w, int(avail.width() * 0.9))
                h = min(desired_h, int(avail.height() * 0.9))
            else:
                w, h = desired_w, desired_h
        except Exception:
            w, h = desired_w, desired_h

        self.resize(w, h)
        
        # Set the initial window state to maximized
        self.setWindowState(Qt.WindowState.WindowMaximized)
        
        # Apply Global Stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)
        
        # Initialize environment
        initialize_env()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout is Horizontal: Sidebar | Content
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create Stacked Widget first (needed for sidebar connections)
        self.stacked_widget = QStackedWidget()
        
        # Create sidebar
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Add stacked widget to layout
        main_layout.addWidget(self.stacked_widget)
        
        # Initialize Pages
        self.init_pages()
        
        # Show home page by default
        self.show_home()
        
    def init_pages(self):
        self.home_page = HomePage(self)
        self.download_page = DownloadPage(self)
        self.pdf_page = PDFPage(self)
        self.video_page = VideoPage(self)
        self.image_page = ImagePage(self)
        self.audio_page = AudioPage(self)
        self.rename_page = RenamePage(self)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.download_page)
        self.stacked_widget.addWidget(self.pdf_page)
        self.stacked_widget.addWidget(self.video_page)
        self.stacked_widget.addWidget(self.image_page)
        self.stacked_widget.addWidget(self.audio_page)
        self.stacked_widget.addWidget(self.rename_page)

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(90) # Compact sidebar
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(15)

        # --- Button Group for Exclusive Selection ---
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        # --- Navigation Items ---
        # Format: (icon_name, tooltip, callback_function)
        buttons_data = [
            ("logo", "Home", self.show_home),
            ("download", "Download", self.show_download),
            ("video", "Video Tools", self.show_video),
            ("audio", "Audio Tools", self.show_audio),
            ("image", "Image Tools", self.show_image),
            ("pdf", "PDF Tools", self.show_pdf),
            ("rename", "Rename Files", self.show_rename),
        ]

        for img_name, tooltip, callback in buttons_data:
            btn = self._create_nav_button(img_name, tooltip)
            btn.clicked.connect(callback)
            
            # Logo is special (top)
            if img_name == "logo":
                btn.setIconSize(QSize(48, 48))
                btn.setFixedHeight(60)
            
            layout.addWidget(btn)
            self.nav_group.addButton(btn)

        # Spacer to push Quit button to bottom
        layout.addStretch()

        # Quit Button
        quit_btn = self._create_nav_button("quit", "Quit Application")
        quit_btn.setStyleSheet(f"""
            QToolButton:hover {{ background-color: {THEME_ERROR}; color: #1e1e2e; }}
        """)
        quit_btn.clicked.connect(self.close)
        layout.addWidget(quit_btn)

        return sidebar

    def _create_nav_button(self, name, tooltip):
        """Helper to create styled sidebar buttons"""
        btn = QToolButton()
        btn.setToolTip(tooltip)
        btn.setCheckable(True) # Allows staying active
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(70, 60)
        
        icon = self.load_icon(name)
        if icon:
            btn.setIcon(icon)
            btn.setIconSize(QSize(32, 32))
        else:
            # Fallback text icon
            btn.setText(name[:2].upper()) 
            
        return btn

    def load_icon(self, name: str, size: tuple = (64, 64)) -> QIcon | None:
        """Enhanced icon loader with error handling"""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets'))
        
        # Map simple names to potential filenames
        alias_map = {
            'logo': ['logo', 'Logo 1024x1024', 'app_icon'],
            'rename': ['rename', 'edit', 'rename files'],
            'image': ['image', 'picture', 'photo'],
            'audio': ['audio', 'music', 'sound'],
            'download': ['download', 'cloud'],
            'pdf': ['pdf', 'document'],
            'video': ['video', 'movie', 'film'],
            'quit': ['quit', 'exit', 'close']
        }

        names = alias_map.get(name, [name])
        extensions = [".png", ".jpg", ".svg", ".ico"]
        
        for n in names:
            for ext in extensions:
                p = os.path.join(base_dir, n + ext)
                if os.path.exists(p):
                    orig = QPixmap(p)
                    # Create a square container for center alignment
                    side = max(size[0], size[1])
                    canvas = QPixmap(side, side)
                    canvas.fill(Qt.GlobalColor.transparent)
                    
                    # Scale image to fit
                    scaled = orig.scaled(QSize(side, side), 
                                       Qt.AspectRatioMode.KeepAspectRatio, 
                                       Qt.TransformationMode.SmoothTransformation)
                    
                    # Center draw
                    painter = QPainter(canvas)
                    x = (side - scaled.width()) // 2
                    y = (side - scaled.height()) // 2
                    painter.drawPixmap(x, y, scaled)
                    painter.end()
                    
                    # If it's a checkable button, we can create a "Selected" state icon tint here
                    # but CSS styling usually handles the background enough.
                    return QIcon(canvas)
        return None
    
    def _set_active_tab(self, index):
        """Helper to set the active page and highlight the correct button"""
        self.stacked_widget.setCurrentIndex(index)
        
        # Highlight the corresponding button in the sidebar
        # Note: The order of buttons in nav_group matches the order added
        # 0: Logo(Home), 1: Download, 2: Video, 3: Audio, 4: Image, 5: PDF, 6: Rename
        
        # Mapping Page Index -> Button Group ID
        # Stacked Widget Order: Home(0), Download(1), PDF(2), Video(3), Image(4), Audio(5), Rename(6)
        # Button Group Order:   Home(0), Download(1), Video(2), Audio(3), Image(4), PDF(5), Rename(6)
        
        # We need to find the button in nav_group that corresponds to the page
        # Ideally, buttons should be stored in a dict, but simple mapping works for now:
        
        btn_list = self.nav_group.buttons()
        # Map stacked_widget index to button list index
        mapping = {
            0: 0, # Home -> Home
            1: 1, # Download -> Download
            2: 5, # PDF -> PDF btn (index 5 in creation loop)
            3: 2, # Video -> Video btn
            4: 4, # Image -> Image btn
            5: 3, # Audio -> Audio btn
            6: 6  # Rename -> Rename
        }
        
        if index in mapping and mapping[index] < len(btn_list):
            btn_list[mapping[index]].setChecked(True)

    def show_home(self):
        self._set_active_tab(0)
        
    def show_download(self):
        self.download_page.go_to_menu()
        self._set_active_tab(1)
        
    def show_pdf(self):
        self._set_active_tab(2)
        
    def show_video(self):
        self.video_page.go_to_menu()
        self._set_active_tab(3)
        
    def show_image(self):
        self._set_active_tab(4)
        
    def show_audio(self):
        self._set_active_tab(5)
        
    def show_rename(self):
        self._set_active_tab(6)
    
    def show_error(self, message):
        """Show styled error in status bar and play error sound"""
        try:
            winsound.MessageBeep(winsound.MB_ICONHAND)
        except:
            pass
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText(message)
        msg_box.setWindowTitle("Error")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Apply custom style to message box
        msg_box.setStyleSheet(f"""
            QMessageBox {{ background-color: {THEME_CARD_BG}; }}
            QLabel {{ color: {THEME_TEXT}; }}
            QPushButton {{ 
                background-color: {THEME_ERROR}; 
                color: #1e1e2e;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: #ff9aa2; }}
        """)
        
        QTimer.singleShot(5000, msg_box.close)
        msg_box.show()

    def center_on_screen(self):
        """Center the main window on the available screen geometry."""
        try:
            # Prefer the window's screen (works with multiple monitors)
            screen = self.screen()
            if screen is None:
                from PyQt6.QtGui import QGuiApplication
                screen = QGuiApplication.primaryScreen()

            if screen is None:
                return

            available = screen.availableGeometry()
            w = self.width()
            h = self.height()
            x = available.x() + (available.width() - w) // 2
            y = available.y() + (available.height() - h) // 2
            self.move(x, y)
        except Exception:
            # Best-effort centering — do not crash the app on any error
            pass

    def has_active_processes(self):
        """Check all pages for active background processes."""
        if self.download_page.is_processing():
            return True
        # Add checks for other pages here if they implement background processing
        return False

    def closeEvent(self, event: QCloseEvent):
        if self.has_active_processes():
            reply = QMessageBox.warning(
                self,
                "Active Processes",
                "There are active processes (downloads, etc.) running.\nAre you sure you want to quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
