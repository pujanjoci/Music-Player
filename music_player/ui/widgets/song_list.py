from typing import List, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QLabel, QHeaderView, QPushButton
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QColor, QIcon
from music_player.models.song import Song
from music_player.ui.utils import create_vector_icon, get_track_placeholder_art


class SongListWidget(QWidget):
    """
    Displays the catalog list in a modern grid view with top tab pills and dynamic columns.
    Top Tabs: Tracks, Albums, Artists, Folders
    """
    song_double_clicked = Signal(Song, int)       # Emits selected Song and its active queue index
    album_double_clicked = Signal(str)            # Emits Album name on double-click
    artist_double_clicked = Signal(str)           # Emits Artist name on double-click
    folder_double_clicked = Signal(str)           # Emits Folder path on double-click
    genre_double_clicked = Signal(str)            # Emits Genre name on double-click
    tab_changed = Signal(str)                      # Emits active view type ('tracks', 'albums', etc.)
    refresh_clicked = Signal()                     # Emits when circular refresh icon is clicked
    favorite_toggled = Signal(Song, bool)          # Emits (song, is_favorite)
    delete_song_requested = Signal(Song)           # Emits (song) for deletion
    edit_song_requested = Signal(Song)             # Emits (song) for metadata editing
    add_to_playlist_requested = Signal(Song, int)          # Emits (song, playlist_id)
    remove_from_playlist_requested = Signal(Song, int)     # Emits (song, playlist_id)
    create_playlist_and_add_requested = Signal(Song)       # Emits (song)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._all_songs: List[Song] = []
        self._view_type: str = "tracks"  # 'tracks', 'albums', 'artists', 'folders'
        self.active_playlist_id: Optional[int] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # --- Top Action Bar ---
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setSpacing(10)

        # Left: Horizontal Pill Tabs for browsing views
        self.pills_container = QWidget(self)
        pills_layout = QHBoxLayout(self.pills_container)
        pills_layout.setContentsMargins(0, 0, 0, 0)
        pills_layout.setSpacing(8)

        self.btn_tab_tracks = QPushButton("Tracks", self.pills_container)
        self.btn_tab_tracks.setObjectName("tabPill")
        self.btn_tab_tracks.setCheckable(True)
        self.btn_tab_tracks.setChecked(True)
        self.btn_tab_tracks.clicked.connect(lambda: self._on_tab_pills_clicked("tracks"))
        pills_layout.addWidget(self.btn_tab_tracks)

        self.btn_tab_albums = QPushButton("Albums", self.pills_container)
        self.btn_tab_albums.setObjectName("tabPill")
        self.btn_tab_albums.setCheckable(True)
        self.btn_tab_albums.clicked.connect(lambda: self._on_tab_pills_clicked("albums"))
        pills_layout.addWidget(self.btn_tab_albums)

        self.btn_tab_artists = QPushButton("Artists", self.pills_container)
        self.btn_tab_artists.setObjectName("tabPill")
        self.btn_tab_artists.setCheckable(True)
        self.btn_tab_artists.clicked.connect(lambda: self._on_tab_pills_clicked("artists"))
        pills_layout.addWidget(self.btn_tab_artists)

        self.btn_tab_folders = QPushButton("Folders", self.pills_container)
        self.btn_tab_folders.setObjectName("tabPill")
        self.btn_tab_folders.setCheckable(True)
        self.btn_tab_folders.clicked.connect(lambda: self._on_tab_pills_clicked("folders"))
        pills_layout.addWidget(self.btn_tab_folders)

        top_bar_layout.addWidget(self.pills_container)
        top_bar_layout.addStretch(1)

        # Right: Search Box & Refresh Icon
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search local files...")
        self.search_bar.setFixedWidth(200)
        self.search_bar.textChanged.connect(self._filter_songs)
        top_bar_layout.addWidget(self.search_bar)

        self.btn_refresh = QPushButton(self)
        self.btn_refresh.setObjectName("refreshBtn")
        self.btn_refresh.setIcon(create_vector_icon("refresh", "#94A3B8", 18))
        self.btn_refresh.setFixedSize(32, 32)
        self.btn_refresh.setToolTip("Scan Library Folders")
        self.btn_refresh.clicked.connect(self.refresh_clicked)
        self.btn_refresh.setStyleSheet("""
            QPushButton#refreshBtn {
                background-color: #10121B;
                border: 1px solid #1A1E2C;
                border-radius: 16px;
                padding: 0px;
            }
            QPushButton#refreshBtn:hover {
                background-color: #1E2335;
                border-color: #6366F1;
            }
        """)
        top_bar_layout.addWidget(self.btn_refresh)

        layout.addLayout(top_bar_layout)

        # --- Dynamic View Header Count ---
        self.count_label = QLabel("0 tracks", self)
        self.count_label.setStyleSheet("color: #64748B; font-size: 12px; margin-left: 2px;")
        layout.addWidget(self.count_label)

        # --- Table View Grid ---
        self.table_widget = QTableWidget(self)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_widget.setShowGrid(False)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table_widget.doubleClicked.connect(self._on_row_double_clicked)
        self.table_widget.cellClicked.connect(self._on_cell_clicked)

        # Setup context menus
        self.table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table_widget)
        self._update_headers()

    def _update_headers(self) -> None:
        """Configures the horizontal columns and sizing depending on self._view_type."""
        self.table_widget.setRowCount(0)
        
        if self._view_type == "tracks":
            self.table_widget.setColumnCount(6)
            self.table_widget.setHorizontalHeaderLabels(["#", "TITLE", "ARTIST", "ALBUM", "DURATION", "♥"])
            self.table_widget.verticalHeader().setDefaultSectionSize(36)

            header = self.table_widget.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)

            self.table_widget.setColumnWidth(0, 45)
            self.table_widget.setColumnWidth(2, 170)
            self.table_widget.setColumnWidth(3, 170)
            self.table_widget.setColumnWidth(4, 75)
            self.table_widget.setColumnWidth(5, 35)

        elif self._view_type == "albums":
            self.table_widget.setColumnCount(4)
            self.table_widget.setHorizontalHeaderLabels(["#", "ALBUM", "ARTIST", "TRACKS"])
            self.table_widget.verticalHeader().setDefaultSectionSize(36)

            header = self.table_widget.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)

            self.table_widget.setColumnWidth(0, 45)
            self.table_widget.setColumnWidth(2, 220)
            self.table_widget.setColumnWidth(3, 80)

        elif self._view_type == "artists":
            self.table_widget.setColumnCount(3)
            self.table_widget.setHorizontalHeaderLabels(["#", "ARTIST", "TRACKS"])
            self.table_widget.verticalHeader().setDefaultSectionSize(36)

            header = self.table_widget.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)

            self.table_widget.setColumnWidth(0, 45)
            self.table_widget.setColumnWidth(2, 80)

        elif self._view_type == "folders":
            self.table_widget.setColumnCount(3)
            self.table_widget.setHorizontalHeaderLabels(["#", "FOLDER PATH", "TRACKS"])
            self.table_widget.verticalHeader().setDefaultSectionSize(36)

            header = self.table_widget.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)

            self.table_widget.setColumnWidth(0, 45)
            self.table_widget.setColumnWidth(2, 80)

        elif self._view_type == "genres":
            self.table_widget.setColumnCount(3)
            self.table_widget.setHorizontalHeaderLabels(["#", "GENRE", "TRACKS"])
            self.table_widget.verticalHeader().setDefaultSectionSize(36)

            header = self.table_widget.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)

            self.table_widget.setColumnWidth(0, 45)
            self.table_widget.setColumnWidth(2, 80)

    def set_view_data(self, view_type: str, data: list) -> None:
        """Loads items dynamically into the list table depending on browse tab categories."""
        self._view_type = view_type
        self._on_tab_pills_clicked(view_type, emit_signal=False)
        self._update_headers()

        self.table_widget.blockSignals(True)
        self.table_widget.setRowCount(0)

        self._all_songs = []

        if self._view_type == "tracks":
            self._all_songs = list(data)
            for idx, song in enumerate(self._all_songs):
                row = self.table_widget.rowCount()
                self.table_widget.insertRow(row)

                # 0. Index
                idx_item = QTableWidgetItem(str(idx + 1))
                idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                idx_item.setData(Qt.ItemDataRole.UserRole, song)
                self.table_widget.setItem(row, 0, idx_item)

                # 1. Title (plain text, no placeholder icon)
                title_item = QTableWidgetItem(song.display_title)
                self.table_widget.setItem(row, 1, title_item)

                # 2. Artist
                self.table_widget.setItem(row, 2, QTableWidgetItem(song.artist))

                # 3. Album
                self.table_widget.setItem(row, 3, QTableWidgetItem(song.album))

                # 4. Duration
                dur_item = QTableWidgetItem(self._format_duration(song.duration))
                dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(row, 4, dur_item)

                # 5. Favorite indicator
                fav_item = QTableWidgetItem()
                if song.favorite:
                    fav_item.setData(Qt.ItemDataRole.DecorationRole, create_vector_icon("heart_filled", "#EF4444", 16))
                self.table_widget.setItem(row, 5, fav_item)

        elif self._view_type == "albums":
            for idx, item in enumerate(data):
                row = self.table_widget.rowCount()
                self.table_widget.insertRow(row)

                idx_item = QTableWidgetItem(str(idx + 1))
                idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                idx_item.setData(Qt.ItemDataRole.UserRole, item)
                self.table_widget.setItem(row, 0, idx_item)

                album_name = item.get("album") or "Unknown Album"
                album_item = QTableWidgetItem(album_name)
                album_item.setIcon(create_vector_icon("cd", "#818CF8", 22))
                self.table_widget.setItem(row, 1, album_item)

                self.table_widget.setItem(row, 2, QTableWidgetItem(item.get("artist") or "Unknown Artist"))

                track_cnt = QTableWidgetItem(str(item.get("track_count") or 0))
                track_cnt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(row, 3, track_cnt)

        elif self._view_type == "artists":
            for idx, item in enumerate(data):
                row = self.table_widget.rowCount()
                self.table_widget.insertRow(row)

                idx_item = QTableWidgetItem(str(idx + 1))
                idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                idx_item.setData(Qt.ItemDataRole.UserRole, item)
                self.table_widget.setItem(row, 0, idx_item)

                artist_name = item.get("artist") or "Unknown Artist"
                artist_item = QTableWidgetItem(artist_name)
                artist_item.setIcon(create_vector_icon("artist", "#818CF8", 22))
                self.table_widget.setItem(row, 1, artist_item)

                track_cnt = QTableWidgetItem(str(item.get("track_count") or 0))
                track_cnt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(row, 2, track_cnt)

        elif self._view_type == "folders":
            for idx, item in enumerate(data):
                row = self.table_widget.rowCount()
                self.table_widget.insertRow(row)

                idx_item = QTableWidgetItem(str(idx + 1))
                idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                idx_item.setData(Qt.ItemDataRole.UserRole, item)
                self.table_widget.setItem(row, 0, idx_item)

                path = item.get("path") or ""
                folder_item = QTableWidgetItem(path)
                folder_item.setIcon(create_vector_icon("folder", "#818CF8", 22))
                self.table_widget.setItem(row, 1, folder_item)

                track_cnt = QTableWidgetItem(str(item.get("track_count") or 0))
                track_cnt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(row, 2, track_cnt)

        elif self._view_type == "genres":
            for idx, item in enumerate(data):
                row = self.table_widget.rowCount()
                self.table_widget.insertRow(row)

                idx_item = QTableWidgetItem(str(idx + 1))
                idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                idx_item.setData(Qt.ItemDataRole.UserRole, item)
                self.table_widget.setItem(row, 0, idx_item)

                genre_name = item.get("genre") or "Unknown Genre"
                genre_item = QTableWidgetItem(genre_name)
                genre_item.setIcon(create_vector_icon("genre", "#818CF8", 22))
                self.table_widget.setItem(row, 1, genre_item)

                track_cnt = QTableWidgetItem(str(item.get("track_count") or 0))
                track_cnt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(row, 2, track_cnt)

        self.table_widget.blockSignals(False)
        self._update_count(len(data))
        self._filter_songs(self.search_bar.text())

    def _on_tab_pills_clicked(self, view_type: str, emit_signal: bool = True) -> None:
        """Sets selected visual style on horizontal pills when tabs are changed."""
        self.btn_tab_tracks.setChecked(view_type == "tracks")
        self.btn_tab_albums.setChecked(view_type == "albums")
        self.btn_tab_artists.setChecked(view_type == "artists")
        self.btn_tab_folders.setChecked(view_type == "folders")

        if emit_signal:
            self.tab_changed.emit(view_type)

    def _on_row_double_clicked(self) -> None:
        """Routes double-click triggers depending on the active view layout."""
        current_row = self.table_widget.currentRow()
        if current_row < 0:
            return

        idx_item = self.table_widget.item(current_row, 0)
        if not idx_item:
            return

        user_data = idx_item.data(Qt.ItemDataRole.UserRole)
        if not user_data:
            return

        if self._view_type == "tracks":
            try:
                full_index = self._all_songs.index(user_data)
                self.song_double_clicked.emit(user_data, full_index)
            except ValueError:
                pass
        elif self._view_type == "albums":
            self.album_double_clicked.emit(user_data.get("album", ""))
        elif self._view_type == "artists":
            self.artist_double_clicked.emit(user_data.get("artist", ""))
        elif self._view_type == "folders":
            self.folder_double_clicked.emit(user_data.get("path", ""))
        elif self._view_type == "genres":
            self.genre_double_clicked.emit(user_data.get("genre", ""))

    def add_song(self, song: Song) -> None:
        """Appends a song to the active table list (only during scanning inside tracks view)."""
        if self._view_type != "tracks":
            return

        self._all_songs.append(song)
        idx = len(self._all_songs) - 1
        row = self.table_widget.rowCount()
        self.table_widget.insertRow(row)

        idx_item = QTableWidgetItem(f"{idx + 1}")
        idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        idx_item.setData(Qt.ItemDataRole.UserRole, song)
        self.table_widget.setItem(row, 0, idx_item)

        title_item = QTableWidgetItem(song.display_title)
        self.table_widget.setItem(row, 1, title_item)

        self.table_widget.setItem(row, 2, QTableWidgetItem(song.artist))
        self.table_widget.setItem(row, 3, QTableWidgetItem(song.album))

        dur_item = QTableWidgetItem(self._format_duration(song.duration))
        dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table_widget.setItem(row, 4, dur_item)

        fav_item = QTableWidgetItem()
        if song.favorite:
            fav_item.setData(Qt.ItemDataRole.DecorationRole, create_vector_icon("heart_filled", "#EF4444", 16))
        self.table_widget.setItem(row, 5, fav_item)

        self._update_count(len(self._all_songs))

    def select_song_by_filepath(self, filepath: str) -> None:
        """Selects and focuses on the row matching the given filepath."""
        if self._view_type != "tracks":
            return
        for row in range(self.table_widget.rowCount()):
            idx_item = self.table_widget.item(row, 0)
            if idx_item:
                song = idx_item.data(Qt.ItemDataRole.UserRole)
                if song and song.filepath == filepath:
                    self.table_widget.setCurrentCell(row, 0)
                    self.table_widget.selectRow(row)
                    break

    def _play_song_at_row(self, song: Song, visual_row: int) -> None:
        try:
            full_index = self._all_songs.index(song)
            self.table_widget.selectRow(visual_row)
            self.song_double_clicked.emit(song, full_index)
        except ValueError:
            pass

    def _filter_songs(self, text: str) -> None:
        """Hides/shows rows in the grid depending on if search queries match cell texts."""
        query = text.lower().strip()
        for row in range(self.table_widget.rowCount()):
            match = False
            # Check all visible text cells in row
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item and query in item.text().lower():
                    match = True
                    break
            self.table_widget.setRowHidden(row, not match)

    def _update_count(self, count: int) -> None:
        self.count_label.setText(f"{count} {self._view_type}")

    def _format_duration(self, seconds: float) -> str:
        if not seconds:
            return "00:00"
        total_seconds = int(seconds)
        mins = total_seconds // 60
        secs = total_seconds % 60
        return f"{mins:02d}:{secs:02d}"

    def _on_cell_clicked(self, row: int, col: int) -> None:
        """Toggles favorite state when clicking on the favorite heart cell directly."""
        if self._view_type == "tracks" and col == 5:
            idx_item = self.table_widget.item(row, 0)
            if idx_item:
                song = idx_item.data(Qt.ItemDataRole.UserRole)
                if song:
                    new_fav = not song.favorite
                    song.favorite = new_fav
                    
                    fav_item = self.table_widget.item(row, 5)
                    if fav_item:
                        if new_fav:
                            fav_item.setData(Qt.ItemDataRole.DecorationRole, create_vector_icon("heart_filled", "#EF4444", 16))
                        else:
                            fav_item.setData(Qt.ItemDataRole.DecorationRole, QIcon())
                    self.favorite_toggled.emit(song, new_fav)

    def _show_context_menu(self, pos) -> None:
        """Shows context menu on right-click over a song row."""
        if self._view_type != "tracks":
            return

        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        item = self.table_widget.itemAt(pos)
        if not item:
            return
            
        row = self.table_widget.row(item)
        idx_item = self.table_widget.item(row, 0)
        if not idx_item:
            return
            
        song = idx_item.data(Qt.ItemDataRole.UserRole)
        if not song:
            return
            
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
        
        play_action = QAction("Play", self)
        play_action.triggered.connect(lambda _checked=False, s=song, r=row: self._play_song_at_row(s, r))
        menu.addAction(play_action)
        
        fav_text = "Remove from Favorites" if song.favorite else "Add to Favorites"
        fav_action = QAction(fav_text, self)
        fav_action.triggered.connect(lambda _checked=False, s=song, r=row: self._on_toggle_favorite_triggered(s, r))
        menu.addAction(fav_action)
        
        edit_action = QAction("Edit Metadata...", self)
        edit_action.triggered.connect(lambda _checked=False, s=song: self.edit_song_requested.emit(s))
        menu.addAction(edit_action)

        # Add to Playlist Sub-menu
        from music_player.database.repository import MusicRepository
        playlists = MusicRepository.get_playlists()
        
        add_to_playlist_menu = menu.addMenu("Add to Playlist")
        add_to_playlist_menu.setStyleSheet("""
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
        
        new_playlist_action = QAction("Create New Playlist...", self)
        new_playlist_action.triggered.connect(lambda _checked=False, s=song: self.create_playlist_and_add_requested.emit(s))
        add_to_playlist_menu.addAction(new_playlist_action)
        
        if playlists:
            add_to_playlist_menu.addSeparator()
            for pl in playlists:
                pl_action = QAction(pl['name'], self)
                pl_action.triggered.connect(lambda _checked=False, s=song, pid=pl['id']: self.add_to_playlist_requested.emit(s, pid))
                add_to_playlist_menu.addAction(pl_action)

        if self.active_playlist_id is not None:
            menu.addSeparator()
            remove_playlist_action = QAction("Remove from Playlist", self)
            remove_playlist_action.triggered.connect(lambda _checked=False, s=song: self.remove_from_playlist_requested.emit(s, self.active_playlist_id))
            menu.addAction(remove_playlist_action)
            
        menu.addSeparator()
        delete_action = QAction("Delete...", self)
        delete_action.triggered.connect(lambda _checked=False, s=song: self.delete_song_requested.emit(s))
        menu.addAction(delete_action)
        
        menu.exec(self.table_widget.mapToGlobal(pos))

    def _on_toggle_favorite_triggered(self, song: Song, row: int) -> None:
        new_fav = not song.favorite
        song.favorite = new_fav
        
        fav_item = self.table_widget.item(row, 5)
        if fav_item:
            if new_fav:
                fav_item.setData(Qt.ItemDataRole.DecorationRole, create_vector_icon("heart_filled", "#EF4444", 16))
            else:
                fav_item.setData(Qt.ItemDataRole.DecorationRole, QIcon())
        self.favorite_toggled.emit(song, new_fav)


