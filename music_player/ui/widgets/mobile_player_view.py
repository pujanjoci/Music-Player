import os
import logging
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QSlider, QStackedWidget, QListWidget, QListWidgetItem, QLineEdit, QFrame
)
from PySide6.QtCore import Signal, Slot, Qt, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QLinearGradient, QBrush, QIcon
from PySide6.QtMultimedia import QMediaPlayer

from music_player.models.song import Song
from music_player.player.play_queue import RepeatMode
from music_player.ui.utils import create_vector_icon, round_pixmap, get_track_placeholder_art
from music_player.database.repository import MusicRepository

logger = logging.getLogger(__name__)

class ClickableSlider(QSlider):
    """Mobile-friendly seek slider with direct click support."""
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            val = self.minimum() + ((self.maximum() - self.minimum()) * event.position().x()) / self.width()
            self.setValue(int(val))
            self.sliderPressed.emit()
            self.sliderMoved.emit(self.value())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButtons.LeftButton:
            val = self.minimum() + ((self.maximum() - self.minimum()) * event.position().x()) / self.width()
            self.setValue(int(val))
            self.sliderMoved.emit(self.value())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.sliderReleased.emit()
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class SongListWidgetItem(QWidget):
    """Custom widget for mobile track list items."""
    def __init__(self, song: Song, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.song = song
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        # Small artwork
        self.art_label = QLabel(self)
        self.art_label.setFixedSize(36, 36)
        self.art_label.setScaledContents(True)
        self.art_label.setPixmap(get_track_placeholder_art(self.song.title, 36))
        layout.addWidget(self.art_label)

        # Text labels (title & artist)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel(self.song.display_title, self)
        self.title_label.setStyleSheet("font-weight: 600; color: #F3F4F6; font-size: 13px;")
        self.title_label.setWordWrap(False)
        
        self.artist_label = QLabel(self.song.artist, self)
        self.artist_label.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        self.artist_label.setWordWrap(False)
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.artist_label)
        layout.addLayout(text_layout)
        layout.addStretch(1)

        # Duration
        dur_label = QLabel(self._format_duration(self.song.duration), self)
        dur_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        layout.addWidget(dur_label)

    def _format_duration(self, seconds: float) -> str:
        s = int(seconds % 60)
        m = int((seconds // 60) % 60)
        return f"{m:02d}:{s:02d}"


class MobilePlayerView(QWidget):
    """
    Mobile-optimized player component for portrait/narrow layouts.
    Includes a beautiful Player Screen and an integrated Library List.
    """
    play_clicked = Signal()
    pause_clicked = Signal()
    prev_clicked = Signal()
    next_clicked = Signal()
    seek_requested = Signal(int)
    repeat_toggled = Signal(RepeatMode)
    favorite_toggled = Signal(bool)
    song_selected = Signal(Song, int)  # Emits (song, index) from mobile library list
    edit_song_requested = Signal(Song)
    delete_song_requested = Signal(Song)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._is_sliding = False
        self._is_playing = False
        self._duration_ms = 0
        self._current_repeat = RepeatMode.OFF
        self._all_songs: List[Song] = []
        self._current_song: Optional[Song] = None
        self._current_artwork: Optional[QPixmap] = None

        self._init_ui()

    def _init_ui(self) -> None:
        # Stacked Layout
        self.stack = QStackedWidget(self)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.stack)

        # 1. Player Screen Page
        self.player_page = QWidget(self)
        self._setup_player_page()
        self.stack.addWidget(self.player_page)

        # 2. Library Screen Page
        self.library_page = QWidget(self)
        self._setup_library_page()
        self.stack.addWidget(self.library_page)

        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            /* Custom seek slider styled for mobile */
            QSlider::groove:horizontal {
                border: none;
                height: 5px;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #F43F5E, stop:1 #8B5CF6);
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background-color: #FFFFFF;
                border: none;
                width: 12px;
                height: 12px;
                margin: -3px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            /* Circular play button with glow gradient */
            QPushButton#mobilePlayButton {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #EF4444, stop:1 #6366F1);
                border: none;
                border-radius: 26px;
                min-width: 52px;
                min-height: 52px;
                max-width: 52px;
                max-height: 52px;
            }
            QPushButton#mobilePlayButton:hover {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #F87171, stop:1 #818CF8);
            }
            QPushButton#mobilePlayButton:pressed {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #DC2626, stop:1 #4F46E5);
            }
            /* Mobile control bar background */
            QFrame#mobilePlayerBg {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #1F1F2E, stop:1 #111116);
            }
        """)

    def _setup_player_page(self) -> None:
        layout = QVBoxLayout(self.player_page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        # Background wrapping frame for premium mobile gradient look
        bg_frame = QFrame(self.player_page)
        bg_frame.setObjectName("mobilePlayerBg")
        bg_layout = QVBoxLayout(bg_frame)
        bg_layout.setContentsMargins(16, 20, 16, 20)
        bg_layout.setSpacing(16)

        # --- Row 1: Header ---
        header_layout = QHBoxLayout()
        self.btn_back = QPushButton(bg_frame)
        self.btn_back.setIcon(create_vector_icon("back", "#F3F4F6", 24))
        self.btn_back.setFixedSize(36, 36)
        self.btn_back.setStyleSheet("background: transparent; border: none; border-radius: 18px;")
        self.btn_back.clicked.connect(self._on_back_clicked)
        header_layout.addWidget(self.btn_back)

        header_title = QLabel("NOW PLAYING", bg_frame)
        header_title.setStyleSheet("color: #9CA3AF; font-weight: 700; font-size: 11px; letter-spacing: 2px;")
        header_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(header_title, 1)

        # Menu/Options button
        self.btn_more = QPushButton(bg_frame)
        self.btn_more.setText("•••")
        self.btn_more.setStyleSheet("background: transparent; border: none; color: #F3F4F6; font-size: 16px; font-weight: bold;")
        self.btn_more.setFixedSize(36, 36)
        self.btn_more.clicked.connect(self._show_options_menu)
        header_layout.addWidget(self.btn_more)

        bg_layout.addLayout(header_layout)

        # --- Row 2: Large Album Art ---
        self.artwork_container = QWidget(bg_frame)
        art_layout = QVBoxLayout(self.artwork_container)
        art_layout.setContentsMargins(0, 10, 0, 10)
        art_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.artwork_label = QLabel(self.artwork_container)
        self.artwork_label.setFixedSize(260, 260)
        self.artwork_label.setScaledContents(True)
        self.artwork_label.setStyleSheet("""
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            background-color: #121214;
        """)
        self.artwork_label.setPixmap(self._generate_placeholder_artwork(260))
        art_layout.addWidget(self.artwork_label)
        bg_layout.addWidget(self.artwork_container)

        # --- Row 3: Song details ---
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setContentsMargins(0, 4, 0, 4)
        
        self.title_label = QLabel("Not Playing", bg_frame)
        self.title_label.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        text_layout.addWidget(self.title_label)

        self.artist_label = QLabel("", bg_frame)
        self.artist_label.setStyleSheet("color: #9CA3AF; font-size: 14px;")
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artist_label.setWordWrap(True)
        text_layout.addWidget(self.artist_label)

        bg_layout.addLayout(text_layout)

        # --- Row 4: Progress Bar ---
        progress_container = QWidget(bg_frame)
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(4)

        self.seek_slider = ClickableSlider(Qt.Orientation.Horizontal, progress_container)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderPressed.connect(self._on_slider_pressed)
        self.seek_slider.sliderReleased.connect(self._on_slider_released)
        self.seek_slider.sliderMoved.connect(self._on_slider_moved)
        progress_layout.addWidget(self.seek_slider)

        time_labels_layout = QHBoxLayout()
        self.time_elapsed = QLabel("00:00", progress_container)
        self.time_elapsed.setStyleSheet("color: #9CA3AF; font-size: 10px; font-family: monospace;")
        self.time_total = QLabel("00:00", progress_container)
        self.time_total.setStyleSheet("color: #9CA3AF; font-size: 10px; font-family: monospace;")
        
        time_labels_layout.addWidget(self.time_elapsed)
        time_labels_layout.addStretch(1)
        time_labels_layout.addWidget(self.time_total)
        progress_layout.addLayout(time_labels_layout)

        bg_layout.addWidget(progress_container)

        # --- Row 5: Controls ---
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(18)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Repeat
        self.btn_repeat = QPushButton(bg_frame)
        self.btn_repeat.setIcon(create_vector_icon("repeat", extra=0, size=20))
        self.btn_repeat.setFixedSize(36, 36)
        self.btn_repeat.setStyleSheet("background: transparent; border: none; border-radius: 18px;")
        self.btn_repeat.clicked.connect(self._on_repeat_clicked)
        controls_layout.addWidget(self.btn_repeat)

        # Previous
        self.btn_prev = QPushButton(bg_frame)
        self.btn_prev.setIcon(create_vector_icon("prev", "#FFFFFF", size=22))
        self.btn_prev.setFixedSize(36, 36)
        self.btn_prev.setStyleSheet("background: transparent; border: none; border-radius: 18px;")
        self.btn_prev.clicked.connect(self.prev_clicked)
        controls_layout.addWidget(self.btn_prev)

        # Play/Pause
        self.btn_play_pause = QPushButton(bg_frame)
        self.btn_play_pause.setObjectName("mobilePlayButton")
        self.btn_play_pause.setIcon(create_vector_icon("play", "#FFFFFF", size=24))
        self.btn_play_pause.clicked.connect(self._on_play_pause_clicked)
        controls_layout.addWidget(self.btn_play_pause)

        # Next
        self.btn_next = QPushButton(bg_frame)
        self.btn_next.setIcon(create_vector_icon("next", "#FFFFFF", size=22))
        self.btn_next.setFixedSize(36, 36)
        self.btn_next.setStyleSheet("background: transparent; border: none; border-radius: 18px;")
        self.btn_next.clicked.connect(self.next_clicked)
        controls_layout.addWidget(self.btn_next)

        # Favorite
        self.btn_favorite = QPushButton(bg_frame)
        self.btn_favorite.setCheckable(True)
        self.btn_favorite.setIcon(create_vector_icon("heart_outline", "#9CA3AF", 20))
        self.btn_favorite.setFixedSize(36, 36)
        self.btn_favorite.setStyleSheet("background: transparent; border: none; border-radius: 18px;")
        self.btn_favorite.clicked.connect(self._on_favorite_clicked)
        self.btn_favorite.setEnabled(False)
        controls_layout.addWidget(self.btn_favorite)

        bg_layout.addLayout(controls_layout)

        # Add gradient frame to main page
        layout.addWidget(bg_frame)

    def _setup_library_page(self) -> None:
        layout = QVBoxLayout(self.library_page)
        layout.setContentsMargins(15, 20, 15, 10)
        layout.setSpacing(12)

        # Search header
        header_lbl = QLabel("Library", self.library_page)
        header_lbl.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold;")
        layout.addWidget(header_lbl)

        self.search_bar = QLineEdit(self.library_page)
        self.search_bar.setPlaceholderText("Search tracks, artists...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #1F1F24;
                border: 1px solid #32323D;
                border-radius: 8px;
                padding: 8px 12px;
                color: #FFFFFF;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #6366F1;
            }
        """)
        self.search_bar.textChanged.connect(self._on_search_text_changed)
        layout.addWidget(self.search_bar)

        # QListWidget
        self.list_widget = QListWidget(self.library_page)
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: none;
            }
            QListWidget::item {
                background-color: #1A1A1E;
                border: 1px solid #23232A;
                border-radius: 8px;
                padding: 2px;
                margin-bottom: 6px;
            }
            QListWidget::item:hover {
                background-color: #24242B;
            }
            QListWidget::item:selected {
                background-color: rgba(99, 102, 241, 0.15);
                border: 1px solid #6366F1;
            }
        """)
        self.list_widget.itemDoubleClicked.connect(self._on_list_item_double_clicked)
        layout.addWidget(self.list_widget)

        # Bottom Mini Player Bar
        self.mini_bar = QFrame(self.library_page)
        self.mini_bar.setObjectName("miniPlayerBar")
        self.mini_bar.setFixedHeight(54)
        self.mini_bar.setStyleSheet("""
            QFrame#miniPlayerBar {
                background-color: #1B1B22;
                border: 1px solid #2D2D35;
                border-radius: 8px;
            }
        """)
        
        mini_layout = QHBoxLayout(self.mini_bar)
        mini_layout.setContentsMargins(8, 6, 8, 6)
        mini_layout.setSpacing(10)

        self.mini_art = QLabel(self.mini_bar)
        self.mini_art.setFixedSize(36, 36)
        self.mini_art.setScaledContents(True)
        self.mini_art.setStyleSheet("border-radius: 4px;")
        self.mini_art.setPixmap(self._generate_placeholder_artwork(36))
        mini_layout.addWidget(self.mini_art)

        mini_text_layout = QVBoxLayout()
        mini_text_layout.setSpacing(1)
        mini_text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.lbl_mini_title = QLabel("Not Playing", self.mini_bar)
        self.lbl_mini_title.setStyleSheet("font-weight: 600; color: #FFFFFF; font-size: 12px;")
        self.lbl_mini_artist = QLabel("", self.mini_bar)
        self.lbl_mini_artist.setStyleSheet("color: #9CA3AF; font-size: 10px;")
        
        mini_text_layout.addWidget(self.lbl_mini_title)
        mini_text_layout.addWidget(self.lbl_mini_artist)
        mini_layout.addLayout(mini_text_layout)
        mini_layout.addStretch(1)

        # Mini play/pause
        self.btn_mini_play_pause = QPushButton(self.mini_bar)
        self.btn_mini_play_pause.setFixedSize(32, 32)
        self.btn_mini_play_pause.setIcon(create_vector_icon("play", "#FFFFFF", 16))
        self.btn_mini_play_pause.setStyleSheet("background: transparent; border: none;")
        self.btn_mini_play_pause.clicked.connect(self._on_play_pause_clicked)
        mini_layout.addWidget(self.btn_mini_play_pause)

        # Mini next
        self.btn_mini_next = QPushButton(self.mini_bar)
        self.btn_mini_next.setFixedSize(32, 32)
        self.btn_mini_next.setIcon(create_vector_icon("next", "#FFFFFF", 16))
        self.btn_mini_next.setStyleSheet("background: transparent; border: none;")
        self.btn_mini_next.clicked.connect(self.next_clicked)
        mini_layout.addWidget(self.btn_mini_next)

        # Make the mini bar clickable to open the player page
        self.mini_bar.mousePressEvent = self._on_mini_bar_clicked

        layout.addWidget(self.mini_bar)

    # --- Interaction Slots ---

    def _on_back_clicked(self) -> None:
        """Switch to Library list page."""
        self.stack.setCurrentIndex(1)

    def _on_mini_bar_clicked(self, event) -> None:
        """Switch to Full Player screen page."""
        self.stack.setCurrentIndex(0)

    def _on_play_pause_clicked(self) -> None:
        if self._is_playing:
            self.pause_clicked.emit()
        else:
            self.play_clicked.emit()

    def _on_favorite_clicked(self) -> None:
        is_checked = self.btn_favorite.isChecked()
        if is_checked:
            self.btn_favorite.setIcon(create_vector_icon("heart_filled", "#EF4444", 20))
        else:
            self.btn_favorite.setIcon(create_vector_icon("heart_outline", "#9CA3AF", 20))
        self.favorite_toggled.emit(is_checked)

    def _on_repeat_clicked(self) -> None:
        """Cycles through repeat modes: Off -> All -> One -> Off."""
        if self._current_repeat == RepeatMode.OFF:
            self._current_repeat = RepeatMode.ALL
        elif self._current_repeat == RepeatMode.ALL:
            self._current_repeat = RepeatMode.ONE
        else:
            self._current_repeat = RepeatMode.OFF

        self.btn_repeat.setIcon(create_vector_icon("repeat", extra=self._current_repeat.value, size=20))
        self.btn_repeat.setToolTip(f"Repeat: {self._current_repeat.name.capitalize()}")
        self.repeat_toggled.emit(self._current_repeat)

    def _on_slider_pressed(self) -> None:
        self._is_sliding = True

    def _on_slider_released(self) -> None:
        self._is_sliding = False
        self.seek_requested.emit(self.seek_slider.value())

    def _on_slider_moved(self, value: int) -> None:
        self.time_elapsed.setText(self._format_time(value))

    def _on_list_item_double_clicked(self, item: QListWidgetItem) -> None:
        song = item.data(Qt.ItemDataRole.UserRole)
        # Find index in full filtered list
        idx = self.list_widget.row(item)
        
        # We need to map it to the actual index in self._all_songs or emit the song
        # Let's find index in the original _all_songs list
        orig_idx = 0
        for i, s in enumerate(self._all_songs):
            if s.filepath == song.filepath:
                orig_idx = i
                break
        
        self.song_selected.emit(song, orig_idx)
        # Go back to player screen
        self.stack.setCurrentIndex(0)

    def _on_search_text_changed(self, text: str) -> None:
        self.filter_song_list(text)

    # --- Public View Sync API ---

    def set_songs(self, songs: List[Song]) -> None:
        """Updates the track list in the mobile view."""
        self._all_songs = list(songs)
        self.filter_song_list(self.search_bar.text())

    def filter_song_list(self, filter_text: str) -> None:
        self.list_widget.clear()
        query = filter_text.strip().lower()
        for song in self._all_songs:
            if not query or query in song.title.lower() or query in song.artist.lower():
                item = QListWidgetItem(self.list_widget)
                custom_widget = SongListWidgetItem(song, self)
                item.setSizeHint(custom_widget.sizeHint())
                item.setData(Qt.ItemDataRole.UserRole, song)
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, custom_widget)

    def set_active_song(self, song: Optional[Song], artwork_pixmap: Optional[QPixmap] = None) -> None:
        """Sets the currently active playing track, updating both Player Page and Mini Bar."""
        self._current_song = song
        self._current_artwork = artwork_pixmap

        if song:
            # Player Page
            self.title_label.setText(song.display_title)
            self.artist_label.setText(song.artist or "Unknown Artist")
            self.btn_favorite.setEnabled(True)
            self.btn_favorite.setChecked(song.favorite)
            if song.favorite:
                self.btn_favorite.setIcon(create_vector_icon("heart_filled", "#EF4444", 20))
            else:
                self.btn_favorite.setIcon(create_vector_icon("heart_outline", "#9CA3AF", 20))

            # Mini Bar
            self.lbl_mini_title.setText(song.display_title)
            self.lbl_mini_artist.setText(song.artist or "Unknown Artist")

            # Artwork
            if artwork_pixmap and not artwork_pixmap.isNull():
                self.artwork_label.setPixmap(round_pixmap(artwork_pixmap, 14))
                self.mini_art.setPixmap(round_pixmap(artwork_pixmap, 4))
            else:
                self.artwork_label.setPixmap(self._generate_placeholder_artwork(260))
                self.mini_art.setPixmap(self._generate_placeholder_artwork(36))
        else:
            self.title_label.setText("Not Playing")
            self.artist_label.setText("")
            self.btn_favorite.setChecked(False)
            self.btn_favorite.setIcon(create_vector_icon("heart_outline", "#9CA3AF", 20))
            self.btn_favorite.setEnabled(False)

            self.lbl_mini_title.setText("Not Playing")
            self.lbl_mini_artist.setText("")

            self.artwork_label.setPixmap(self._generate_placeholder_artwork(260))
            self.mini_art.setPixmap(self._generate_placeholder_artwork(36))

    def set_playback_state(self, state: QMediaPlayer.PlaybackState) -> None:
        """Updates play/pause icons in both player screen and mini bar."""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._is_playing = True
            self.btn_play_pause.setIcon(create_vector_icon("pause", "#FFFFFF", 24))
            self.btn_mini_play_pause.setIcon(create_vector_icon("pause", "#FFFFFF", 16))
        else:
            self._is_playing = False
            self.btn_play_pause.setIcon(create_vector_icon("play", "#FFFFFF", 24))
            self.btn_mini_play_pause.setIcon(create_vector_icon("play", "#FFFFFF", 16))

    def update_position(self, position_ms: int) -> None:
        if not self._is_sliding and self._duration_ms > 0:
            self.seek_slider.setValue(position_ms)
            self.time_elapsed.setText(self._format_time(position_ms))

    def update_duration(self, duration_ms: int) -> None:
        if duration_ms <= 0:
            return
        self._duration_ms = duration_ms
        self.seek_slider.setRange(0, duration_ms)
        self.time_total.setText(self._format_time(duration_ms))

    def set_repeat_mode(self, mode: RepeatMode) -> None:
        self._current_repeat = mode
        self.btn_repeat.setIcon(create_vector_icon("repeat", extra=mode.value, size=20))
        self.btn_repeat.setToolTip(f"Repeat: {mode.name.capitalize()}")

    def _show_options_menu(self) -> None:
        """Shows options menu (Edit metadata, Delete) for currently playing song."""
        if not self._current_song:
            return

        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #10121B;
                color: #CBD5E1;
                border: 1px solid #1C2030;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #6366F1;
                color: #FFFFFF;
            }
        """)

        edit_action = QAction("Edit Metadata...", self)
        edit_action.triggered.connect(lambda: self.edit_song_requested.emit(self._current_song))
        menu.addAction(edit_action)

        delete_action = QAction("Delete Song...", self)
        delete_action.triggered.connect(lambda: self.delete_song_requested.emit(self._current_song))
        menu.addAction(delete_action)

        menu.exec(self.btn_more.mapToGlobal(self.btn_more.rect().bottomLeft()))

    # --- Utility Methods ---

    def _format_time(self, ms: int) -> str:
        seconds = int((ms // 1000) % 60)
        minutes = int((ms // (1000 * 60)) % 60)
        hours = int(ms // (1000 * 60 * 60))
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def _generate_placeholder_artwork(self, size: int) -> QPixmap:
        """Generates a premium look music note placeholder artwork using a modern gradient."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw soft gradient background
        gradient = QLinearGradient(0, 0, size, size)
        gradient.setColorAt(0.0, QColor("#1E1B4B"))  # Deep indigo
        gradient.setColorAt(1.0, QColor("#311042"))  # Deep purple/magenta
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, size, size, 14 if size > 100 else 4, 14 if size > 100 else 4)
        
        # Draw central note logo
        font = painter.font()
        font.setPointSize(int(size * 0.3))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#818CF8"))  # Light indigo
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "♪")
        
        painter.end()
        return pixmap
