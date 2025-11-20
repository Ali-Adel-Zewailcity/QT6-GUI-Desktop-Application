from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QMenu, QApplication, QSizePolicy
from PyQt6.QtWidgets import QHeaderView
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QAction
import webbrowser
import csv
import os
from datetime import datetime


class HistoryPage(QWidget):
    """A simple page that displays the Download log file as a table.
    The UI consists only of a table (no extra controls) and will try to
    read `Media Files Manager/Logs/Download.csv` relative to the app cwd.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['URL', 'Type', 'Message', 'Save Location', 'Date', 'Time'])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Select items (cells) rather than entire rows
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        # Allow interactive column resizing with the mouse
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # When a section is resized, adjust the neighbouring column to keep total width constant
        header.sectionResized.connect(self._on_section_resized)
        self.table.setMouseTracking(True)
        # Prevent horizontal scrolling so columns stay within table width
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Enable custom context menu for right-click copy
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)
        # Double click URL to open in default browser
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        # Single click selection behavior (exposed for potential hooks)
        self.table.itemClicked.connect(self._on_item_clicked)

        # Make table expand to available width but not grow unlimited horizontally
        # Use a proper QSizePolicy instance to make the table expand within its container
        self.table.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))

        self.layout.addWidget(self.table)

        self.csv_path = os.path.join('Media Files Manager', 'Logs', 'Download.csv')
        self.load_csv()

    def _parse_datetime(self, text):
        """Try to parse common datetime formats; return (date_str, time_str)."""
        if not text:
            return ('', '')
        # Try typical ctime format: 'Thu Nov 20 12:34:56 2025'
        for fmt in ("%a %b %d %H:%M:%S %Y", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
            try:
                dt = datetime.strptime(text, fmt)
                return (dt.date().isoformat(), dt.time().isoformat())
            except Exception:
                continue
        # Fallback: try to split by space and pick elements
        parts = text.split()
        if len(parts) >= 4:
            # parts like ['Thu','Nov','20','12:34:56','2025']
            date = ' '.join(parts[0:3])
            time = parts[3]
            return (date, time)
        return (text, '')

    def load_csv(self):
        self.table.setRowCount(0)
        if not os.path.exists(self.csv_path):
            return

        try:
            with open(self.csv_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception:
            return

        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            url = row.get('URL', '')
            proc = row.get('Process', '')
            message = row.get('Message', '')
            error = row.get('Error', '')
            save_loc = row.get('Save Location', '')
            datetime_raw = row.get('Datetime', '')

            # Determine message and style
            if message and message.strip():
                display_msg = message
                bg = QColor(166, 227, 161, 80)  # light green with transparency
            else:
                display_msg = error or ''
                bg = QColor(243, 139, 168, 80)  # light red/pink transparent

            date_str, time_str = self._parse_datetime(datetime_raw)

            items = [
                QTableWidgetItem(url),
                QTableWidgetItem(proc),
                QTableWidgetItem(display_msg),
                QTableWidgetItem(save_loc),
                QTableWidgetItem(date_str),
                QTableWidgetItem(time_str),
            ]

            for c, it in enumerate(items):
                it.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                # message column -> colored background
                if c == 2:
                    it.setBackground(bg)
                # set tooltip so full text appears on hover
                text_for_tooltip = it.text()
                if text_for_tooltip:
                    it.setToolTip(text_for_tooltip)
                self.table.setItem(r, c, it)

    def showEvent(self, event):
        """Set initial column widths after the widget is shown so we can read the correct available width."""
        super().showEvent(event)
        total = max(100, self.table.viewport().width())
        # Date and Time each take 1/8 of the table width
        date_w = total // 10
        time_w = total // 10
        remaining = total - date_w - time_w
        # Distribute remaining equally among other columns (4 columns)
        if remaining > 0:
            per = remaining // 4
        else:
            per = 100

        # Column order: URL(0), Type(1), Message(2), Save Location(3), Date(4), Time(5)
        widths = [per, per, per, per, date_w, time_w]
        header = self.table.horizontalHeader()
        header.blockSignals(True)
        try:
            for i, w in enumerate(widths):
                self.table.setColumnWidth(i, max(60, w))
        finally:
            header.blockSignals(False)

    def _on_section_resized(self, logicalIndex: int, oldSize: int, newSize: int):
        """When a header section is resized by the user, take the delta from the adjacent column so the table width stays constant."""
        delta = newSize - oldSize
        if delta == 0:
            return

        col_count = self.table.columnCount()
        # Prefer to take/give from the right neighbor, otherwise left
        right = logicalIndex + 1 if logicalIndex + 1 < col_count else None
        left = logicalIndex - 1 if logicalIndex - 1 >= 0 else None

        adj = None
        if right is not None:
            adj = right
        elif left is not None:
            adj = left
        else:
            return

        adj_width = self.table.columnWidth(adj)
        new_adj_width = adj_width - delta
        min_w = 60
        # If new_adj_width would be too small, cap and compensate
        if new_adj_width < min_w:
            # limit how much we can change
            allowed_delta = adj_width - min_w
            if allowed_delta == 0:
                return
            # adjust the target column to maximum allowed change
            new_adj_width = min_w
            newSize = oldSize + allowed_delta
            # apply the adjusted new size to the original column
            header = self.table.horizontalHeader()
            header.blockSignals(True)
            try:
                self.table.setColumnWidth(logicalIndex, newSize)
                self.table.setColumnWidth(adj, new_adj_width)
            finally:
                header.blockSignals(False)
            return

        header = self.table.horizontalHeader()
        header.blockSignals(True)
        try:
            self.table.setColumnWidth(adj, new_adj_width)
        finally:
            header.blockSignals(False)

    def _on_item_clicked(self, item: QTableWidgetItem):
        # Keep behavior simple: ensure the clicked cell is selected and focused
        self.table.setCurrentItem(item)

    def _on_item_double_clicked(self, item: QTableWidgetItem):
        # If double-clicked on the URL column, open in default browser
        if item is None:
            return
        col = item.column()
        if col == 0:
            url = item.text().strip()
            if url:
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
        # If double-clicked on Save Location, open folder in Windows Explorer
        elif col == 3:
            path = item.text().strip()
            if not path:
                return
            try:
                p = os.path.expanduser(path)
                p = os.path.abspath(p)
                # If the path is a directory, open it; if it's a file, open its containing folder
                if os.path.isdir(p):
                    os.startfile(p)
                elif os.path.exists(p):
                    folder = os.path.dirname(p)
                    if folder:
                        os.startfile(folder)
                else:
                    # Try stripping quotes and whitespace then attempt again
                    p2 = p.strip('"\'')
                    if os.path.isdir(p2):
                        os.startfile(p2)
                    elif os.path.exists(p2):
                        folder = os.path.dirname(p2)
                        if folder:
                            os.startfile(folder)
            except Exception:
                pass

    def _on_context_menu(self, pos: QPoint):
        # Map the position to the table index
        idx = self.table.indexAt(pos)
        if not idx.isValid():
            return

        row = idx.row()
        col = idx.column()
        item = self.table.item(row, col)
        if item is None:
            return

        menu = QMenu(self)
        copy_action = QAction("Copy", self)
        menu.addAction(copy_action)

        def _copy():
            text = item.text()
            if text:
                QApplication.clipboard().setText(text)

        copy_action.triggered.connect(_copy)
        # Show menu at global position
        menu.exec(self.table.viewport().mapToGlobal(pos))
