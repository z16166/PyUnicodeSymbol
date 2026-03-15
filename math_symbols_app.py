import sys
import unicodedata
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QScrollArea, QPushButton, QLabel, QLineEdit,
    QFrame, QGridLayout, QStatusBar, QProgressBar
)
from PySide6.QtCore import Qt, QSize, QThread, Signal, QTimer, Slot
from PySide6.QtGui import QFont, QClipboard

class SymbolButton(QPushButton):
    def __init__(self, char, parent=None):
        super().__init__(char, parent)
        self.char = char
        self.setFixedSize(QSize(60, 60))
        self.setFont(QFont("Segoe UI Symbol", 24))
        self.setToolTip(f"Code: U+{ord(char):04X}\nClick to copy")
        self.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #f0f7ff;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #cce4f7;
            }
        """)
        self.clicked.connect(self.copy_to_clipboard)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.char)
        window = self.window()
        if isinstance(window, QMainWindow):
            window.statusBar().showMessage(f"已复制: {self.char} (U+{ord(self.char):04X})", 2000)

class LoadWorker(QThread):
    finished_batch = Signal(list)
    progress = Signal(int)

    def __init__(self, symbols, cols):
        super().__init__()
        self.symbols = symbols
        self.cols = cols
        self._is_running = True

    def run(self):
        batch_size = 50
        current_batch = []
        for i, char in enumerate(self.symbols):
            if not self._is_running: break
            current_batch.append(char)
            if len(current_batch) >= batch_size:
                self.finished_batch.emit(current_batch)
                current_batch = []
                # Small sleep to let UI thread breathe
                self.msleep(10)
            
            if i % 10 == 0:
                self.progress.emit(int((i / len(self.symbols)) * 100))
        
        if current_batch and self._is_running:
            self.finished_batch.emit(current_batch)
        self.progress.emit(100)

    def stop(self):
        self._is_running = False

class MathSymbolViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultimate Unicode Math Symbol Viewer (Async Mode)")
        self.resize(1100, 750)
        
        self.symbols_data = self.initialize_data()
        self.worker = None
        self.loaded_count = 0
        
        self.init_ui()

    def initialize_data(self):
        # Precise ordering for superscripts and subscripts
        superscripts = [chr(0x2070), chr(0x00B9), chr(0x00B2), chr(0x00B3)] + [chr(c) for c in range(0x2074, 0x207A)]
        subscripts = [chr(c) for c in range(0x2080, 0x208A)]
        
        data = {
            "逻辑与集合 (Logic & Sets)": [
                (0x2200, 0x22FF), # Mathematical Operators
                (0x2A00, 0x2AFF), # Supplemental Mathematical Operators
            ],
            "范畴论与箭头 (Category & Arrows)": [
                (0x2190, 0x21FF), # Arrows
                (0x27F0, 0x27FF), # Supplemental Arrows-A
                (0x2900, 0x297F), # Supplemental Arrows-B
                (0x2B00, 0x2BFF), # Misc Symbols and Arrows
            ],
            "群论与代数 (Algebra)": [
                (0x2102, 0x2102), (0x210D, 0x210D), (0x2115, 0x2115), 
                (0x2119, 0x2119), (0x211A, 0x211A), (0x211D, 0x211D), (0x2124, 0x2124),
                (0x212C, 0x212C), (0x2130, 0x2133), (0x2135, 0x2138),
                (0x1D400, 0x1D7FF), # Math Alphanumeric
            ],
            "拓扑学 (Topology)": [
                0x2202, 0x2207,
                (0x27C0, 0x27EF), # Misc Math Symbols-A
                (0x2980, 0x29FF), # Misc Math Symbols-B
            ],
            "模型论 (Model Theory)": [
                (0x22A2, 0x22AF), 
                (0x227C, 0x227D), 
                (0x2250, 0x225F),
                (0x2300, 0x23FF),
            ],
            "类型论 / λ 演算 (Type Theory)": [
                0x03BB, 0x03BC, 0x03A0, 0x03A3, 0x2200, 0x2203, 
                0x2192, 0x21A3, 0x21A6, 0x22A2, 0x22EE, 0x2254,
                (0x27E6, 0x27EB),
            ],
            "上标与下标 (Sub/Superscripts)": superscripts + subscripts,
            "常用杂项数学符号 (Misc)": [
                0x221E, (0x222B, 0x2233), 0x2211, (0x220F, 0x2210), 
                0x2212, (0x2215, 0x2218), (0x221A, 0x221D), (0x223C, 0x2240), (0x2241, 0x2250),
            ],
            "段落编号 (Numbers)": [
                (0x2460, 0x24FF), # Encircled Alphanumerics
                (0x2768, 0x2775), # Dingbat circled
                0x24EA,
                (0x2776, 0x2793), # Dingbat negative circled
            ]
        }
        return data

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setFont(QFont("Microsoft YaHei", 10))
        self.sidebar.addItems(self.symbols_data.keys())
        self.sidebar.currentRowChanged.connect(self.request_category_load)
        main_layout.addWidget(self.sidebar)

        # Right side content
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索符号名称或代码 (e.g., lambda, 2200)...")
        self.search_input.setStyleSheet("padding: 8px; border-radius: 5px; border: 1px solid #ccc;")
        self.search_input.textChanged.connect(self.filter_symbols)
        search_layout.addWidget(self.search_input)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(100)
        self.progress_bar.setVisible(False)
        search_layout.addWidget(self.progress_bar)
        
        right_layout.addLayout(search_layout)

        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #f8f9fa; }")
        
        self.symbol_container = QWidget()
        self.symbol_grid = QGridLayout(self.symbol_container)
        self.symbol_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.symbol_grid.setSpacing(8)
        self.scroll_area.setWidget(self.symbol_container)
        
        right_layout.addWidget(self.scroll_area)
        main_layout.addWidget(right_panel)

        self.setStatusBar(QStatusBar())
        
        # Debounce for resize
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.deferred_resize)
        
        # Initial display
        QTimer.singleShot(100, lambda: self.sidebar.setCurrentRow(0))

    def request_category_load(self, index):
        if index < 0: return
        
        category_name = list(self.symbols_data.keys())[index]
        ranges = self.symbols_data[category_name]
        
        symbols = []
        for r in ranges:
            if isinstance(r, tuple):
                for code in range(r[0], r[1] + 1):
                    symbols.append(chr(code))
            elif isinstance(r, int):
                symbols.append(chr(r))
            else:
                symbols.append(r)
        
        # Filter non-printable
        symbols = [s for s in symbols if self.is_printable(s)]
        self.start_async_load(symbols)

    def start_async_load(self, symbols):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        # Clear grid
        while self.symbol_grid.count():
            item = self.symbol_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.loaded_count = 0
        self.current_symbols = symbols
        
        viewport_width = self.scroll_area.viewport().width()
        cols = max(1, (viewport_width - 25) // 70)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker = LoadWorker(symbols, cols)
        self.worker.finished_batch.connect(self.add_symbols_batch)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(lambda: self.progress_bar.setVisible(False))
        self.worker.start()

    @Slot(list)
    def add_symbols_batch(self, batch):
        viewport_width = self.scroll_area.viewport().width()
        cols = max(1, (viewport_width - 25) // 70)
        
        for char in batch:
            btn = SymbolButton(char)
            self.symbol_grid.addWidget(btn, self.loaded_count // cols, self.loaded_count % cols)
            self.loaded_count += 1

    def is_printable(self, char):
        category = unicodedata.category(char)
        return category not in ('Cc', 'Cs', 'Cn')

    def filter_symbols(self, text):
        text = text.lower().strip()
        if not text:
            self.request_category_load(self.sidebar.currentRow())
            return

        # Filtering happens globally
        all_matches = []
        for cat, ranges in self.symbols_data.items():
            for r in ranges:
                if isinstance(r, tuple): start, end = r
                elif isinstance(r, int): start, end = r, r
                else: 
                    char = r
                    if text in char.lower(): all_matches.append(char)
                    try: 
                        name = unicodedata.name(char).lower()
                        if text in name: all_matches.append(char)
                    except: pass
                    continue
                
                for code in range(start, end + 1):
                    char = chr(code)
                    if not self.is_printable(char): continue
                    if text in f"{code:04X}".lower() or text in char:
                        all_matches.append(char)
                    else:
                        try:
                            if text in unicodedata.name(char).lower():
                                all_matches.append(char)
                        except: pass
        
        all_matches = list(dict.fromkeys(all_matches)) # unique
        self.statusBar().showMessage(f"找到 {len(all_matches)} 个匹配项")
        self.start_async_load(all_matches)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_timer.start(300)

    def deferred_resize(self):
        # On resize, we need to re-layout from current list
        if hasattr(self, 'current_symbols') and self.current_symbols:
            self.start_async_load(self.current_symbols)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    viewer = MathSymbolViewer()
    viewer.show()
    sys.exit(app.exec())
