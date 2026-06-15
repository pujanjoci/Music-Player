from typing import Optional, List
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox
from PySide6.QtCore import Qt

class EditMetadataDialog(QDialog):
    """
    Dialog window for renaming songs and changing artist/album/genre metadata.
    """
    def __init__(self, title: str, artist: str, album: str, genre: str, existing_genres: List[str], parent: Optional[QDialog] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Metadata")
        self.resize(400, 330)
        self.setModal(True)
        self._init_ui(title, artist, album, genre, existing_genres)

    def _init_ui(self, title: str, artist: str, album: str, genre: str, existing_genres: List[str]) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title Input
        lbl_title = QLabel("Song Title:", self)
        lbl_title.setStyleSheet("font-weight: bold; color: #CBD5E1;")
        self.edit_title = QLineEdit(self)
        self.edit_title.setText(title)
        self.edit_title.setPlaceholderText("Enter song title...")
        layout.addWidget(lbl_title)
        layout.addWidget(self.edit_title)

        # Artist Input
        lbl_artist = QLabel("Artist Name:", self)
        lbl_artist.setStyleSheet("font-weight: bold; color: #CBD5E1;")
        self.edit_artist = QLineEdit(self)
        self.edit_artist.setText(artist)
        self.edit_artist.setPlaceholderText("Enter artist name...")
        layout.addWidget(lbl_artist)
        layout.addWidget(self.edit_artist)

        # Album Input
        lbl_album = QLabel("Album Name:", self)
        lbl_album.setStyleSheet("font-weight: bold; color: #CBD5E1;")
        self.edit_album = QLineEdit(self)
        self.edit_album.setText(album)
        self.edit_album.setPlaceholderText("Enter album name...")
        layout.addWidget(lbl_album)
        layout.addWidget(self.edit_album)

        # Genre Input (Editable ComboBox)
        lbl_genre = QLabel("Genre:", self)
        lbl_genre.setStyleSheet("font-weight: bold; color: #CBD5E1;")
        self.edit_genre = QComboBox(self)
        self.edit_genre.setEditable(True)
        self.edit_genre.addItems(existing_genres)
        self.edit_genre.setCurrentText(genre or "")
        self.edit_genre.setPlaceholderText("Select or type genre...")
        layout.addWidget(lbl_genre)
        layout.addWidget(self.edit_genre)

        # Spacer
        layout.addSpacing(10)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Save", self)
        self.btn_save.setObjectName("primaryPlayButton")
        self.btn_save.setStyleSheet("""
            QPushButton#primaryPlayButton {
                background-color: #6366F1;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 20px;
                font-weight: bold;
            }
            QPushButton#primaryPlayButton:hover {
                background-color: #4F46E5;
            }
            QPushButton#primaryPlayButton:pressed {
                background-color: #3730A3;
            }
        """)
        self.btn_save.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

        # Set styling that aligns with stylesheet.py
        self.setStyleSheet("""
            QDialog {
                background-color: #0A0C12;
                border: 1px solid #1C2030;
            }
            QLineEdit, QComboBox {
                background-color: #131620;
                border: 1px solid #1C2030;
                border-radius: 6px;
                padding: 7px 10px;
                color: #E2E8F0;
                font-size: 13px;
            }
            QComboBox {
                padding-right: 30px;
            }
            QComboBox QLineEdit {
                color: #E2E8F0;
                background: transparent;
                border: none;
                padding: 0px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #6366F1;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border: none;
                background-color: transparent;
            }
            QComboBox::down-arrow {
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #CBD5E1;
                width: 0px;
                height: 0px;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #6366F1;
            }
            QComboBox QAbstractItemView {
                background-color: #10121B;
                color: #CBD5E1;
                border: 1px solid #1C2030;
                selection-background-color: #6366F1;
            }
            QPushButton {
                background-color: #1A1E2E;
                border: 1px solid #252A3A;
                border-radius: 6px;
                padding: 6px 14px;
                color: #E2E8F0;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #252A3A;
                border-color: #334155;
            }
        """)

    def get_data(self) -> tuple[str, str, str, str]:
        return (
            self.edit_title.text().strip(),
            self.edit_artist.text().strip(),
            self.edit_album.text().strip(),
            self.edit_genre.currentText().strip()
        )
