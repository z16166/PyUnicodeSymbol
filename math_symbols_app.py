import sys
import os
import re
import unicodedata
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QScrollArea, QPushButton, QLabel, QLineEdit,
    QFrame, QGridLayout, QStatusBar, QProgressBar, QComboBox
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

class GlobalSearchWorker(QThread):
    finished_found = Signal(list)
    progress = Signal(int)

    def __init__(self, search_pool, text):
        super().__init__()
        self.search_pool = search_pool
        self.text = text.lower().strip()
        self._is_running = True

    def run(self):
        all_matches = []
        total_cats = len(self.search_pool)
        
        for idx, (cat, ranges) in enumerate(self.search_pool.items()):
            if not self._is_running: break
            
            for r in ranges:
                if not self._is_running: break
                
                if isinstance(r, tuple): start, end = r
                elif isinstance(r, int): start, end = r, r
                else: 
                    char = r
                    if self.text in char.lower(): all_matches.append(char)
                    try:
                        name = unicodedata.name(char).lower()
                        if self.text in name: all_matches.append(char)
                    except: pass
                    continue
                
                # Optimized search for large ranges
                for code in range(start, end + 1):
                    char = chr(code)
                    # Check hex or char directly
                    if self.text in char or self.text in f"{code:04X}".lower():
                        all_matches.append(char)
                    else:
                        try:
                            # Name lookup is expensive, maybe skip for huge blocks unless specifically requested?
                            # For "Ultimate" experience, we do it but keep responsiveness
                            if self.text in unicodedata.name(char).lower():
                                all_matches.append(char)
                        except: pass
            
            self.progress.emit(int((idx / total_cats) * 100))
        
        if self._is_running:
            # unique
            unique_matches = list(dict.fromkeys(all_matches))
            self.finished_found.emit(unique_matches)

    def stop(self):
        self._is_running = False

class MathSymbolViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultimate Unicode Symbol Viewer (Pro)")
        self.resize(1200, 800)
        
        self.featured_data = self.initialize_featured_data()
        self.full_blocks_data = self.parse_blocks_txt()
        self.current_data_source = self.featured_data
        
        self.active_symbols = []
        self.loaded_count = 0
        self.batch_size = 200
        
        self.search_worker = None
        
        self.init_ui()

    def initialize_featured_data(self):
        # Complete Superscripts and Subscripts range (2070-209F)
        # Plus common missing subscripts (i, j, r, u, v)
        # i: 1D62, j: 2C7C, r: 1D63, u: 1D64, v: 1D65
        extra_subs = [chr(0x1D62), chr(0x2C7C), chr(0x1D63), chr(0x1D64), chr(0x1D65)]
        
        # Plus comprehensive superscript letters (a-z)
        # a:1D43, b:1D47, c:1D9C, d:1D48, e:1D49, f:1DA0, g:1D4D, h:02B0, i:2071, j:02B2, k:1D4F, l:02E1, m:1D50, n:207F, o:1D52, p:1D56, r:02B3, s:02E2, t:1D57, u:1D58, v:1D5B, w:02B7, x:02E3, y:02B8, z:1DBB
        extra_sups = [
            chr(0x1D43), chr(0x1D47), chr(0x1D9C), chr(0x1D48), chr(0x1D49), chr(0x1DA0), 
            chr(0x1D4D), chr(0x02B0), chr(0x2071), chr(0x02B2), chr(0x1D4F), chr(0x02E1), 
            chr(0x1D50), chr(0x207F), chr(0x1D52), chr(0x1D56), chr(0x02B3), chr(0x02E2), 
            chr(0x1D57), chr(0x1D58), chr(0x1D5B), chr(0x02B7), chr(0x02E3), chr(0x02B8), chr(0x1DBB)
        ]
        
        sub_sup_list = [chr(0x00B2), chr(0x00B3), chr(0x00B9)] + [chr(c) for c in range(0x2070, 0x20A0)] + extra_subs + extra_sups
        
        return {
            "逻辑与集合 (Logic & Sets)": [(0x2200, 0x22FF), (0x2A00, 0x2AFF)],
            "范畴论与箭头 (Category & Arrows)": [(0x2190, 0x21FF), (0x27F0, 0x27FF), (0x2900, 0x297F), (0x2B00, 0x2BFF)],
            "群论与代数 (Algebra)": [(0x2102, 0x2102), (0x210D, 0x210D), (0x2115, 0x2115), (0x2119, 0x2119), (0x211A, 0x211A), (0x211D, 0x211D), (0x2124, 0x2124), (0x1D400, 0x1D7FF)],
            "拓扑学 (Topology)": [0x2202, 0x2207, (0x27C0, 0x27EF), (0x2980, 0x29FF)],
            "模型论 (Model Theory)": [(0x22A2, 0x22AF), (0x227C, 0x227D), (0x2250, 0x225F), (0x2300, 0x23FF)],
            "类型论 / λ 演算 (Type Theory)": [0x03BB, 0x03BC, 0x03A0, 0x03A3, 0x2200, 0x2203, 0x2192, 0x21A3, 0x21A6, 0x22A2, 0x22EE, 0x2254, (0x27E6, 0x27EB)],
            "上标与下标 (Sub/Superscripts)": sub_sup_list,
            "表情符号 (Smilies)": [(0x1F600, 0x1F64F)],
            "常用杂项数学符号 (Misc)": [0x221E, (0x222B, 0x2233), 0x2211, (0x220F, 0x2210), 0x2212, (0x2215, 0x2218), (0x221A, 0x221D), (0x223C, 0x2240), (0x2241, 0x2250)],
            "段落编号 (Numbers)": [(0x2460, 0x24FF), (0x2768, 0x2775), 0x24EA, (0x2776, 0x2793)]
        }

    def parse_blocks_txt(self):
        blocks = {}
        file_path = "Blocks.txt"
        if not os.path.exists(file_path):
            return {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("@"): continue
                    match = re.match(r"([0-9A-Fa-f]+)\.\.([0-9A-Fa-f]+);\s*(.*)", line)
                    if match:
                        start_hex, end_hex, name = match.groups()
                        blocks[name] = [(int(start_hex, 16), int(end_hex, 16))]
        except: pass
        return blocks

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 1. Sidebar Panel (Categories)
        sidebar_panel = QWidget()
        sidebar_panel.setFixedWidth(260)
        sidebar_layout = QVBoxLayout(sidebar_panel)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["⭐ 精选数学符号", "🌐 全部 Unicode 区块"])
        self.mode_combo.currentIndexChanged.connect(self.switch_mode)
        sidebar_layout.addWidget(self.mode_combo)

        # Sidebar Search
        self.cat_search = QLineEdit()
        self.cat_search.setPlaceholderText("🔍 过滤分类名称...")
        self.cat_search.textChanged.connect(self.filter_categories)
        sidebar_layout.addWidget(self.cat_search)

        self.sidebar = QListWidget()
        self.sidebar.setFont(QFont("Microsoft YaHei", 10))
        self.sidebar.currentRowChanged.connect(self.request_category_load)
        sidebar_layout.addWidget(self.sidebar)
        
        main_layout.addWidget(sidebar_panel)

        # 2. Main Content Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main Search
        search_layout = QHBoxLayout()
        self.char_search = QLineEdit()
        self.char_search.setPlaceholderText("🔍 全局字符搜索 (名称或 Hex 代码)...")
        self.char_search.setStyleSheet("padding: 10px; border-radius: 5px; border: 1px solid #ccc;")
        self.char_search.textChanged.connect(self.request_global_search)
        search_layout.addWidget(self.char_search)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(100)
        self.progress_bar.setVisible(False)
        search_layout.addWidget(self.progress_bar)
        right_layout.addLayout(search_layout)

        # Scroll Area for Grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #ffffff; }")
        
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)
        
        self.symbol_container = QWidget()
        self.symbol_grid = QGridLayout(self.symbol_container)
        self.symbol_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.symbol_grid.setSpacing(10)
        self.scroll_area.setWidget(self.symbol_container)
        
        right_layout.addWidget(self.scroll_area)
        
        # Load Hint Label
        self.load_hint = QLabel("")
        self.load_hint.setAlignment(Qt.AlignCenter)
        self.load_hint.setStyleSheet("""
            QLabel {
                background-color: #f0f7ff;
                color: #0078d4;
                padding: 10px;
                border-top: 1px solid #cce4f7;
                font-weight: bold;
            }
        """)
        self.load_hint.setVisible(False)
        right_layout.addWidget(self.load_hint)
        
        main_layout.addWidget(right_panel)

        self.setStatusBar(QStatusBar())
        
        # Debounce/Delay timer for search
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_global_search)

        # Debounce timer for resize
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.deferred_resize)

        self.switch_mode(0)

    def switch_mode(self, index):
        self.sidebar.clear()
        if index == 0: self.current_data_source = self.featured_data
        else: self.current_data_source = self.full_blocks_data
        self.sidebar.addItems(self.current_data_source.keys())
        self.sidebar.setCurrentRow(0)

    def filter_categories(self, text):
        text = text.lower().strip()
        visible_items = 0
        last_item = None
        for i in range(self.sidebar.count()):
            item = self.sidebar.item(i)
            matches = not text or text in item.text().lower()
            item.setHidden(not matches)
            if matches:
                visible_items += 1
                last_item = item
        
        # If no item is selected or visible, clear right panel
        current = self.sidebar.currentItem()
        if not current or current.isHidden():
            self.clear_grid()
            self.statusBar().showMessage("没有选中的分类")

    def request_category_load(self, index):
        if index < 0: return
        
        item = self.sidebar.item(index)
        if not item or item.isHidden(): 
            self.active_symbols = []
            self.clear_grid()
            self.update_load_hint()
            return

        category_name = item.text()
        ranges = self.current_data_source[category_name]
        
        symbols = []
        for r in ranges:
            if isinstance(r, tuple):
                for code in range(r[0], r[1] + 1): symbols.append(chr(code))
            elif isinstance(r, int): symbols.append(chr(r))
            else: symbols.append(r)
        
        self.active_symbols = [s for s in symbols if self.is_printable(s)]
        self.reset_and_load_initial()

    def clear_grid(self):
        # Quickest way to clear: replace container
        if hasattr(self, 'symbol_container') and self.symbol_container:
            self.symbol_container.setParent(None)
            self.symbol_container.deleteLater()
            
        self.symbol_container = QWidget()
        self.symbol_grid = QGridLayout(self.symbol_container)
        self.symbol_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.symbol_grid.setSpacing(10)
        self.scroll_area.setWidget(self.symbol_container)
        self.loaded_count = 0
        self.update_load_hint()

    def reset_and_load_initial(self):
        self.clear_grid()
        self.load_next_batch()
        # Initial check to fill space if 200 isn't enough for a large screen
        QTimer.singleShot(200, self.check_and_fill_space)

    def deferred_resize(self):
        # On resize, rearrange existing widgets into new grid columns
        if not self.active_symbols or self.symbol_grid.count() == 0:
            return
            
        viewport_width = self.scroll_area.viewport().width()
        if viewport_width <= 0:
            viewport_width = self.scroll_area.width() - 20
        cols = max(1, (viewport_width - 30) // 75)
        
        # Suspend updates during reflow
        self.symbol_container.setUpdatesEnabled(False)
        
        widgets = []
        # Extract all widgets
        while self.symbol_grid.count():
            item = self.symbol_grid.takeAt(0)
            if item.widget():
                widgets.append(item.widget())
        
        # Re-add widgets in new positions
        for idx, widget in enumerate(widgets):
            self.symbol_grid.addWidget(widget, idx // cols, idx % cols)
            
        self.symbol_container.setUpdatesEnabled(True)
        self.symbol_container.update()
        self.update_load_hint()

        # Always check if we need to fill more space after a resize
        if self.loaded_count < len(self.active_symbols):
            QTimer.singleShot(200, self.check_and_fill_space)

    def check_and_fill_space(self):
        if self.loaded_count >= len(self.active_symbols):
            self.update_load_hint()
            return
            
        # Robust check: if container height is less than viewport height + margin, load more
        container_height = self.symbol_container.sizeHint().height()
        viewport_height = self.scroll_area.viewport().height()
        
        # Also check scrollbar as a fallback
        bar = self.scroll_area.verticalScrollBar()
        
        if container_height < viewport_height + 50 or bar.maximum() <= 0:
            self.load_next_batch()
            # If we loaded more, check again after a short delay for layout to update
            QTimer.singleShot(200, self.check_and_fill_space)
        else:
            self.update_load_hint()

    def load_next_batch(self):
        if self.loaded_count >= len(self.active_symbols): 
            self.update_load_hint()
            return
        
        batch = self.active_symbols[self.loaded_count : self.loaded_count + self.batch_size]
        
        # Determine viewport width. ScrollArea might not have its final size yet
        viewport_width = self.scroll_area.viewport().width()
        if viewport_width <= 0:
            viewport_width = self.scroll_area.width() - 20
            
        cols = max(1, (viewport_width - 30) // 75)
        
        self.symbol_container.setUpdatesEnabled(False)
        for char in batch:
            btn = SymbolButton(char)
            self.symbol_grid.addWidget(btn, self.loaded_count // cols, self.loaded_count % cols)
            self.loaded_count += 1
        self.symbol_container.setUpdatesEnabled(True)
        self.update_load_hint()

    def update_load_hint(self):
        total = len(self.active_symbols)
        if total == 0:
            self.load_hint.setVisible(False)
            return

        if self.loaded_count < total:
            self.load_hint.setText(f"︾ 继续向下滚动加载更多字符 (已加载 {self.loaded_count} / {total})")
            self.load_hint.setStyleSheet("background-color: #f0f7ff; color: #0078d4; border-top: 1px solid #cce4f7; padding: 10px; font-weight: bold;")
            self.load_hint.setVisible(True)
        else:
            self.load_hint.setText(f"✅ 该分类共 {total} 个字符已全部加载完毕")
            self.load_hint.setStyleSheet("background-color: #f6fff6; color: #2d8a2d; border-top: 1px solid #d4ecd4; padding: 10px; font-weight: normal;")
            self.load_hint.setVisible(True)
            # Auto-hide after 3 seconds if done
            QTimer.singleShot(3000, lambda: self.load_hint.setVisible(False) if self.loaded_count >= len(self.active_symbols) else None)

    def on_scroll(self, value):
        # Trigger when scroll is near bottom (e.g., 80% down)
        bar = self.scroll_area.verticalScrollBar()
        if bar.maximum() > 0 and value > bar.maximum() * 0.8:
            self.load_next_batch()

    def request_global_search(self, text):
        if not text:
            self.request_category_load(self.sidebar.currentRow())
            return
        self.search_timer.start(500) # 500ms delay

    def perform_global_search(self):
        text = self.char_search.text()
        if not text: return
        
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop()
            self.search_worker.wait()
        
        search_pool = {**self.featured_data, **self.full_blocks_data}
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.search_worker = GlobalSearchWorker(search_pool, text)
        self.search_worker.progress.connect(self.progress_bar.setValue)
        self.search_worker.finished_found.connect(self.on_search_finished)
        self.search_worker.start()

    @Slot(list)
    def on_search_finished(self, matches):
        self.progress_bar.setVisible(False)
        self.active_symbols = matches
        self.statusBar().showMessage(f"全局搜索找到 {len(matches)} 个结果")
        self.reset_and_load_initial()

    def is_printable(self, char):
        return unicodedata.category(char) not in ('Cc', 'Cs', 'Cn')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_timer.start(300)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    viewer = MathSymbolViewer()
    viewer.show()
    sys.exit(app.exec())
