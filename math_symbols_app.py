import sys
import os
import re
import unicodedata
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QScrollArea, QPushButton, QLabel, QLineEdit,
    QFrame, QGridLayout, QStatusBar, QProgressBar, QComboBox, QSplitter
)
from PySide6.QtCore import Qt, QSize, QThread, Signal, QTimer, Slot
from PySide6.QtGui import QFont, QClipboard

BLOCK_TRANSLATIONS = {
    "Basic Latin": "基础拉丁语", "Latin-1 Supplement": "拉丁语-1 补充", "Latin Extended-A": "拉丁语扩展-A", "Latin Extended-B": "拉丁语扩展-B",
    "IPA Extensions": "IPA 扩展", "Spacing Modifier Letters": "占位修饰符号", "Combining Diacritical Marks": "组合变音符号", "Greek and Coptic": "希腊语及科普特语",
    "Cyrillic": "西里尔字母", "Cyrillic Supplement": "西里尔字母补充", "Armenian": "亚美尼亚语", "Hebrew": "希伯来语", "Arabic": "阿拉伯语",
    "Syriac": "叙利亚语", "Arabic Supplement": "阿拉伯语补充", "Thaana": "它拿字母", "NKo": "西非书面语言 (NKo)", "Samaritan": "撒马利亚语",
    "Mandaic": "曼底安语", "Syriac Supplement": "叙利亚语补充", "Arabic Extended-B": "阿拉伯语扩展-B", "Arabic Extended-A": "阿拉伯语扩展-A",
    "Devanagari": "天城文", "Bengali": "孟加拉语", "Gurmukhi": "古木基文", "Gujarati": "古吉拉特文", "Oriya": "奥里亚文", "Tamil": "泰米尔文",
    "Telugu": "泰卢固文", "Kannada": "康纳达文", "Malayalam": "马拉雅拉姆文", "Sinhala": "僧伽罗文", "Thai": "泰文", "Lao": "老挝文",
    "Tibetan": "藏文", "Myanmar": "缅甸语", "Georgian": "格鲁吉亚语", "Hangul Jamo": "谚文字母", "Ethiopic": "埃塞俄比亚语",
    "Ethiopic Supplement": "埃塞俄比亚语补充", "Cherokee": "切罗基语", "Unified Canadian Aboriginal Syllabics": "统一加拿大原住民音节文字",
    "Ogham": "欧甘字母", "Runic": "卢恩字母", "Tagalog": "塔加路语", "Hanunoo": "哈努诺字母", "Buhid": "布希德文", "Tagbanwa": "塔格巴努亚文",
    "Khmer": "高棉语", "Mongolian": "蒙古文", "Unified Canadian Aboriginal Syllabics Extended": "统一加拿大原住民音节文字扩展",
    "Limbu": "林布文", "Tai Le": "德宏傣文", "New Tai Lue": "西双版纳新傣文", "Khmer Symbols": "高棉语符号", "Buginese": "布吉文",
    "Tai Tham": "兰纳文", "Combining Diacritical Marks Extended": "组合变音符号扩展", "Balinese": "巴厘文", "Sundanese": "巽他文",
    "Batak": "巴塔克文", "Lepcha": "勒嘉文", "Ol Chiki": "桑塔利文", "Cyrillic Extended-C": "西里尔字母扩展-C", "Georgian Extended": "格鲁吉亚语扩展",
    "Sundanese Supplement": "巽他文补充", "Vedic Extensions": "吠陀扩展", "Phonetic Extensions": "音标扩展", "Phonetic Extensions Supplement": "音标扩展补充",
    "Combining Diacritical Marks Supplement": "组合变音符号补充", "Latin Extended Additional": "拉丁语扩展附加", "Greek Extended": "希腊语扩展",
    "General Punctuation": "常用标点", "Superscripts and Subscripts": "上标与下标", "Currency Symbols": "货币符号",
    "Combining Diacritical Marks for Symbols": "符号用组合变音符号", "Letterlike Symbols": "类字母符号", "Number Forms": "数字形式", "Arrows": "箭头",
    "Mathematical Operators": "数学运算符", "Miscellaneous Technical": "杂项技术符号", "Control Pictures": "控制图形",
    "Optical Character Recognition": "光学字符识别 (OCR)", "Enclosed Alphanumerics": "带圈字母数字", "Box Drawing": "制表符", "Block Elements": "方块元素",
    "Geometric Shapes": "几何图形", "Miscellaneous Symbols": "杂项符号", "Dingbats": "装饰符号 (Dingbats)", "Miscellaneous Mathematical Symbols-A": "杂项数学符号-A",
    "Supplemental Arrows-A": "补充箭头-A", "Braille Patterns": "盲文点字", "Supplemental Arrows-B": "补充箭头-B",
    "Miscellaneous Mathematical Symbols-B": "杂项数学符号-B", "Supplemental Mathematical Operators": "补充数学运算符",
    "Miscellaneous Symbols and Arrows": "杂项符号及箭头", "Glagolitic": "格拉哥里字母", "Latin Extended-C": "拉丁语扩展-C", "Coptic": "科普特语",
    "Georgian Supplement": "格鲁吉亚语补充", "Tifinagh": "提非纳文字", "Ethiopic Extended": "埃塞俄比亚语扩展", "Cyrillic Extended-A": "西里尔字母扩展-A",
    "Supplemental Punctuation": "补充标点", "CJK Radicals Supplement": "中日韩汉字部首补充", "Kangxi Radicals": "康熙部首",
    "Ideographic Description Characters": "表意文字描述字符", "CJK Symbols and Punctuation": "中日韩符号和标点", "Hiragana": "平假名", "Katakana": "片假名",
    "Bopomofo": "注音符号", "Hangul Compatibility Jamo": "谚文兼容字母", "Kanbun": "汉文训读符号", "Bopomofo Extended": "注音符号扩展",
    "CJK Strokes": "中日韩笔画", "Katakana Phonetic Extensions": "片假名语音扩展", "Enclosed CJK Letters and Months": "带圈中日韩字母及月份",
    "CJK Compatibility": "中日韩兼容字符", "CJK Unified Ideographs Extension A": "中日韩统一表意文字扩展区-A", "Yijing Hexagram Symbols": "易经六十四卦符号",
    "CJK Unified Ideographs": "中日韩统一表意文字", "Yi Syllables": "彝文音节", "Yi Radicals": "彝文部首", "Lisu": "栗僳语", "Vai": "瓦伊语",
    "Cyrillic Extended-B": "西里尔字母扩展-B", "Bamum": "巴姆穆语", "Modifier Tone Letters": "变调字母", "Latin Extended-D": "拉丁语扩展-D",
    "Syloti Nagri": "锡洛蒂纳格里文", "Common Indic Number Forms": "常用印度数字形式", "Phags-pa": "八思巴文", "Saurashtra": "索罗什特拉文",
    "Devanagari Extended": "天城文扩展", "Kayah Li": "克耶里文字", "Rejang": "拉让文", "Hangul Jamo Extended-A": "谚文字母扩展-A", "Javanese": "爪哇语",
    "Myanmar Extended-B": "缅甸语扩展-B", "Cham": "占文", "Myanmar Extended-A": "缅甸语扩展-A", "Tai Viet": "泰越文", "Meetei Mayek Extensions": "曼尼普尔文扩展",
    "Ethiopic Extended-A": "埃塞俄比亚语扩展-A", "Latin Extended-E": "拉丁语扩展-E", "Cherokee Supplement": "切罗基语补充", "Meetei Mayek": "曼尼普尔文",
    "Hangul Syllables": "谚文音节", "Hangul Jamo Extended-B": "谚文字母扩展-B", "High Surrogates": "高位代理字符", "High Private Use Surrogates": "高位私用代理字符",
    "Low Surrogates": "低位代理字符", "Private Use Area": "私用区", "CJK Compatibility Ideographs": "中日韩兼容表意文字", "Alphabetic Presentation Forms": "字母列报形式",
    "Arabic Presentation Forms-A": "阿拉伯语列报形式-A", "Variation Selectors": "变体选择符", "Vertical Forms": "竖排形式", "Combining Half Marks": "组合半角符号",
    "CJK Compatibility Forms": "中日韩兼容形式", "Small Form Variants": "小写变体", "Arabic Presentation Forms-B": "阿拉伯语列报形式-B",
    "Halfwidth and Fullwidth Forms": "半角及全角字符", "Specials": "特殊字符", "Linear B Syllabary": "线形文字B音节文字", "Linear B Ideograms": "线形文字B表意文字",
    "Aegean Numbers": "爱琴海数字", "Ancient Greek Numbers": "古希腊数字", "Ancient Symbols": "古符号", "Phaistos Disc": "费斯托斯圆盘文字",
    "Lycian": "吕底亚字母", "Carian": "卡里亚字母", "Coptic Epact Numbers": "科普特希腊数字", "Old Italic": "古意大利字母", "Gothic": "哥特字母",
    "Old Permic": "古彼尔姆文字", "Ugaritic": "乌加里特字母", "Old Persian": "古波斯语", "Deseret": "德瑟雷特字母", "Shavian": "萧伯纳字母",
    "Osmanya": "奥斯曼亚字母", "Osage": "欧塞奇字母", "Elbasan": "爱尔巴桑字母", "Caucasian Albanian": "高加索阿尔巴尼亚字母", "Vithkuqi": "维特库奇字母",
    "Todhri": "托德里文", "Linear A": "线形文字A", "Latin Extended-F": "拉丁语扩展-F", "Cypriot Syllabary": "塞浦路斯音节文字", "Imperial Aramaic": "帝国亚拉姆语",
    "Palmyrene": "帕尔米拉字母", "Nabataean": "纳巴泰字母", "Hatran": "哈特拉字母", "Phoenician": "腓尼基字母", "Lydian": "吕底亚语",
    "Sidetic": "西代提克文", "Meroitic Hieroglyphs": "梅里埃象形文字", "Meroitic Cursive": "梅里埃草书", "Kharoshthi": "佉卢文",
    "Old South Arabian": "古南阿拉伯字母", "Old North Arabian": "古北阿拉伯字母", "Manichaean": "摩尼教字母", "Avestan": "阿维斯塔语",
    "Inscriptional Parthian": "铭文帕提亚文", "Inscriptional Pahlavi": "铭文帕拉维文", "Psalter Pahlavi": "赞美诗帕拉维文", "Old Turkic": "古突厥文 (鄂尔浑文)",
    "Old Hungarian": "古匈牙利字母", "Hanifi Rohingya": "哈乃斐罗兴亚文字", "Garay": "加雷文字", "Rumi Numeral Symbols": "鲁米数字符号",
    "Yezidi": "雅兹迪文字", "Arabic Extended-C": "阿拉伯语扩展-C", "Old Sogdian": "古粟特字母", "Sogdian": "粟特字母", "Old Uyghur": "古回鹘字母",
    "Chorasmian": "花剌子模字母", "Elymaic": "埃利迈文", "Brahmi": "婆罗米文", "Kaithi": "凯提文", "Sora Sompeng": "索拉僧平文字", "Chakma": "查克马文",
    "Mahajani": "马哈佳尼文", "Sharada": "舍拉达文", "Sinhala Archaic Numbers": "僧伽罗古数字", "Khojki": "库基文", "Multani": "木尔坦文",
    "Khudawadi": "库达瓦迪文", "Grantha": "格兰塔文", "Tulu-Tigalari": "图卢-蒂加拉里文", "Newa": "内瓦文字", "Tirhuta": "提卢塔文",
    "Siddham": "悉昙文", "Modi": "莫迪文", "Mongolian Supplement": "蒙古文补充", "Takri": "塔克里语", "Myanmar Extended-C": "缅甸语扩展-C",
    "Ahom": "阿洪姆文", "Dogra": "多格拉文", "Warang Citi": "瓦朗齐地文", "Dives Akuru": "迪维希语阿库鲁文", "Nandinagari": "楠迪纳加里文",
    "Zanabazar Square": "札那巴札尔方形字母", "Soyombo": "索永伯字母", "Unified Canadian Aboriginal Syllabics Extended-A": "统一加拿大原住民音节文字扩展-A",
    "Pau Cin Hau": "包钦豪文字", "Devanagari Extended-A": "天城文扩展-A", "Sharada Supplement": "舍拉达文补充", "Sunuwar": "苏努瓦尔文",
    "Bhaiksuki": "拜克苏基文", "Marchen": "玛琴文", "Masaram Gondi": "贡德文字", "Gunjala Gondi": "贡贾拉贡德文字", "Tolong Siki": "托隆希基文",
    "Makasar": "望加锡文", "Kawi": "卡维文", "Lisu Supplement": "栗僳语补充", "Tamil Supplement": "泰米尔语补充", "Cuneiform": "楔形文字",
    "Cuneiform Numbers and Punctuation": "楔形文字数字和标点", "Early Dynastic Cuneiform": "早期王朝楔形文字", "Cypro-Minoan": "塞浦路斯-米诺斯文字",
    "Egyptian Hieroglyphs": "埃及圣书体", "Egyptian Hieroglyph Format Controls": "埃及圣书体格式控制符", "Egyptian Hieroglyphs Extended-A": "埃及圣书体扩展-A",
    "Anatolian Hieroglyphs": "安纳托利亚象形文字", "Gurung Khema": "古隆克马文", "Bamum Supplement": "巴姆穆语补充", "Mro": "姆罗文",
    "Tangsa": "唐萨文", "Bassa Vah": "巴萨瓦文字", "Pahawh Hmong": "巴浩苗文", "Kirat Rai": "基拉特莱文", "Medefaidrin": "梅德法伊德语文字",
    "Beria Erfe": "贝里亚埃尔费文字", "Miao": "苗语", "Ideographic Symbols and Punctuation": "表意文字符号与标点", "Tangut": "西夏文",
    "Tangut Components": "西夏文部件", "Khitan Small Script": "契丹小字", "Tangut Supplement": "西夏文补充", "Tangut Components Supplement": "西夏文部件补充",
    "Kana Extended-B": "假名扩展-B", "Kana Supplement": "假名补充", "Kana Extended-A": "假名扩展-A", "Small Kana Extension": "小假名扩展",
    "Nushu": "女书", "Duployan": "杜普洛伊速记文字", "Shorthand Format Controls": "速记格式控制符", "Symbols for Legacy Computing Supplement": "传统计算符号补充",
    "Miscellaneous Symbols Supplement": "杂项符号补充", "Znamenny Musical Notation": "兹纳梅尼音乐符号", "Byzantine Musical Symbols": "拜占庭音乐符号",
    "Musical Symbols": "音乐符号", "Ancient Greek Musical Notation": "古希腊音乐记谱法", "Kaktovik Numerals": "卡克托维克数字", "Mayan Numerals": "玛雅数字",
    "Tai Xuan Jing Symbols": "太玄经符号", "Counting Rod Numerals": "算筹数字", "Mathematical Alphanumeric Symbols": "数学字母数字符号",
    "Sutton SignWriting": "萨顿书写符号", "Latin Extended-G": "拉丁语扩展-G", "Glagolitic Supplement": "格拉哥里字母补充", "Cyrillic Extended-D": "西里尔字母扩展-D",
    "Nyiakeng Puachue Hmong": "义江普求苗文", "Toto": "托托文", "Wancho": "万秋文", "Nag Mundari": "纳格蒙达里文", "Ol Onal": "奥欧纳尔文",
    "Tai Yo": "傣哟文", "Ethiopic Extended-B": "埃塞俄比亚语扩展-B", "Mende Kikakui": "门德基卡库文字", "Adlam": "阿德拉姆文字",
    "Indic Siyaq Numbers": "印度希亚克数字", "Ottoman Siyaq Numbers": "奥斯曼希亚克数字", "Arabic Mathematical Alphabetic Symbols": "阿拉伯语数学字母符号",
    "Mahjong Tiles": "麻将牌", "Domino Tiles": "多米诺骨牌", "Playing Cards": "扑克牌", "Enclosed Alphanumeric Supplement": "带圈字母数字补充",
    "Enclosed Ideographic Supplement": "带圈表意文字补充", "Miscellaneous Symbols and Pictographs": "杂项符号及象形文字", "Emoticons": "表情符号",
    "Ornamental Dingbats": "装饰图形补充", "Transport and Map Symbols": "交通及地图符号", "Alchemical Symbols": "炼金术符号",
    "Geometric Shapes Extended": "几何图形扩展", "Supplemental Arrows-C": "补充箭头-C", "Supplemental Symbols and Pictographs": "补充符号及象形文字",
    "Chess Symbols": "国际象棋符号", "Symbols and Pictographs Extended-A": "符号及象形文字扩展-A", "Symbols for Legacy Computing": "传统计算符号",
    "CJK Unified Ideographs Extension B": "中日韩统一表意文字扩展区-B", "CJK Unified Ideographs Extension C": "中日韩统一表意文字扩展区-C",
    "CJK Unified Ideographs Extension D": "中日韩统一表意文字扩展区-D", "CJK Unified Ideographs Extension E": "中日韩统一表意文字扩展区-E",
    "CJK Unified Ideographs Extension F": "中日韩统一表意文字扩展区-F", "CJK Unified Ideographs Extension I": "中日韩统一表意文字扩展区-I",
    "CJK Compatibility Ideographs Supplement": "中日韩兼容表意文字补充", "CJK Unified Ideographs Extension G": "中日韩统一表意文字扩展区-G",
    "CJK Unified Ideographs Extension H": "中日韩统一表意文字扩展区-H", "CJK Unified Ideographs Extension J": "中日韩统一表意文字扩展区-J",
    "Tags": "标签", "Variation Selectors Supplement": "变体选择符补充", "Supplementary Private Use Area-A": "补充私用区-A",
    "Supplementary Private Use Area-B": "补充私用区-B",
}

print(f"Loaded {len(BLOCK_TRANSLATIONS)} block translations.")

class SymbolButton(QPushButton):
    def __init__(self, char, parent=None):
        super().__init__(char, parent)
        self.char = char
        self.setFixedSize(QSize(60, 60))
        
        # Multi-font fallback strategy for maximum coverage on Windows
        font = QFont()
        font.setFamilies([
            "Segoe UI Symbol", 
            "Segoe UI Emoji", 
            "Cambria Math", 
            "Microsoft YaHei", 
            "Malgun Gothic", 
            "Arial Unicode MS",
            "Noto Sans Symbols"
        ])
        font.setPointSize(24)
        self.setFont(font)
        
        try:
            name = unicodedata.name(char).title()
        except:
            name = "Unknown Name"
            
        self.setToolTip(f"Code: U+{ord(char):04X}\nName: {name}\nClick to copy")
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
        # 1. Superscripts List
        # Latin-1: ² (B2), ³ (B3), ¹ (B9) + Range 2070-207F
        # Plus comprehensive superscript letters (a-z)
        extra_sups = [
            chr(0x1D43), chr(0x1D47), chr(0x1D9C), chr(0x1D48), chr(0x1D49), chr(0x1DA0), 
            chr(0x1D4D), chr(0x02B0), chr(0x2071), chr(0x02B2), chr(0x1D4F), chr(0x02E1), 
            chr(0x1D50), chr(0x207F), chr(0x1D52), chr(0x1D56), chr(0x02B3), chr(0x02E2), 
            chr(0x1D57), chr(0x1D58), chr(0x1D5B), chr(0x02B7), chr(0x02E3), chr(0x02B8), chr(0x1DBB)
        ]
        sups_list = [chr(0x00B2), chr(0x00B3), chr(0x00B9)] + [chr(c) for c in range(0x2070, 0x2080)] + extra_sups
        
        # 2. Subscripts List
        # Range 2080-209F + extra math subs (i, j, r, u, v)
        extra_subs = [chr(0x1D62), chr(0x2C7C), chr(0x1D63), chr(0x1D64), chr(0x1D65)]
        subs_list = [chr(c) for c in range(0x2080, 0x20A0)] + extra_subs
        
        return {
            "逻辑与集合 (Logic & Sets)": [(0x2200, 0x22FF), (0x2A00, 0x2AFF)],
            "范畴论与箭头 (Category & Arrows)": [(0x2190, 0x21FF), (0x27F0, 0x27FF), (0x2900, 0x297F), (0x2B00, 0x2BFF)],
            "群论与代数 (Algebra)": [(0x2102, 0x2102), (0x210D, 0x210D), (0x2115, 0x2115), (0x2119, 0x2119), (0x211A, 0x211A), (0x211D, 0x211D), (0x2124, 0x2124), (0x1D400, 0x1D7FF)],
            "拓扑学 (Topology)": [0x2202, 0x2207, (0x27C0, 0x27EF), (0x2980, 0x29FF)],
            "模型论 (Model Theory)": [(0x22A2, 0x22AF), (0x227C, 0x227D), (0x2250, 0x225F), (0x2300, 0x23FF)],
            "类型论 / λ 演算 (Type Theory)": [0x03BB, 0x03BC, 0x03A0, 0x03A3, 0x2200, 0x2203, 0x2192, 0x21A3, 0x21A6, 0x22A2, 0x22EE, 0x2254, (0x27E6, 0x27EB)],
            "上标字符 (Superscripts)": sups_list,
            "下标字符 (Subscripts)": subs_list,
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
                        # Add translation if exists
                        chinese_name = BLOCK_TRANSLATIONS.get(name)
                        display_name = f"{name} ({chinese_name})" if chinese_name else name
                        blocks[display_name] = [(int(start_hex, 16), int(end_hex, 16))]
        except: pass
        return blocks

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        # Create Splitter
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        # 1. Sidebar Panel (Categories)
        sidebar_panel = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_panel)
        sidebar_layout.setContentsMargins(0, 0, 5, 0)
        sidebar_layout.setSpacing(10)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["⭐ 精选数学符号", "🌐 全部 Unicode 区块"])
        self.mode_combo.currentIndexChanged.connect(self.switch_mode)
        sidebar_layout.addWidget(self.mode_combo)

        # Sidebar Search
        self.cat_search = QLineEdit()
        self.cat_search.setPlaceholderText("🔍 过滤分类名称 (支持中英)...")
        self.cat_search.textChanged.connect(self.filter_categories)
        sidebar_layout.addWidget(self.cat_search)

        self.sidebar = QListWidget()
        self.sidebar.setFont(QFont("Microsoft YaHei", 10))
        self.sidebar.currentRowChanged.connect(self.request_category_load)
        sidebar_layout.addWidget(self.sidebar)
        
        self.splitter.addWidget(sidebar_panel)

        # 2. Main Content Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        right_layout.setSpacing(10)
        
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
        self.scroll_area.setStyleSheet("QScrollArea { border: 1px solid #e0e0e0; background-color: #ffffff; border-radius: 5px; }")
        
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)
        
        self.symbol_container = QWidget()
        self.symbol_grid = QGridLayout(self.symbol_container)
        self.symbol_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.symbol_grid.setSpacing(10)
        self.scroll_area.setWidget(self.symbol_container)
        
        right_layout.addWidget(self.scroll_area)
        
        self.splitter.addWidget(right_panel)
        
        # Initial splitter sizes
        self.splitter.setSizes([280, 920])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

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
