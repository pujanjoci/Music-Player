import logging
from typing import Optional
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QPainter, QColor, QLinearGradient, QBrush
from music_player.models.song import Song
from music_player.ui.utils import create_vector_icon, round_pixmap

logger = logging.getLogger(__name__)


class NowPlayingPanel(QFrame):
    """
    Right sidebar panel displaying detail view of the currently playing song:
    Artwork, Title, Artist, Album, Genre, and a prominent Like (favorite) button.
    """
    favorite_toggled = Signal(bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("nowPlayingFrame")
        self.setFixedWidth(250)
        self._init_ui()

    def _init_ui(self) -> None:
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 20, 16, 20)
        self.layout.setSpacing(16)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header Label "NOW PLAYING"
        self.header_label = QLabel("NOW PLAYING", self)
        self.header_label.setObjectName("nowPlayingHeader")
        self.header_label.setStyleSheet("""
            color: #475569; /* Gray 600 */
            font-weight: bold;
            font-size: 10px;
            letter-spacing: 1px;
        """)
        self.layout.addWidget(self.header_label)

        # Large Artwork
        self.artwork_label = QLabel(self)
        self.artwork_label.setFixedSize(218, 218)
        self.artwork_label.setScaledContents(True)
        self.artwork_label.setStyleSheet("""
            border: 1px solid #333333;
            border-radius: 8px;
            background-color: #1F1F1F;
        """)
        self.artwork_label.setPixmap(self._generate_placeholder_artwork())
        self.layout.addWidget(self.artwork_label)

        # Title & Artist Text Layout
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        # Song Title
        self.title_label = QLabel("Not Playing", self)
        self.title_label.setObjectName("nowPlayingTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("""
            color: #F8FAFC;
            font-size: 15px;
            font-weight: bold;
        """)
        text_layout.addWidget(self.title_label)

        # Artist
        self.artist_label = QLabel("", self)
        self.artist_label.setObjectName("nowPlayingArtist")
        self.artist_label.setWordWrap(True)
        self.artist_label.setStyleSheet("""
            color: #94A3B8;
            font-size: 13px;
        """)
        text_layout.addWidget(self.artist_label)
        
        self.layout.addLayout(text_layout)

        # Extra Metadata Layout (Album, Genre)
        self.metadata_widget = QWidget(self)
        metadata_layout = QVBoxLayout(self.metadata_widget)
        metadata_layout.setContentsMargins(0, 4, 0, 4)
        metadata_layout.setSpacing(6)

        # Album
        self.album_row = QHBoxLayout()
        self.album_icon = QLabel(self.metadata_widget)
        self.album_icon.setPixmap(create_vector_icon("cd", "#475569", 14).pixmap(14, 14))
        self.album_label = QLabel("", self.metadata_widget)
        self.album_label.setStyleSheet("color: #64748B; font-size: 11px;")
        self.album_label.setWordWrap(True)
        self.album_row.addWidget(self.album_icon)
        self.album_row.addWidget(self.album_label)
        self.album_row.addStretch()
        metadata_layout.addLayout(self.album_row)

        # Genre
        self.genre_row = QHBoxLayout()
        self.genre_icon = QLabel(self.metadata_widget)
        self.genre_icon.setPixmap(create_vector_icon("genre", "#475569", 14).pixmap(14, 14))
        self.genre_label = QLabel("", self.metadata_widget)
        self.genre_label.setStyleSheet("color: #64748B; font-size: 11px;")
        self.genre_label.setWordWrap(True)
        self.genre_row.addWidget(self.genre_icon)
        self.genre_row.addWidget(self.genre_label)
        self.genre_row.addStretch()
        metadata_layout.addLayout(self.genre_row)

        self.layout.addWidget(self.metadata_widget)
        self.metadata_widget.setVisible(False)

        # Spacer
        self.layout.addStretch(1)

        # Control Row (Favorite Button at the bottom center)
        control_row = QHBoxLayout()
        control_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_favorite = QPushButton(self)
        self.btn_favorite.setObjectName("nowPlayingFavoriteButton")
        self.btn_favorite.setCheckable(True)
        self.btn_favorite.setFixedSize(44, 44)
        self.btn_favorite.setIcon(create_vector_icon("heart_outline", "#94A3B8", 22))
        self.btn_favorite.setStyleSheet("""
            QPushButton#nowPlayingFavoriteButton {
                background-color: #1F1F1F;
                border: 1px solid #333333;
                border-radius: 22px;
                padding: 0px;
            }
            QPushButton#nowPlayingFavoriteButton:hover {
                background-color: rgba(99, 102, 241, 0.08);
                border-color: #6366F1;
            }
            QPushButton#nowPlayingFavoriteButton:checked {
                background-color: rgba(239, 68, 68, 0.1);
                border-color: #EF4444;
            }
        """)
        self.btn_favorite.clicked.connect(self._on_favorite_clicked)
        self.btn_favorite.setEnabled(False)
        control_row.addWidget(self.btn_favorite)

        self.layout.addLayout(control_row)

    def set_active_song(self, song: Optional[Song], artwork_pixmap: Optional[QPixmap] = None) -> None:
        """Updates the now playing detail sidebar views."""
        if song:
            self.title_label.setText(song.display_title)
            self.artist_label.setText(song.artist or "Unknown Artist")
            
            # Show extra metadata
            self.album_label.setText(song.album or "Unknown Album")
            self.genre_label.setText(song.genre or "Unknown Genre")
            self.metadata_widget.setVisible(True)

            if artwork_pixmap and not artwork_pixmap.isNull():
                self.artwork_label.setPixmap(round_pixmap(artwork_pixmap, 8))
            else:
                self.artwork_label.setPixmap(self._generate_placeholder_artwork())

            self.btn_favorite.setEnabled(True)
            self.btn_favorite.setChecked(song.favorite)
            if song.favorite:
                self.btn_favorite.setIcon(create_vector_icon("heart_filled", "#EF4444", 22))
            else:
                self.btn_favorite.setIcon(create_vector_icon("heart_outline", "#94A3B8", 22))
        else:
            self.title_label.setText("Not Playing")
            self.artist_label.setText("")
            self.album_label.setText("")
            self.genre_label.setText("")
            self.metadata_widget.setVisible(False)
            self.artwork_label.setPixmap(self._generate_placeholder_artwork())
            self.btn_favorite.setChecked(False)
            self.btn_favorite.setIcon(create_vector_icon("heart_outline", "#94A3B8", 22))
            self.btn_favorite.setEnabled(False)

    def _on_favorite_clicked(self) -> None:
        is_checked = self.btn_favorite.isChecked()
        if is_checked:
            self.btn_favorite.setIcon(create_vector_icon("heart_filled", "#EF4444", 22))
        else:
            self.btn_favorite.setIcon(create_vector_icon("heart_outline", "#94A3B8", 22))
        self.favorite_toggled.emit(is_checked)

    def _generate_placeholder_artwork(self) -> QPixmap:
        """Generates a premium looking music note placeholder artwork using a modern gradient."""
        pixmap = QPixmap(218, 218)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw soft gradient background
        gradient = QLinearGradient(0, 0, 218, 218)
        gradient.setColorAt(0.0, QColor("#1E1B4B"))  # Deep indigo
        gradient.setColorAt(1.0, QColor("#311042"))  # Deep purple/magenta
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 218, 218, 8, 8)
        
        # Draw central note logo
        font = painter.font()
        font.setPointSize(64)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#818CF8"))  # Light indigo
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "♪")
        
        painter.end()
        return pixmap
