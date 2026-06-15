import os
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy, QMenu
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction
from music_player.ui.utils import create_vector_icon


class Sidebar(QFrame):
    """
    Redesigned Sidebar navigation widget matching the mockup.
    Includes MENU (Library, Albums, Artists, Genres), FOLDERS (with context menu), and PLAYLISTS.
    """
    add_folder_clicked = Signal()
    library_clicked = Signal()
    albums_clicked = Signal()
    artists_clicked = Signal()
    genres_clicked = Signal()
    folder_clicked = Signal(str)
    remove_folder_requested = Signal(str)
    favorites_clicked = Signal()
    add_playlist_clicked = Signal()
    playlist_clicked = Signal(int)
    remove_playlist_requested = Signal(int)

    def __init__(self, parent: Optional[QFrame] = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebarFrame")
        self.nav_buttons: List[QPushButton] = []
        self._folder_buttons_map: Dict[str, QPushButton] = {}
        self._playlist_buttons_map: Dict[int, QPushButton] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 16, 12, 16)
        self.main_layout.setSpacing(6)

        # --- Premium Logo & Header Layout ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(6, 0, 6, 10)
        header_layout.setSpacing(10)

        # Purple circle icon with white music note
        logo_label = QLabel(self)
        logo_label.setFixedSize(26, 26)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setText("♪")
        logo_label.setStyleSheet("""
            background-color: #6366F1;
            color: #FFFFFF;
            font-size: 15px;
            font-weight: bold;
            border-radius: 13px;
        """)
        header_layout.addWidget(logo_label)

        # Title / Subtitle Text
        title_text_layout = QVBoxLayout()
        title_text_layout.setSpacing(0)
        
        self.title_label = QLabel("LocalPlayer", self)
        self.title_label.setStyleSheet("color: #F8FAFC; font-weight: bold; font-size: 14px;")
        title_text_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("Library", self)
        self.subtitle_label.setStyleSheet("color: #64748B; font-size: 10px;")
        title_text_layout.addWidget(self.subtitle_label)

        header_layout.addLayout(title_text_layout)
        header_layout.addStretch()
        self.main_layout.addLayout(header_layout)

        # --- MENU Section ---
        menu_label = QLabel("MENU", self)
        menu_label.setObjectName("sidebarHeader")
        self.main_layout.addWidget(menu_label)

        # Library Button (with dynamic track count badge)
        self.btn_library = QPushButton(self)
        self.btn_library.setObjectName("sidebarNavBtn")
        self.btn_library.setCheckable(True)
        self.btn_library.setChecked(True)
        self.btn_library.clicked.connect(self.library_clicked)
        self.btn_library.clicked.connect(lambda: self._on_btn_clicked(self.btn_library))
        self.nav_buttons.append(self.btn_library)

        btn_lib_layout = QHBoxLayout(self.btn_library)
        btn_lib_layout.setContentsMargins(8, 0, 8, 0)
        btn_lib_layout.setSpacing(8)

        lib_icon = QLabel(self.btn_library)
        lib_icon.setPixmap(create_vector_icon("cd", "#94A3B8", 18).pixmap(18, 18))
        lib_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        btn_lib_layout.addWidget(lib_icon)

        lib_text = QLabel("Library", self.btn_library)
        lib_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        btn_lib_layout.addWidget(lib_text)
        btn_lib_layout.addStretch()

        self.library_badge = QLabel("0", self.btn_library)
        self.library_badge.setObjectName("badgeLabel")
        self.library_badge.setStyleSheet("""
            background-color: #312E81;
            color: #818CF8;
            font-size: 10px;
            font-weight: bold;
            padding: 1px 6px;
            border-radius: 9px;
        """)
        self.library_badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        btn_lib_layout.addWidget(self.library_badge)

        self.main_layout.addWidget(self.btn_library)

        # Albums Button
        self.btn_albums = self._create_nav_button("cd", "Albums", self.albums_clicked)
        self.main_layout.addWidget(self.btn_albums)

        # Artists Button
        self.btn_artists = self._create_nav_button("artist", "Artists", self.artists_clicked)
        self.main_layout.addWidget(self.btn_artists)

        # Genres Button
        self.btn_genres = self._create_nav_button("genre", "Genres", self.genres_clicked)
        self.main_layout.addWidget(self.btn_genres)

        # --- FOLDERS Section ---
        folders_header = QLabel("FOLDERS", self)
        folders_header.setObjectName("sidebarHeader")
        self.main_layout.addWidget(folders_header)

        # Layout container for dynamic folder items
        self.folders_container = QFrame(self)
        self.folders_layout = QVBoxLayout(self.folders_container)
        self.folders_layout.setContentsMargins(0, 0, 0, 0)
        self.folders_layout.setSpacing(4)
        self.main_layout.addWidget(self.folders_container)

        # Add Folder Button (+ Add Folder) with dashed border style
        self.btn_add_folder = QPushButton("+ Add Folder", self)
        self.btn_add_folder.setObjectName("addFolderBtn")
        self.btn_add_folder.setStyleSheet("""
            QPushButton#addFolderBtn {
                border: 1px dashed #312E81;
                border-radius: 8px;
                padding: 10px 14px;
                color: #818CF8;
                background-color: transparent;
                text-align: center;
                font-weight: 500;
            }
            QPushButton#addFolderBtn:hover {
                background-color: rgba(99, 102, 241, 0.06);
                border-color: #6366F1;
            }
        """)
        self.btn_add_folder.clicked.connect(self.add_folder_clicked)
        self.main_layout.addWidget(self.btn_add_folder)

        # --- PLAYLISTS Section ---
        playlists_header = QLabel("PLAYLISTS", self)
        playlists_header.setObjectName("sidebarHeader")
        self.main_layout.addWidget(playlists_header)

        # Favorites Mix Button
        self.btn_favorites_mix = self._create_nav_button("heart_outline", "Favorites Mix", self.favorites_clicked)
        # Apply standard style modifications for favorites icon
        self.main_layout.addWidget(self.btn_favorites_mix)

        # Layout container for dynamic playlist items
        self.playlists_container = QFrame(self)
        self.playlists_layout = QVBoxLayout(self.playlists_container)
        self.playlists_layout.setContentsMargins(0, 0, 0, 0)
        self.playlists_layout.setSpacing(4)
        self.main_layout.addWidget(self.playlists_container)

        # Create Playlist Button (+ Create Playlist) with dashed border style
        self.btn_add_playlist = QPushButton("+ Create Playlist", self)
        self.btn_add_playlist.setObjectName("addPlaylistBtn")
        self.btn_add_playlist.setStyleSheet("""
            QPushButton#addPlaylistBtn {
                border: 1px dashed #312E81;
                border-radius: 8px;
                padding: 10px 14px;
                color: #818CF8;
                background-color: transparent;
                text-align: center;
                font-weight: 500;
            }
            QPushButton#addPlaylistBtn:hover {
                background-color: rgba(99, 102, 241, 0.06);
                border-color: #6366F1;
            }
        """)
        self.btn_add_playlist.clicked.connect(self.add_playlist_clicked)
        self.main_layout.addWidget(self.btn_add_playlist)

        # Push items to top
        self.main_layout.addStretch()

        # Version stamp
        self.version_label = QLabel("v1.1.0", self)
        self.version_label.setObjectName("sidebarVersion")
        self.main_layout.addWidget(self.version_label)

    def _create_nav_button(self, icon_name: str, label: str, signal: Signal) -> QPushButton:
        """Helper to construct and register standard sidebar navigation buttons."""
        btn = QPushButton(self)
        btn.setObjectName("sidebarNavBtn")
        btn.setCheckable(True)
        btn.clicked.connect(signal)
        btn.clicked.connect(lambda: self._on_btn_clicked(btn))
        self.nav_buttons.append(btn)

        layout = QHBoxLayout(btn)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)

        icon_label = QLabel(btn)
        icon_label.setPixmap(create_vector_icon(icon_name, "#94A3B8", 18).pixmap(18, 18))
        icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(icon_label)

        text_label = QLabel(label, btn)
        text_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(text_label)
        layout.addStretch()

        return btn



    def _on_btn_clicked(self, clicked_btn: QPushButton) -> None:
        """Manages button checked states so only a single sidebar navigation item is highlighted."""
        for btn in self.nav_buttons:
            if btn != clicked_btn:
                btn.setChecked(False)
        clicked_btn.setChecked(True)

    def set_library_count(self, count: int) -> None:
        """Updates the text count next to the Library sidebar item."""
        self.library_badge.setText(str(count))

    def update_folders(self, folders: List[Dict[str, Any]]) -> None:
        """Dynamically repopulates the folders navigation list under the FOLDERS heading."""
        # Clean existing folder buttons
        for path, btn in self._folder_buttons_map.items():
            if btn in self.nav_buttons:
                self.nav_buttons.remove(btn)
            btn.deleteLater()
        self._folder_buttons_map.clear()

        # Build new folders list
        for folder in folders:
            path = folder['path']
            # Get folder base name (e.g. C:/Users/name/Music -> Music)
            display_name = os.path.basename(path.rstrip('/'))
            if not display_name:
                display_name = path

            # Prepend mockup styles if applicable
            if "music" in display_name.lower():
                display_name = display_name
            
            # Create button
            btn = QPushButton(self.folders_container)
            btn.setObjectName("sidebarNavBtn")
            btn.setCheckable(True)
            btn.setToolTip(path)
            
            # Capture path for lambda closure
            btn.clicked.connect(lambda checked=False, p=path, b=btn: self._on_folder_clicked(p, b))
            
            # Setup layout
            layout = QHBoxLayout(btn)
            layout.setContentsMargins(8, 0, 8, 0)
            layout.setSpacing(8)

            folder_icon = QLabel(btn)
            folder_icon.setPixmap(create_vector_icon("folder", "#94A3B8", 18).pixmap(18, 18))
            folder_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            layout.addWidget(folder_icon)

            text_label = QLabel(display_name, btn)
            text_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            layout.addWidget(text_label)
            layout.addStretch()

            # Context Menu for removal
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, p=path: self._show_folder_context_menu(pos, p))

            self.folders_layout.addWidget(btn)
            self._folder_buttons_map[path] = btn
            self.nav_buttons.append(btn)

    def _on_folder_clicked(self, path: str, btn: QPushButton) -> None:
        self._on_btn_clicked(btn)
        self.folder_clicked.emit(path)

    def _show_folder_context_menu(self, pos, path: str) -> None:
        """Right-click menu on folder buttons to remove folder scan path from SQLite library."""
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
                padding: 6px 14px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #EF4444;
                color: #FFFFFF;
            }
        """)
        
        remove_action = QAction("Remove Folder from Library", self)
        remove_action.triggered.connect(lambda: self.remove_folder_requested.emit(path))
        menu.addAction(remove_action)
        
        # Translate context menu coordinates to global screen
        sender_widget = self.sender()
        if sender_widget:
            menu.exec(sender_widget.mapToGlobal(pos))

    def update_playlists(self, playlists: List[Dict[str, Any]]) -> None:
        """Dynamically repopulates the playlists navigation list under the PLAYLISTS heading."""
        # Clean existing playlist buttons
        for playlist_id, btn in self._playlist_buttons_map.items():
            if btn in self.nav_buttons:
                self.nav_buttons.remove(btn)
            btn.deleteLater()
        self._playlist_buttons_map.clear()

        # Build new playlists list
        for pl in playlists:
            pid = pl['id']
            name = pl['name']
            
            # Create button
            btn = QPushButton(self.playlists_container)
            btn.setObjectName("sidebarNavBtn")
            btn.setCheckable(True)
            btn.setToolTip(f"Playlist: {name}")
            
            # Capture ID for lambda closure
            btn.clicked.connect(lambda checked=False, p_id=pid, b=btn: self._on_playlist_clicked(p_id, b))
            
            # Setup layout
            layout = QHBoxLayout(btn)
            layout.setContentsMargins(8, 0, 8, 0)
            layout.setSpacing(8)

            playlist_icon = QLabel(btn)
            playlist_icon.setPixmap(create_vector_icon("genre", "#94A3B8", 18).pixmap(18, 18))
            playlist_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            layout.addWidget(playlist_icon)

            text_label = QLabel(name, btn)
            text_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            layout.addWidget(text_label)
            layout.addStretch()

            # Optional badge for song count
            track_count = pl.get('track_count', 0)
            if track_count > 0:
                badge = QLabel(str(track_count), btn)
                badge.setStyleSheet("""
                    background-color: rgba(99, 102, 241, 0.1);
                    color: #818CF8;
                    font-size: 10px;
                    font-weight: bold;
                    padding: 1px 6px;
                    border-radius: 8px;
                """)
                badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                layout.addWidget(badge)

            # Context Menu for removal
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, p_id=pid: self._show_playlist_context_menu(pos, p_id))

            self.playlists_layout.addWidget(btn)
            self._playlist_buttons_map[pid] = btn
            self.nav_buttons.append(btn)

    def _on_playlist_clicked(self, playlist_id: int, btn: QPushButton) -> None:
        self._on_btn_clicked(btn)
        self.playlist_clicked.emit(playlist_id)

    def _show_playlist_context_menu(self, pos, playlist_id: int) -> None:
        """Right-click menu on playlist buttons to delete playlist."""
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
                padding: 6px 14px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #EF4444;
                color: #FFFFFF;
            }
        """)
        
        remove_action = QAction("Delete Playlist", self)
        remove_action.triggered.connect(lambda: self.remove_playlist_requested.emit(playlist_id))
        menu.addAction(remove_action)
        
        sender_widget = self.sender()
        if sender_widget:
            menu.exec(sender_widget.mapToGlobal(pos))

