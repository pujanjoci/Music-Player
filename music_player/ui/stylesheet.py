# Premium Clean Dark Theme QSS — Music Player (Offline)

DARK_STYLESHEET = """
/* ============ Global ============ */
QWidget {
    color: #E5E7EB; /* Gray 200 */
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    background-color: transparent;
}

QMainWindow {
    background-color: #262626; /* Neutral 800 */
}

/* ============ Two-Column Layout ============ */
QFrame#sidebarFrame {
    background-color: #171717; /* Neutral 900 */
    border-right: 1px solid #333333;
}

QFrame#libraryFrame {
    background-color: #262626; /* Neutral 800 */
}

QFrame#playerBarFrame {
    background-color: #171717; /* Neutral 900 */
    border-top: 1px solid #333333;
    min-height: 76px;
}

/* ============ Table / Song Grid ============ */
QTableWidget {
    background-color: #262626; /* Neutral 800 */
    border: none;
    gridline-color: transparent;
    outline: 0;
    font-size: 13px;
}

QTableWidget::item {
    background-color: transparent;
    color: #D1D5DB; /* Gray 300 */
    padding: 8px 12px;
    border-bottom: 1px solid rgba(82, 82, 82, 0.4); /* Neutral 700 with opacity */
}

QTableWidget::item:hover {
    background-color: rgba(99, 102, 241, 0.12); /* Subtle indigo highlight */
    color: #F9FAFB; /* Gray 50 */
}

QTableWidget::item:selected {
    background-color: rgba(99, 102, 241, 0.22);
    color: #FFFFFF;
}

/* Table Header */
QHeaderView::section {
    background-color: #262626; /* Neutral 800 */
    color: #9CA3AF; /* Gray 400 */
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid #333333;
    font-weight: 600;
    font-size: 11px;
}

/* ============ Inputs ============ */
QLineEdit {
    background-color: #1F1F1F;
    border: 1px solid #404040;
    border-radius: 8px;
    padding: 8px 14px;
    color: #F3F4F6;
    font-size: 13px;
    selection-background-color: #6366F1;
}

QLineEdit:focus {
    border: 1px solid #6366F1;
}

QLineEdit::placeholder {
    color: #737373;
}

/* ============ Buttons ============ */
QPushButton {
    background-color: #2D2D2D;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 6px 14px;
    color: #F3F4F6;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3F3F3F;
    border-color: #525252;
}

QPushButton:pressed {
    background-color: #1F1F1F;
}

/* Transport Control Buttons */
QPushButton#controlButton {
    background-color: transparent;
    border: none;
    min-width: 36px;
    min-height: 36px;
    max-width: 36px;
    max-height: 36px;
    border-radius: 18px;
    font-size: 12px;
    color: #D1D5DB;
}

QPushButton#controlButton:hover {
    background-color: rgba(99, 102, 241, 0.12);
    color: #F9FAFB;
}

QPushButton#controlButton:checked {
    background-color: rgba(99, 102, 241, 0.18);
    color: #818CF8;
}

/* Primary Play Button */
QPushButton#primaryPlayButton {
    background-color: #6366F1;
    color: #FFFFFF;
    border: none;
    border-radius: 20px;
    min-width: 40px;
    min-height: 40px;
    max-width: 40px;
    max-height: 40px;
    font-size: 14px;
}

QPushButton#primaryPlayButton:hover {
    background-color: #4F46E5;
}

QPushButton#primaryPlayButton:pressed {
    background-color: #3730A3;
}

QPushButton#primaryPlayButton:disabled {
    background-color: #2D2D2D;
    color: #525252;
}

/* Volume Mute Button */
QPushButton#volumeMuteButton {
    background-color: transparent;
    border: none;
    min-width: 30px;
    min-height: 30px;
    max-width: 30px;
    max-height: 30px;
}

/* ============ Sidebar Nav ============ */
QPushButton#sidebarNavBtn {
    background-color: transparent;
    border: none;
    text-align: left;
    padding: 10px 14px;
    border-radius: 8px;
    color: #D1D5DB; /* Gray 300 */
    font-size: 13px;
    font-weight: 400;
}

QPushButton#sidebarNavBtn:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: #F9FAFB;
}

QPushButton#sidebarNavBtn:checked {
    background-color: rgba(99, 102, 241, 0.14);
    color: #FFFFFF;
    font-weight: 600;
}

/* ============ Tab Pills ============ */
QPushButton#tabPill {
    background-color: #1F1F1F;
    border: 1px solid #404040;
    border-radius: 14px;
    padding: 6px 16px;
    color: #D1D5DB; /* Gray 300 */
    font-weight: 500;
    font-size: 12px;
}

QPushButton#tabPill:hover {
    background-color: #2D2D2D;
    color: #F9FAFB;
    border-color: #525252;
}

QPushButton#tabPill:checked {
    background-color: #6366F1;
    border-color: #6366F1;
    color: #FFFFFF;
}

/* ============ Scrollbars ============ */
QScrollBar:vertical {
    border: none;
    background-color: transparent;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #404040;
    min-height: 20px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6366F1;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* ============ Sliders ============ */
QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background-color: #404040;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background-color: #6366F1;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background-color: #E2E8F0;
    border: none;
    width: 10px;
    height: 10px;
    margin: -3px 0;
    border-radius: 5px;
}

QSlider::handle:horizontal:hover {
    background-color: #A5B4FC;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}

/* ============ Labels ============ */
QLabel#songTitleLabel {
    color: #F9FAFB;
    font-size: 17px;
    font-weight: 700;
}

QLabel#songArtistLabel {
    color: #9CA3AF;
    font-size: 14px;
}

QLabel#timeElapsedLabel, QLabel#timeTotalLabel {
    color: #9CA3AF;
    font-size: 11px;
    font-family: 'Consolas', 'Segoe UI', monospace;
}

/* ============ Status Bar ============ */
QStatusBar {
    background-color: #171717; /* Neutral 900 */
    color: #8E8E93;
    font-size: 11px;
    border-top: 1px solid #333333;
    padding: 2px 8px;
}

/* ============ Splitter ============ */
QSplitter::handle {
    background-color: transparent;
    width: 1px;
}

/* Custom styling for labels inside sidebar buttons to prevent inheritance bugs */
QPushButton#sidebarNavBtn QLabel {
    color: #D1D5DB; /* Gray 300 */
}

QPushButton#sidebarNavBtn:hover QLabel {
    color: #F9FAFB; /* Gray 50 */
}

QPushButton#sidebarNavBtn:checked QLabel {
    color: #FFFFFF;
    font-weight: 600;
}

QPushButton#sidebarNavBtn:disabled QLabel {
    color: #475569; /* Gray 600 */
}

QLabel#sidebarHeader {
    color: #475569;
    font-weight: bold;
    font-size: 10px;
    margin-top: 10px;
    margin-left: 6px;
}

QLabel#sidebarVersion {
    color: #475569;
    font-size: 10px;
    margin-left: 6px;
}

/* ============ Now Playing Panel (Right Sidebar) ============ */
QFrame#nowPlayingFrame {
    background-color: #171717; /* Neutral 900 */
    border-left: 1px solid #333333;
}
"""

