from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                             QLineEdit, QTextEdit, QFileDialog, QComboBox, QFrame, QScrollArea, QSizePolicy, QStackedWidget)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QCursor
from cli.pdf import PDF
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

class PDFToolCard(QFrame):
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

class PDFPage(QWidget):
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
        self.stack.addWidget(self.menu_widget) # 0

        # Merge Page
        self.merge_widget, self.merge_paths, self.merge_save, self.merge_result = self._create_merge_page()
        self.stack.addWidget(self.merge_widget) # 1

        # Split Page
        self.split_widget, self.split_path, self.split_start, self.split_end, self.split_folder, self.split_result = self._create_split_page()
        self.stack.addWidget(self.split_widget) # 2

        # Extract Page
        self.extract_widget, self.extract_path, self.extract_result = self._create_extract_page()
        self.stack.addWidget(self.extract_widget) # 3

        # Delete Page
        self.delete_widget, self.delete_path, self.delete_pages, self.delete_result = self._create_delete_page()
        self.stack.addWidget(self.delete_widget) # 4
        
    def go_to_menu(self):
        self.stack.setCurrentIndex(0)

    def show_merge(self):
        self.stack.setCurrentIndex(1)

    def show_split(self):
        self.stack.setCurrentIndex(2)

    def show_extract_images(self):
        self.stack.setCurrentIndex(3)

    def show_delete_pages(self):
        self.stack.setCurrentIndex(4)

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
        title = QLabel("PDF Tools")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Merge, split, and convert your PDF documents")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(title)
        header.addWidget(subtitle)
        content_layout.addLayout(header)
        
        grid = QGridLayout()
        grid.setSpacing(20)
        
        tools = [
            ("Merge PDFs", "Combine multiple PDF files into one document.", "📑", self.show_merge),
            ("Split PDF", "Extract specific pages from a PDF file.", "✂️", self.show_split),
            ("Extract Images", "Save all images embedded inside a PDF.", "🖼️", self.show_extract_images),
            ("Delete Pages", "Remove unwanted pages from a PDF.", "🗑️", self.show_delete_pages),
        ]
        
        row, col = 0, 0
        for title, desc, icon, func in tools:
            card = PDFToolCard(title, desc, icon, func)
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

    def _create_merge_page(self):
        widget, layout, result_text = self._create_base_subpage("Merge PDF Files")
        
        layout.addWidget(QLabel("PDF Files:"))
        file_row = QHBoxLayout()
        paths_input = QLineEdit()
        paths_input.setPlaceholderText("Select multiple PDF files...")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self.browse_merge_files(paths_input))
        file_row.addWidget(paths_input)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)
        
        layout.addWidget(QLabel("Save As:"))
        save_row = QHBoxLayout()
        save_input = QLineEdit()
        save_input.setPlaceholderText("Output filename (e.g., merged.pdf)")
        save_btn = QPushButton("Browse")
        save_btn.clicked.connect(lambda: self.browse_save_location(save_input))
        save_row.addWidget(save_input)
        save_row.addWidget(save_btn)
        layout.addLayout(save_row)
        
        process_btn = QPushButton("Merge PDFs")
        process_btn.setProperty("class", "success")
        process_btn.clicked.connect(self.process_merge)
        layout.addWidget(process_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        return widget, paths_input, save_input, result_text

    def _create_split_page(self):
        widget, layout, result_text = self._create_base_subpage("Split PDF File")
        
        layout.addWidget(QLabel("PDF File:"))
        file_row = QHBoxLayout()
        pdf_path_input = QLineEdit()
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self.browse_file(pdf_path_input, "PDF"))
        file_row.addWidget(pdf_path_input)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)
        
        range_row = QHBoxLayout()
        start_layout = QVBoxLayout()
        start_layout.addWidget(QLabel("Start Page:"))
        start_page_input = QLineEdit()
        start_page_input.setPlaceholderText("1")
        start_layout.addWidget(start_page_input)
        
        end_layout = QVBoxLayout()
        end_layout.addWidget(QLabel("End Page:"))
        end_page_input = QLineEdit()
        end_page_input.setPlaceholderText("5")
        end_layout.addWidget(end_page_input)
        
        range_row.addLayout(start_layout)
        range_row.addLayout(end_layout)
        layout.addLayout(range_row)
        
        layout.addWidget(QLabel("Output Folder:"))
        folder_row = QHBoxLayout()
        save_folder_input = QLineEdit()
        browse_folder_btn = QPushButton("Browse")
        browse_folder_btn.clicked.connect(lambda: self.browse_folder(save_folder_input))
        folder_row.addWidget(save_folder_input)
        folder_row.addWidget(browse_folder_btn)
        layout.addLayout(folder_row)
        
        process_btn = QPushButton("Split PDF")
        process_btn.setProperty("class", "success")
        process_btn.clicked.connect(self.process_split)
        layout.addWidget(process_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        return widget, pdf_path_input, start_page_input, end_page_input, save_folder_input, result_text

    def _create_extract_page(self):
        widget, layout, result_text = self._create_base_subpage("Extract Images")
        
        layout.addWidget(QLabel("PDF File:"))
        file_row = QHBoxLayout()
        pdf_path_input = QLineEdit()
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self.browse_file(pdf_path_input, "PDF"))
        file_row.addWidget(pdf_path_input)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)
        
        process_btn = QPushButton("Extract Images")
        process_btn.setProperty("class", "success")
        process_btn.clicked.connect(self.process_extract)
        layout.addWidget(process_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        return widget, pdf_path_input, result_text

    def _create_delete_page(self):
        widget, layout, result_text = self._create_base_subpage("Delete Pages")
        
        layout.addWidget(QLabel("PDF File:"))
        file_row = QHBoxLayout()
        pdf_path_input = QLineEdit()
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self.browse_file(pdf_path_input, "PDF"))
        file_row.addWidget(pdf_path_input)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)
        
        layout.addWidget(QLabel("Pages to delete:"))
        pages_input = QLineEdit()
        pages_input.setPlaceholderText("e.g., 2 or 1-8 or 1,8,5,7")
        layout.addWidget(pages_input)
        
        process_btn = QPushButton("Delete Pages")
        process_btn.setProperty("class", "success")
        process_btn.clicked.connect(self.process_delete)
        layout.addWidget(process_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        return widget, pdf_path_input, pages_input, result_text

    # --- Helper Functions ---
    def browse_merge_files(self, input_widget):
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF Files", "", "PDF Files (*.pdf)")
        if files:
            input_widget.setText(','.join(files))
            
    def browse_save_location(self, input_widget):
        file, _ = QFileDialog.getSaveFileName(self, "Save Location", "", "PDF Files (*.pdf)")
        if file:
            input_widget.setText(file)
            
    def browse_file(self, input_widget, file_type="PDF"):
        file, _ = QFileDialog.getOpenFileName(self, f"Select {file_type} File", "", f"{file_type} Files (*.{file_type.lower()})")
        if file:
            input_widget.setText(file)
            
    def browse_folder(self, input_widget):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            input_widget.setText(folder)

    # --- Process Logic ---
    def process_merge(self):
        paths = self.merge_paths.text().strip()
        save = self.merge_save.text().strip()
        
        if not paths or not save:
            self.main_window.show_error("Please select files and output location")
            return
            
        paths_list = [p.strip() for p in paths.split(',')]
        self.merge_result.append(f"⏳ Merging {len(paths_list)} files...")
        
        try:
            result = PDF(" ").merge_pdf(paths_list, save)
            write_log(result, 'PDF')
            if result.get('State'):
                self.merge_result.append(f"✅ {result.get('Message')}\nSaved to: {result.get('Save Location')}")
            else:
                self.merge_result.append(f"❌ Error: {result.get('Error')}")
        except Exception as e:
            self.merge_result.append(f"❌ Critical Error: {str(e)}")

    def process_split(self):
        pdf_path = self.split_path.text().strip()
        start = self.split_start.text().strip()
        end = self.split_end.text().strip()
        save_folder = self.split_folder.text().strip()
        
        if not all([pdf_path, start, end, save_folder]):
            self.main_window.show_error("Please fill in all fields")
            return
        
        self.split_result.append("⏳ Splitting PDF...")
        pdf = PDF(pdf_path)
        result = pdf.split_pdf(start, end, save_folder)
        write_log(result, 'PDF')
        
        if result.get('State'):
            self.split_result.append(f"✅ {result.get('Message')}\nSaved to: {result.get('Save Location')}")
        else:
            self.split_result.append(f"❌ Error: {result.get('Error')}")

    def process_extract(self):
        pdf_path = self.extract_path.text().strip()
        if not pdf_path:
            self.main_window.show_error("Please select a PDF file")
            return
        
        self.extract_result.append("⏳ Extracting images (this may take a moment)...")
        pdf = PDF(pdf_path)
        result = pdf.pdf_extract_images()
        write_log(result, 'PDF')
        
        if result.get('State'):
            self.extract_result.append(f"✅ {result.get('Message')}\nSaved to: {result.get('Save Location')}")
        else:
            self.extract_result.append(f"❌ Error: {result.get('Error')}")

    def process_delete(self):
        pdf_path = self.delete_path.text().strip()
        pages = self.delete_pages.text().strip()
        if not all([pdf_path, pages]):
            self.main_window.show_error("Please fill in all fields")
            return
        
        self.delete_result.append("⏳ Deleting pages...")
        pdf = PDF(pdf_path)
        result = pdf.pdf_pages_delete(pages)
        write_log(result, 'PDF')
        
        if result.get('State'):
            self.delete_result.append(f"✅ {result.get('Message')}\nSaved to: {result.get('Save Location')}")
        else:
            self.delete_result.append(f"❌ Error: {result.get('Error')}")

    def reset(self):
        pass
