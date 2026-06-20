from typing import Optional
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QSizePolicy, QWidget, QStyle
from PySide6.QtCore import Signal, Qt, QRectF
from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon
from PySide6.QtMultimedia import QMediaPlayer
from music_player.models.song import Song
from music_player.player.play_queue import RepeatMode
from music_player.ui.utils import create_vector_icon, round_pixmap


class ClickableSlider(QSlider):
    """
    Subclass of QSlider to support direct click-to-seek and smooth dragging.
    """
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


class PlayerControls(QFrame):
    """
    Bottom control bar with playback buttons (using premium custom vector icons),
    clickable seek slider, volume, and shuffle/repeat toggles.
    """
    play_clicked = Signal()
    pause_clicked = Signal()
    stop_clicked = Signal()
    prev_clicked = Signal()
    next_clicked = Signal()
    seek_requested = Signal(int)
    volume_changed = Signal(int)
    mute_toggled = Signal(bool)
    shuffle_toggled = Signal(bool)
    repeat_mode_changed = Signal(RepeatMode)
    favorite_toggled = Signal(bool)  # Emitted when mini heart button is toggled

    def __init__(self, parent: Optional[QFrame] = None) -> None:
        super().__init__(parent)
        self.setObjectName("playerBarFrame")
        self._is_sliding = False
        self._is_playing = False
        self._duration_ms = 0
        self._current_repeat = RepeatMode.OFF
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 8, 15, 8)
        main_layout.setSpacing(4)

        # --- Row 1: Progress Bar ---
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(10)

        self.time_elapsed = QLabel("00:00", self)
        self.time_elapsed.setObjectName("timeElapsedLabel")
        self.time_elapsed.setFixedWidth(45)
        progress_layout.addWidget(self.time_elapsed)

        self.seek_slider = ClickableSlider(Qt.Orientation.Horizontal, self)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderPressed.connect(self._on_slider_pressed)
        self.seek_slider.sliderReleased.connect(self._on_slider_released)
        self.seek_slider.sliderMoved.connect(self._on_slider_moved)
        progress_layout.addWidget(self.seek_slider)

        self.time_total = QLabel("00:00", self)
        self.time_total.setObjectName("timeTotalLabel")
        self.time_total.setFixedWidth(45)
        progress_layout.addWidget(self.time_total)

        main_layout.addLayout(progress_layout)

        # --- Row 2: Controls ---
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)

        # === Left: Mini Now Playing ===
        self.mini_info_widget = QWidget(self)
        self.mini_info_widget.setFixedWidth(260)  # Expanded slightly to accommodate the heart button
        mini_layout = QHBoxLayout(self.mini_info_widget)
        mini_layout.setContentsMargins(0, 0, 0, 0)
        mini_layout.setSpacing(10)

        self.mini_art = QLabel(self.mini_info_widget)
        self.mini_art.setFixedSize(40, 40)
        self.mini_art.setScaledContents(True)
        self.mini_art.setStyleSheet("border-radius: 4px;")
        self.mini_art.setPixmap(self._generate_mini_placeholder())
        mini_layout.addWidget(self.mini_art)

        mini_text_layout = QVBoxLayout()
        mini_text_layout.setSpacing(2)
        mini_text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.lbl_mini_title = QLabel("Not Playing", self.mini_info_widget)
        self.lbl_mini_title.setStyleSheet("font-weight: 600; color: #F8FAFC; font-size: 12px;")
        self.lbl_mini_title.setWordWrap(False)
        mini_text_layout.addWidget(self.lbl_mini_title)

        self.lbl_mini_artist = QLabel("", self.mini_info_widget)
        self.lbl_mini_artist.setStyleSheet("color: #64748B; font-size: 11px;")
        self.lbl_mini_artist.setWordWrap(False)
        mini_text_layout.addWidget(self.lbl_mini_artist)

        mini_layout.addLayout(mini_text_layout)

        # Heart button next to the text
        self.btn_mini_favorite = QPushButton(self.mini_info_widget)
        self.btn_mini_favorite.setObjectName("miniFavoriteButton")
        self.btn_mini_favorite.setCheckable(True)
        self.btn_mini_favorite.setFixedSize(24, 24)
        self.btn_mini_favorite.setIcon(create_vector_icon("heart_outline", "#64748B", 16))
        self.btn_mini_favorite.clicked.connect(self._on_mini_favorite_clicked)
        self.btn_mini_favorite.setEnabled(False)
        self.btn_mini_favorite.setStyleSheet("""
            QPushButton#miniFavoriteButton {
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QPushButton#miniFavoriteButton:hover {
                background-color: rgba(99, 102, 241, 0.08);
                border-radius: 12px;
            }
        """)
        mini_layout.addWidget(self.btn_mini_favorite)

        controls_layout.addWidget(self.mini_info_widget)

        # Expanding space
        controls_layout.addStretch(1)

        # === Center: Playback Buttons ===
        center_container = QWidget(self)
        center_layout = QHBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(10)

        # Shuffle button
        self.btn_shuffle = QPushButton(self)
        self.btn_shuffle.setObjectName("controlButton")
        self.btn_shuffle.setIcon(create_vector_icon("shuffle", extra=0, size=20))
        self.btn_shuffle.setToolTip("Shuffle")
        self.btn_shuffle.setCheckable(True)
        self.btn_shuffle.toggled.connect(self._on_shuffle_toggled)
        center_layout.addWidget(self.btn_shuffle)

        # Previous
        self.btn_prev = QPushButton(self)
        self.btn_prev.setObjectName("controlButton")
        self.btn_prev.setIcon(create_vector_icon("prev", size=20))
        self.btn_prev.setToolTip("Previous")
        self.btn_prev.clicked.connect(self.prev_clicked)
        center_layout.addWidget(self.btn_prev)

        # Stop
        self.btn_stop = QPushButton(self)
        self.btn_stop.setObjectName("controlButton")
        self.btn_stop.setIcon(create_vector_icon("stop", size=20))
        self.btn_stop.setToolTip("Stop")
        self.btn_stop.clicked.connect(self.stop_clicked)
        center_layout.addWidget(self.btn_stop)

        # Play / Pause merged button
        self.btn_play_pause = QPushButton(self)
        self.btn_play_pause.setObjectName("primaryPlayButton")
        self.btn_play_pause.setIcon(create_vector_icon("play", "#FFFFFF", size=24))
        self.btn_play_pause.setToolTip("Play")
        self.btn_play_pause.clicked.connect(self._on_play_pause_clicked)
        center_layout.addWidget(self.btn_play_pause)

        # Next
        self.btn_next = QPushButton(self)
        self.btn_next.setObjectName("controlButton")
        self.btn_next.setIcon(create_vector_icon("next", size=20))
        self.btn_next.setToolTip("Next")
        self.btn_next.clicked.connect(self.next_clicked)
        center_layout.addWidget(self.btn_next)

        # Repeat button
        self.btn_repeat = QPushButton(self)
        self.btn_repeat.setObjectName("controlButton")
        self.btn_repeat.setIcon(create_vector_icon("repeat", extra=0, size=20))
        self.btn_repeat.setToolTip("Repeat: Off")
        self.btn_repeat.clicked.connect(self._on_repeat_clicked)
        center_layout.addWidget(self.btn_repeat)

        controls_layout.addWidget(center_container, 0, Qt.AlignmentFlag.AlignCenter)

        # Expanding space
        controls_layout.addStretch(1)

        # === Right: Volume ===
        volume_container = QWidget(self)
        volume_container.setFixedWidth(160)
        volume_layout = QHBoxLayout(volume_container)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(5)

        self.btn_mute = QPushButton(self)
        self.btn_mute.setObjectName("volumeMuteButton")
        self.btn_mute.setIcon(create_vector_icon("volume_medium", size=18))
        self.btn_mute.setCheckable(True)
        self.btn_mute.toggled.connect(self._on_mute_toggled)
        volume_layout.addWidget(self.btn_mute)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal, volume_container)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.volume_changed)
        volume_layout.addWidget(self.volume_slider)

        controls_layout.addWidget(volume_container)

        main_layout.addLayout(controls_layout)

    # --- Public API ---

    def set_active_song(self, song: Optional[Song], artwork_pixmap: Optional[QPixmap] = None) -> None:
        """Updates the mini now-playing layout."""
        if song:
            title = song.display_title
            if len(title) > 22:
                title = title[:20] + "…"
            self.lbl_mini_title.setText(title)

            artist = song.artist
            if len(artist) > 26:
                artist = artist[:24] + "…"
            self.lbl_mini_artist.setText(artist)

            if artwork_pixmap and not artwork_pixmap.isNull():
                self.mini_art.setPixmap(round_pixmap(artwork_pixmap, 4))
            else:
                self.mini_art.setPixmap(self._generate_mini_placeholder())

            self.btn_mini_favorite.setEnabled(True)
            self.btn_mini_favorite.setChecked(song.favorite)
            if song.favorite:
                self.btn_mini_favorite.setIcon(create_vector_icon("heart_filled", "#EF4444", 16))
            else:
                self.btn_mini_favorite.setIcon(create_vector_icon("heart_outline", "#64748B", 16))
        else:
            self.lbl_mini_title.setText("Not Playing")
            self.lbl_mini_artist.setText("")
            self.mini_art.setPixmap(self._generate_mini_placeholder())
            self.btn_mini_favorite.setChecked(False)
            self.btn_mini_favorite.setIcon(create_vector_icon("heart_outline", "#64748B", 16))
            self.btn_mini_favorite.setEnabled(False)

    def _on_mini_favorite_clicked(self) -> None:
        """Emits the new favorite status from bottom bar's heart click."""
        is_checked = self.btn_mini_favorite.isChecked()
        if is_checked:
            self.btn_mini_favorite.setIcon(create_vector_icon("heart_filled", "#EF4444", 16))
        else:
            self.btn_mini_favorite.setIcon(create_vector_icon("heart_outline", "#64748B", 16))
        self.favorite_toggled.emit(is_checked)

    def set_playback_state(self, state: QMediaPlayer.PlaybackState) -> None:
        """Updates play/pause button visual states dynamically."""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._is_playing = True
            self.btn_play_pause.setIcon(create_vector_icon("pause", "#FFFFFF", size=24))
            self.btn_play_pause.setToolTip("Pause")
        else:
            self._is_playing = False
            self.btn_play_pause.setIcon(create_vector_icon("play", "#FFFFFF", size=24))
            self.btn_play_pause.setToolTip("Play")

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

    def set_volume(self, volume: int) -> None:
        self.volume_slider.setValue(volume)
        self._update_volume_icon(volume, self.btn_mute.isChecked())

    def set_repeat_mode(self, mode: RepeatMode) -> None:
        self._current_repeat = mode
        self.btn_repeat.setIcon(create_vector_icon("repeat", extra=mode.value, size=20))
        self.btn_repeat.setToolTip(f"Repeat: {mode.name.capitalize()}")

    # --- Private Handlers ---

    def _on_play_pause_clicked(self) -> None:
        if self._is_playing:
            self.pause_clicked.emit()
        else:
            self.play_clicked.emit()

    def _on_slider_pressed(self) -> None:
        self._is_sliding = True

    def _on_slider_released(self) -> None:
        self._is_sliding = False
        self.seek_requested.emit(self.seek_slider.value())

    def _on_slider_moved(self, value: int) -> None:
        self.time_elapsed.setText(self._format_time(value))

    def _on_mute_toggled(self, checked: bool) -> None:
        if checked:
            self.btn_mute.setIcon(create_vector_icon("volume_mute", size=18))
        else:
            self._update_volume_icon(self.volume_slider.value(), False)
        self.mute_toggled.emit(checked)

    def _on_shuffle_toggled(self, checked: bool) -> None:
        self.btn_shuffle.setIcon(create_vector_icon("shuffle", extra=int(checked), size=20))
        self.btn_shuffle.setToolTip("Shuffle: On" if checked else "Shuffle: Off")
        self.shuffle_toggled.emit(checked)

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
        self.repeat_mode_changed.emit(self._current_repeat)

    def _update_volume_icon(self, volume: int, is_muted: bool) -> None:
        if is_muted or volume == 0:
            self.btn_mute.setIcon(create_vector_icon("volume_mute", size=18))
        elif volume < 33:
            self.btn_mute.setIcon(create_vector_icon("volume_low", size=18))
        elif volume < 66:
            self.btn_mute.setIcon(create_vector_icon("volume_medium", size=18))
        else:
            self.btn_mute.setIcon(create_vector_icon("volume_high", size=18))

    def _generate_mini_placeholder(self) -> QPixmap:
        pixmap = QPixmap(40, 40)
        pixmap.fill(QColor("#1E293B"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor("#475569"))
        font = painter.font()
        font.setPointSize(16)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "♪")
        painter.end()
        return round_pixmap(pixmap, 4)

    def _format_time(self, ms: int) -> str:
        seconds = int((ms // 1000) % 60)
        minutes = int((ms // (1000 * 60)) % 60)
        hours = int(ms // (1000 * 60 * 60))
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
