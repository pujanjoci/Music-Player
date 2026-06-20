import os
import logging
from typing import List, Optional, Dict, Any
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QSplitter, QFrame, QInputDialog, QMessageBox, QLineEdit, QStackedWidget
from PySide6.QtCore import Qt, Slot, QUrl
from PySide6.QtGui import QPixmap, QColor, QIcon
from PySide6.QtMultimedia import QMediaPlayer

from music_player.models.song import Song
from music_player.player.audio_player import AudioPlayer
from music_player.player.play_queue import PlayQueue, RepeatMode
from music_player.services.scanner import LibraryScanner
from music_player.services.metadata import MetadataService
from music_player.database.repository import MusicRepository
from music_player.database.connection import DbConnection
from music_player.settings.config import ConfigService

from music_player.ui.widgets.sidebar import Sidebar
from music_player.ui.widgets.song_list import SongListWidget
from music_player.ui.widgets.player_controls import PlayerControls
from music_player.ui.widgets.now_playing_panel import NowPlayingPanel
from music_player.ui.widgets.mobile_player_view import MobilePlayerView
from music_player.ui.stylesheet import DARK_STYLESHEET
from music_player.services.artwork_loader import ArtworkLoader
from music_player.ui.dialogs.edit_metadata_dialog import EditMetadataDialog
from music_player.ui.utils import create_vector_icon, round_pixmap

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window — Music Player (Offline).
    """
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Music Player (Offline)")
        
        # Set window icon
        import sys
        if hasattr(sys, "_MEIPASS"):
            icon_path = os.path.join(sys._MEIPASS, "app_icon.png")
        else:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "app_icon.png")
            
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            self.setWindowIcon(create_vector_icon("cd", "#6366F1", 32))
            
        self.resize(1100, 720)

        # Initialize engines & settings
        self.audio_player = AudioPlayer()
        self.play_queue = PlayQueue()
        self.settings = ConfigService.load()
        self.active_scanner: Optional[LibraryScanner] = None
        self.active_artwork_loader: Optional[ArtworkLoader] = None
        
        self._current_view_favorites = False
        self._scan_queue: List[str] = []

        self._init_ui()
        self._wire_signals()
        
        # Load initial database folder scanning lists and library songs
        self.sidebar.update_folders(MusicRepository.get_folders())
        self.sidebar.update_playlists(MusicRepository.get_playlists())
        self._load_initial_library()
        self._apply_saved_settings()

    def _init_ui(self) -> None:
        # Central Widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # QStackedWidget to support responsive Desktop / Mobile Views
        self.view_stack = QStackedWidget(self.central_widget)
        main_layout.addWidget(self.view_stack)

        # --- Desktop View Container ---
        self.desktop_view_widget = QWidget(self.view_stack)
        desktop_layout = QVBoxLayout(self.desktop_view_widget)
        desktop_layout.setContentsMargins(0, 0, 0, 0)
        desktop_layout.setSpacing(0)

        # Main splitter dividing Sidebar and Library List Grid (2-column layout)
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self.desktop_view_widget)
        self.splitter.setChildrenCollapsible(False)
        desktop_layout.addWidget(self.splitter, 1)

        # --- Column 1: Sidebar ---
        self.left_panel = QFrame(self.splitter)
        self.left_panel.setObjectName("sidebarFrame")
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.sidebar = Sidebar(self.left_panel)
        left_layout.addWidget(self.sidebar)
        self.splitter.addWidget(self.left_panel)

        # --- Column 2: Library Grid Table ---
        self.middle_panel = QFrame(self.splitter)
        self.middle_panel.setObjectName("libraryFrame")
        middle_layout = QVBoxLayout(self.middle_panel)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)

        self.song_list = SongListWidget(self.middle_panel)
        middle_layout.addWidget(self.song_list)
        self.splitter.addWidget(self.middle_panel)

        # --- Column 3: Now Playing Sidebar ---
        self.right_panel = QFrame(self.splitter)
        self.right_panel.setObjectName("nowPlayingFrame")
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.now_playing_panel = NowPlayingPanel(self.right_panel)
        right_layout.addWidget(self.now_playing_panel)
        self.splitter.addWidget(self.right_panel)

        # Set initial splitter widths (Sidebar: 220px, Main Grid: remaining, Right Sidebar: 250px)
        self.splitter.setSizes([220, 630, 250])

        # --- Bottom Panel: Player Control Bar ---
        self.player_controls = PlayerControls(self.desktop_view_widget)
        desktop_layout.addWidget(self.player_controls)

        self.view_stack.addWidget(self.desktop_view_widget)

        # --- Mobile View Container ---
        self.mobile_view_widget = MobilePlayerView(self.view_stack)
        self.view_stack.addWidget(self.mobile_view_widget)

        # --- Status Bar ---
        self.statusBar().showMessage("Ready")

        # Apply dark QSS stylesheet
        self.setStyleSheet(DARK_STYLESHEET)

    def _wire_signals(self) -> None:
        # Sidebar Actions
        self.sidebar.add_folder_clicked.connect(self._on_scan_folder_clicked)
        self.sidebar.library_clicked.connect(self._on_library_clicked)
        self.sidebar.albums_clicked.connect(self._on_albums_clicked)
        self.sidebar.artists_clicked.connect(self._on_artists_clicked)
        self.sidebar.genres_clicked.connect(self._on_genres_clicked)
        self.sidebar.folder_clicked.connect(self._on_folder_clicked)
        self.sidebar.remove_folder_requested.connect(self._on_remove_folder_clicked)
        self.sidebar.favorites_clicked.connect(self._on_favorites_clicked)
        self.sidebar.add_playlist_clicked.connect(self._on_create_playlist)
        self.sidebar.playlist_clicked.connect(self._show_songs_by_playlist)
        self.sidebar.remove_playlist_requested.connect(self._on_delete_playlist)

        # Song List Actions
        self.song_list.song_double_clicked.connect(self._on_song_double_clicked)
        self.song_list.album_double_clicked.connect(self._on_album_double_clicked)
        self.song_list.artist_double_clicked.connect(self._on_artist_double_clicked)
        self.song_list.folder_double_clicked.connect(self._on_folder_double_clicked)
        self.song_list.genre_double_clicked.connect(self._on_genre_double_clicked)
        self.song_list.tab_changed.connect(self._on_tab_changed)
        self.song_list.refresh_clicked.connect(self._on_refresh_clicked)
        self.song_list.favorite_toggled.connect(self._on_list_favorite_toggled)
        self.song_list.edit_song_requested.connect(self._on_edit_song_requested)
        self.song_list.delete_song_requested.connect(self._on_delete_song_requested)
        self.song_list.search_bar.textChanged.connect(self._on_search_text_changed)
        self.song_list.add_to_playlist_requested.connect(self._on_add_to_playlist)
        self.song_list.remove_from_playlist_requested.connect(self._on_remove_from_playlist)
        self.song_list.create_playlist_and_add_requested.connect(self._on_create_playlist_and_add)

        # Player Controls Actions
        self.player_controls.play_clicked.connect(self._on_play_clicked)
        self.player_controls.pause_clicked.connect(self._on_pause_clicked)
        self.player_controls.stop_clicked.connect(self._on_stop_clicked)
        self.player_controls.prev_clicked.connect(self._on_prev_clicked)
        self.player_controls.next_clicked.connect(self._on_next_clicked)
        self.player_controls.seek_requested.connect(self.audio_player.set_position)
        self.player_controls.volume_changed.connect(self._on_volume_changed)
        self.player_controls.mute_toggled.connect(self.audio_player.set_muted)
        self.player_controls.shuffle_toggled.connect(self._on_shuffle_toggled)
        self.player_controls.repeat_mode_changed.connect(self._on_repeat_mode_changed)
        self.player_controls.favorite_toggled.connect(self._on_bottom_favorite_toggled)
        self.now_playing_panel.favorite_toggled.connect(self._on_bottom_favorite_toggled)

        # Audio Player Signals
        self.audio_player.position_changed.connect(self.player_controls.update_position)
        self.audio_player.position_changed.connect(self.mobile_view_widget.update_position)
        self.audio_player.duration_changed.connect(self._on_player_duration_changed)
        self.audio_player.state_changed.connect(self.player_controls.set_playback_state)
        self.audio_player.state_changed.connect(self.mobile_view_widget.set_playback_state)
        self.audio_player.song_finished.connect(self._on_song_finished)

        # Mobile View Actions
        self.mobile_view_widget.play_clicked.connect(self._on_play_clicked)
        self.mobile_view_widget.pause_clicked.connect(self._on_pause_clicked)
        self.mobile_view_widget.prev_clicked.connect(self._on_prev_clicked)
        self.mobile_view_widget.next_clicked.connect(self._on_next_clicked)
        self.mobile_view_widget.seek_requested.connect(self.audio_player.set_position)
        self.mobile_view_widget.repeat_toggled.connect(self._on_mobile_repeat_changed)
        self.mobile_view_widget.favorite_toggled.connect(self._on_bottom_favorite_toggled)
        self.mobile_view_widget.song_selected.connect(self._on_mobile_song_selected)
        self.mobile_view_widget.edit_song_requested.connect(self._on_edit_song_requested)
        self.mobile_view_widget.delete_song_requested.connect(self._on_delete_song_requested)

    def _load_initial_library(self) -> None:
        """Loads cached song list from the database on startup."""
        songs = MusicRepository.get_all_songs()
        self.sidebar.set_library_count(len(songs))
        self._show_all_songs()

    def _apply_saved_settings(self) -> None:
        """Applies volume and mute settings from config on startup."""
        vol = self.settings.get("volume", 70)
        self.audio_player.set_volume(vol)
        self.player_controls.set_volume(vol)

        is_muted = self.settings.get("is_muted", False)
        self.audio_player.set_muted(is_muted)
        self.player_controls.btn_mute.setChecked(is_muted)

    # --- Scanning & Folder Management ---

    def _start_sequential_scan(self, folders: List[str]) -> None:
        """Sequential scanning engine that runs through a list of folders one by one."""
        self._scan_queue = [f.replace('\\', '/') for f in folders]
        self._run_next_scan()

    def _run_next_scan(self) -> None:
        if not self._scan_queue:
            # Reached end of scan queue
            songs = MusicRepository.get_all_songs()
            self.sidebar.set_library_count(len(songs))
            self.sidebar.update_folders(MusicRepository.get_folders())
            self._show_all_songs()
            self.statusBar().showMessage("Library scan completed.")
            return

        next_path = self._scan_queue.pop(0)
        self.statusBar().showMessage(f"Scanning: {next_path}...")

        # Purge references to files no longer on disk
        MusicRepository.clean_missing_songs(next_path)

        if self.active_scanner and self.active_scanner.isRunning():
            self.active_scanner.requestInterruption()
            self.active_scanner.wait()

        self.active_scanner = LibraryScanner(next_path)
        self.active_scanner.song_found.connect(self._on_song_scanned)
        self.active_scanner.scan_progress.connect(self._on_scan_progress)
        self.active_scanner.scan_finished.connect(self._on_scan_next_finished)
        self.active_scanner.start()

    @Slot(Song)
    def _on_song_scanned(self, song: Song) -> None:
        MusicRepository.upsert_song(song)

    @Slot(str)
    def _on_scan_progress(self, msg: str) -> None:
        self.statusBar().showMessage(msg)

    @Slot(list)
    def _on_scan_next_finished(self, songs: List[Song]) -> None:
        # Continue executing items in queue
        self._run_next_scan()

    @Slot()
    def _on_scan_folder_clicked(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Music Library Folder", self.settings.get("last_folder", ""))
        if folder:
            # Standardize and insert
            folder_norm = folder.replace('\\', '/')
            self.settings["last_folder"] = folder_norm
            ConfigService.save(self.settings)

            # Insert path
            MusicRepository.add_folder(folder_norm)
            self.sidebar.update_folders(MusicRepository.get_folders())

            # Begin scan of just this new folder
            self._start_sequential_scan([folder_norm])

    @Slot(str)
    def _on_remove_folder_clicked(self, path: str) -> None:
        """Deletes folder from scanner list and purges related tracks from active database catalog."""
        MusicRepository.delete_folder(path)
        self.sidebar.update_folders(MusicRepository.get_folders())
        songs = MusicRepository.get_all_songs()
        self.sidebar.set_library_count(len(songs))
        self._show_all_songs()
        self.statusBar().showMessage(f"Removed folder: {path}")

    @Slot()
    def _on_refresh_clicked(self) -> None:
        """Circular refresh trigger scans all registered folder paths from SQLite DB."""
        folders_list = [f['path'] for f in MusicRepository.get_all_folders()]
        if folders_list:
            self._start_sequential_scan(folders_list)
        else:
            self.statusBar().showMessage("No folders to scan. Add a folder path first.")

    # --- View Swapping Slots ---

    @Slot()
    def _show_all_songs(self) -> None:
        self.song_list.active_playlist_id = None
        self._current_view_favorites = False
        songs = MusicRepository.get_all_songs()
        self.song_list.set_view_data("tracks", songs)
        self.play_queue.set_songs(songs, start_index=0)
        self.mobile_view_widget.set_songs(songs)

        current = self.audio_player.get_current_song()
        if current:
            self.song_list.select_song_by_filepath(current.filepath)

    @Slot()
    def _show_favorites(self) -> None:
        self.song_list.active_playlist_id = None
        self._current_view_favorites = True
        songs = MusicRepository.get_favorites()
        self.song_list.set_view_data("tracks", songs)
        self.play_queue.set_songs(songs, start_index=0)
        self.mobile_view_widget.set_songs(songs)

        current = self.audio_player.get_current_song()
        if current:
            self.song_list.select_song_by_filepath(current.filepath)

    @Slot()
    def _show_albums(self) -> None:
        self.song_list.active_playlist_id = None
        self._current_view_favorites = False
        albums = MusicRepository.get_albums()
        self.song_list.set_view_data("albums", albums)

    @Slot()
    def _show_artists(self) -> None:
        self.song_list.active_playlist_id = None
        self._current_view_favorites = False
        artists = MusicRepository.get_artists()
        self.song_list.set_view_data("artists", artists)

    @Slot()
    def _show_genres(self) -> None:
        self.song_list.active_playlist_id = None
        self._current_view_favorites = False
        # Fetch genres directly from database since there is no separate repo method
        conn = DbConnection.get_connection()
        genres = []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT genre, COUNT(id) as track_count
                FROM songs
                WHERE genre IS NOT NULL AND genre != ''
                GROUP BY genre
                ORDER BY genre COLLATE NOCASE ASC
            """)
            rows = cursor.fetchall()
            for row in rows:
                genres.append({
                    "genre": row["genre"],
                    "track_count": row["track_count"]
                })
        except Exception as e:
            logger.error(f"Error loading genres: {e}")
        finally:
            conn.close()
        self.song_list.set_view_data("genres", genres)

    @Slot(str)
    def _show_songs_by_folder(self, folder_path: str) -> None:
        self.song_list.active_playlist_id = None
        self._current_view_favorites = False
        songs = MusicRepository.get_songs_by_folder(folder_path)
        self.song_list.set_view_data("tracks", songs)
        self.play_queue.set_songs(songs, start_index=0)
        self.mobile_view_widget.set_songs(songs)

        current = self.audio_player.get_current_song()
        if current:
            self.song_list.select_song_by_filepath(current.filepath)

    def _clear_search_bar(self) -> None:
        self.song_list.search_bar.blockSignals(True)
        self.song_list.search_bar.clear()
        self.song_list.search_bar.blockSignals(False)

    @Slot()
    def _on_library_clicked(self) -> None:
        self._clear_search_bar()
        self._show_all_songs()

    @Slot()
    def _on_favorites_clicked(self) -> None:
        self._clear_search_bar()
        self._show_favorites()

    @Slot()
    def _on_albums_clicked(self) -> None:
        self._clear_search_bar()
        self._show_albums()

    @Slot()
    def _on_artists_clicked(self) -> None:
        self._clear_search_bar()
        self._show_artists()

    @Slot()
    def _on_genres_clicked(self) -> None:
        self._clear_search_bar()
        self._show_genres()

    @Slot(str)
    def _on_folder_clicked(self, folder_path: str) -> None:
        self._clear_search_bar()
        self._show_songs_by_folder(folder_path)

    @Slot(str)
    def _on_tab_changed(self, view_type: str) -> None:
        """Handles horizontal pill tabs clicked in SongListWidget."""
        self.song_list.active_playlist_id = None
        self._clear_search_bar()
        if view_type == "tracks":
            self._show_all_songs()
        elif view_type == "albums":
            self._show_albums()
        elif view_type == "artists":
            self._show_artists()
        elif view_type == "folders":
            folders = MusicRepository.get_folders()
            self.song_list.set_view_data("folders", folders)

    @Slot(str)
    def _on_search_text_changed(self, text: str) -> None:
        """Forces the active view back to Tracks (all library songs) and resets sidebar if searching."""
        if text.strip():
            is_favorites_active = self._current_view_favorites or self.sidebar.btn_favorites_mix.isChecked()
            is_folder_active = any(btn.isChecked() for btn in self.sidebar._folder_buttons_map.values())
            is_playlist_active = self.song_list.active_playlist_id is not None or any(btn.isChecked() for btn in self.sidebar._playlist_buttons_map.values())
            
            if self.song_list._view_type != "tracks" or is_favorites_active or is_folder_active or is_playlist_active:
                # Reset active playlist ID
                self.song_list.active_playlist_id = None
                # Reset sidebar state to check "Library" only
                self.sidebar.btn_library.setChecked(True)
                self.sidebar._on_btn_clicked(self.sidebar.btn_library)
                self._show_all_songs()

    @Slot(int)
    def _show_songs_by_playlist(self, playlist_id: int) -> None:
        self._current_view_favorites = False
        self.song_list.active_playlist_id = playlist_id
        songs = MusicRepository.get_songs_by_playlist(playlist_id)
        self.song_list.set_view_data("tracks", songs)
        self.play_queue.set_songs(songs, start_index=0)
        self.mobile_view_widget.set_songs(songs)

        current = self.audio_player.get_current_song()
        if current:
            self.song_list.select_song_by_filepath(current.filepath)

    @Slot()
    def _on_create_playlist(self) -> Optional[int]:
        name, ok = QInputDialog.getText(
            self, "Create Playlist", "Enter playlist name:", QLineEdit.EchoMode.Normal
        )
        if ok and name.strip():
            playlist_name = name.strip()
            playlist_id = MusicRepository.create_playlist(playlist_name)
            if playlist_id:
                self.sidebar.update_playlists(MusicRepository.get_playlists())
                self.statusBar().showMessage(f"Created playlist: {playlist_name}")
                return playlist_id
            else:
                QMessageBox.warning(self, "Warning", f"Failed to create playlist. A playlist named '{playlist_name}' may already exist.")
        return None

    @Slot(int)
    def _on_delete_playlist(self, playlist_id: int) -> None:
        confirm = QMessageBox.question(
            self,
            "Delete Playlist",
            "Are you sure you want to delete this playlist?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            MusicRepository.delete_playlist(playlist_id)
            self.sidebar.update_playlists(MusicRepository.get_playlists())
            if self.song_list.active_playlist_id == playlist_id:
                self.sidebar.btn_library.setChecked(True)
                self.sidebar._on_btn_clicked(self.sidebar.btn_library)
                self._show_all_songs()
            self.statusBar().showMessage("Playlist deleted.")

    @Slot(Song, int)
    def _on_add_to_playlist(self, song: Song, playlist_id: int) -> None:
        success = MusicRepository.add_song_to_playlist(song.filepath, playlist_id)
        if success:
            self.sidebar.update_playlists(MusicRepository.get_playlists())
            if self.song_list.active_playlist_id == playlist_id:
                self._show_songs_by_playlist(playlist_id)
            self.statusBar().showMessage("Added song to playlist.")
        else:
            self.statusBar().showMessage("Song already exists in this playlist.")

    @Slot(Song, int)
    def _on_remove_from_playlist(self, song: Song, playlist_id: int) -> None:
        MusicRepository.remove_song_from_playlist(song.filepath, playlist_id)
        self.sidebar.update_playlists(MusicRepository.get_playlists())
        if self.song_list.active_playlist_id == playlist_id:
            self._show_songs_by_playlist(playlist_id)
        self.statusBar().showMessage("Removed song from playlist.")

    @Slot(Song)
    def _on_create_playlist_and_add(self, song: Song) -> None:
        playlist_id = self._on_create_playlist()
        if playlist_id:
            self._on_add_to_playlist(song, playlist_id)

    # --- Double Click Filters ---

    @Slot(str)
    def _on_album_double_clicked(self, album_name: str) -> None:
        songs = MusicRepository.get_songs_by_album(album_name)
        self.song_list.set_view_data("tracks", songs)
        self.play_queue.set_songs(songs, start_index=0)
        self.mobile_view_widget.set_songs(songs)

    @Slot(str)
    def _on_artist_double_clicked(self, artist_name: str) -> None:
        songs = MusicRepository.get_songs_by_artist(artist_name)
        self.song_list.set_view_data("tracks", songs)
        self.play_queue.set_songs(songs, start_index=0)
        self.mobile_view_widget.set_songs(songs)

    @Slot(str)
    def _on_folder_double_clicked(self, folder_path: str) -> None:
        songs = MusicRepository.get_songs_by_folder(folder_path)
        self.song_list.set_view_data("tracks", songs)
        self.play_queue.set_songs(songs, start_index=0)
        self.mobile_view_widget.set_songs(songs)

    @Slot(str)
    def _on_genre_double_clicked(self, genre_name: str) -> None:
        conn = DbConnection.get_connection()
        songs = []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, ar.name as artist, al.name as album
                FROM songs s
                LEFT JOIN artists ar ON s.artist_id = ar.id
                LEFT JOIN albums al ON s.album_id = al.id
                WHERE s.genre = ?
                ORDER BY s.title COLLATE NOCASE ASC
            """, (genre_name,))
            rows = cursor.fetchall()
            for row in rows:
                songs.append(MusicRepository._row_to_song(row))
        except Exception as e:
            logger.error(f"Error querying songs by genre: {e}")
        finally:
            conn.close()

        self.song_list.set_view_data("tracks", songs)
        self.play_queue.set_songs(songs, start_index=0)
        self.mobile_view_widget.set_songs(songs)

    # --- Playback Logic & Sync ---

    @Slot(Song, int)
    def _on_song_double_clicked(self, song: Song, index: int) -> None:
        """Handles song list double-click: updates queue pointer and plays."""
        self.play_queue.set_songs(self.song_list._all_songs, start_index=index)
        self._play_song(song)

    def _play_song(self, song: Song) -> None:
        """Loads metadata, updates UI, and triggers playback."""
        # 1. Trigger audio player
        self.audio_player.play_song(song)

        # 2. Update player controls metadata
        self.player_controls.set_active_song(song, None)
        self.now_playing_panel.set_active_song(song, None)
        self.mobile_view_widget.set_active_song(song, None)

        # 3. Load Album Art in background
        if self.active_artwork_loader and self.active_artwork_loader.isRunning():
            self.active_artwork_loader.terminate()
            self.active_artwork_loader.wait()

        self.active_artwork_loader = ArtworkLoader(song.filepath)
        self.active_artwork_loader.artwork_loaded.connect(self._on_artwork_loaded)
        self.active_artwork_loader.start()

        # 4. Highlight song in UI List
        self.song_list.select_song_by_filepath(song.filepath)
        self.statusBar().showMessage(f"Playing: {song.display_title}")

    @Slot(bytes, str)
    def _on_artwork_loaded(self, artwork_data: bytes, filepath: str) -> None:
        """Triggered when artwork background loading completes."""
        current_song = self.audio_player.get_current_song()
        if not current_song or current_song.filepath != filepath:
            return

        artwork_pixmap = None
        if artwork_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(artwork_data):
                artwork_pixmap = pixmap

        # Update bottom bar mini artwork and right panel artwork
        self.player_controls.set_active_song(current_song, artwork_pixmap)
        self.now_playing_panel.set_active_song(current_song, artwork_pixmap)
        self.mobile_view_widget.set_active_song(current_song, artwork_pixmap)

    @Slot(Song, bool)
    def _on_list_favorite_toggled(self, song: Song, is_fav: bool) -> None:
        """Triggered when user clicks the favorite column in the table list or toggles via context menu."""
        # Update SQLite
        MusicRepository.update_favorite(song.filepath, is_fav)
        
        # Synchronize Now Playing bottom controls if this song is currently playing
        current = self.audio_player.get_current_song()
        if current and current.filepath == song.filepath:
            current.favorite = is_fav
            self.player_controls.btn_mini_favorite.setChecked(is_fav)
            if is_fav:
                self.player_controls.btn_mini_favorite.setIcon(create_vector_icon("heart_filled", "#EF4444", 16))
            else:
                self.player_controls.btn_mini_favorite.setIcon(create_vector_icon("heart_outline", "#64748B", 16))
            
            self.now_playing_panel.btn_favorite.setChecked(is_fav)
            if is_fav:
                self.now_playing_panel.btn_favorite.setIcon(create_vector_icon("heart_filled", "#EF4444", 22))
            else:
                self.now_playing_panel.btn_favorite.setIcon(create_vector_icon("heart_outline", "#94A3B8", 22))
                
        # If in favorites view, refresh view automatically
        if self._current_view_favorites:
            self._show_favorites()
        else:
            self._update_song_in_list_data(song)

    @Slot(bool)
    def _on_bottom_favorite_toggled(self, is_fav: bool) -> None:
        """Triggered when user clicks the heart button inside the bottom controls bar or right panel."""
        song = self.audio_player.get_current_song()
        if not song:
            return
        
        song.favorite = is_fav
        MusicRepository.update_favorite(song.filepath, is_fav)

        # Sync both favorite buttons
        self.player_controls.btn_mini_favorite.setChecked(is_fav)
        if is_fav:
            self.player_controls.btn_mini_favorite.setIcon(create_vector_icon("heart_filled", "#EF4444", 16))
        else:
            self.player_controls.btn_mini_favorite.setIcon(create_vector_icon("heart_outline", "#64748B", 16))

        self.now_playing_panel.btn_favorite.setChecked(is_fav)
        if is_fav:
            self.now_playing_panel.btn_favorite.setIcon(create_vector_icon("heart_filled", "#EF4444", 22))
        else:
            self.now_playing_panel.btn_favorite.setIcon(create_vector_icon("heart_outline", "#94A3B8", 22))

        if self._current_view_favorites:
            self._show_favorites()
        else:
            self._update_song_in_list_data(song)

    @Slot(Song)
    def _on_edit_song_requested(self, song: Song) -> None:
        """Opens dialog to rename song or edit artist/album/genre metadata."""
        existing_genres = MusicRepository.get_all_genres()
        dialog = EditMetadataDialog(song.title, song.artist, song.album, song.genre or "", existing_genres, self)
        if dialog.exec() == EditMetadataDialog.DialogCode.Accepted:
            new_title, new_artist, new_album, new_genre = dialog.get_data()
            if not new_title:
                new_title = os.path.splitext(os.path.basename(song.filepath))[0]
            
            # 1. Update mutagen tags on physical file
            MetadataService.write_metadata(song.filepath, new_title, new_artist, new_album, new_genre)
            
            # 2. Update database
            MusicRepository.update_song_metadata(song.filepath, new_title, new_artist, new_album, new_genre)
            
            # 3. Update song model object
            song.title = new_title
            song.artist = new_artist
            song.album = new_album
            song.genre = new_genre
            
            # 4. Refresh view
            if self._current_view_favorites:
                self._show_favorites()
            else:
                # Refresh according to view type
                if self.song_list._view_type == "tracks":
                    self._show_all_songs()
                elif self.song_list._view_type == "albums":
                    self._show_albums()
                elif self.song_list._view_type == "artists":
                    self._show_artists()
                elif self.song_list._view_type == "genres":
                    self._show_genres()
                
            # 5. If editing currently playing song, refresh bottom controls
            current = self.audio_player.get_current_song()
            if current and current.filepath == song.filepath:
                current.title = new_title
                current.artist = new_artist
                current.album = new_album
                current.genre = new_genre
                
                # Fetch artwork pixmap from controls if loaded
                self.player_controls.set_active_song(current, self.player_controls.mini_art.pixmap())
                self.now_playing_panel.set_active_song(current, self.player_controls.mini_art.pixmap())
                self.statusBar().showMessage(f"Updated metadata for playing song: {new_title}")
            else:
                self.statusBar().showMessage(f"Updated metadata for: {new_title}")

    def _update_song_in_list_data(self, song: Song) -> None:
        """Updates internal reference data of song in table widget cells."""
        # Update internal list
        for idx, s in enumerate(self.song_list._all_songs):
            if s.filepath == song.filepath:
                self.song_list._all_songs[idx] = song
                break
        
        # Visually update matching table row
        for row in range(self.song_list.table_widget.rowCount()):
            idx_item = self.song_list.table_widget.item(row, 0)
            if idx_item:
                item_song = idx_item.data(Qt.ItemDataRole.UserRole)
                if item_song and hasattr(item_song, "filepath") and item_song.filepath == song.filepath:
                    idx_item.setData(Qt.ItemDataRole.UserRole, song)
                    
                    title_cell = self.song_list.table_widget.item(row, 1)
                    if title_cell:
                        title_cell.setText(song.display_title)
                    artist_cell = self.song_list.table_widget.item(row, 2)
                    if artist_cell:
                        artist_cell.setText(song.artist)
                    album_cell = self.song_list.table_widget.item(row, 3)
                    if album_cell:
                        album_cell.setText(song.album)
                    dur_cell = self.song_list.table_widget.item(row, 4)
                    if dur_cell:
                        dur_cell.setText(self.song_list._format_duration(song.duration))
                    fav_cell = self.song_list.table_widget.item(row, 5)
                    if fav_cell:
                        if song.favorite:
                            fav_cell.setData(Qt.ItemDataRole.DecorationRole, create_vector_icon("heart_filled", "#EF4444", 16))
                        else:
                            fav_cell.setData(Qt.ItemDataRole.DecorationRole, QIcon())
                    break

    @Slot()
    def _on_play_clicked(self) -> None:
        current_song = self.audio_player.get_current_song()
        if current_song:
            self.audio_player.play()
        else:
            song = self.play_queue.get_current_song()
            if song:
                self._play_song(song)

    @Slot()
    def _on_pause_clicked(self) -> None:
        self.audio_player.pause()

    @Slot()
    def _on_stop_clicked(self) -> None:
        self.audio_player.stop()
        self.player_controls.set_active_song(None)
        self.now_playing_panel.set_active_song(None)
        self.mobile_view_widget.set_active_song(None)
        self.statusBar().showMessage("Playback stopped")

    @Slot()
    def _on_prev_clicked(self) -> None:
        song = self.play_queue.prev_song()
        if song:
            self._play_song(song)

    @Slot()
    def _on_next_clicked(self) -> None:
        song = self.play_queue.next_song()
        if song:
            self._play_song(song)
        else:
            self._on_stop_clicked()

    @Slot()
    def _on_song_finished(self) -> None:
        """Triggered automatically when the media finishes playing."""
        current_song = self.audio_player.get_current_song()
        if current_song:
            MusicRepository.increment_play_count(current_song.filepath)
            current_song.play_count += 1
            self._update_song_in_list_data(current_song)

        logger.info("Song finished, advancing queue...")
        song = self.play_queue.next_song()
        if song:
            self._play_song(song)
        else:
            self._on_stop_clicked()

    @Slot(int)
    def _on_volume_changed(self, value: int) -> None:
        self.audio_player.set_volume(value)
        self.settings["volume"] = value
        ConfigService.save(self.settings)

    @Slot(bool)
    def _on_shuffle_toggled(self, enabled: bool) -> None:
        self.play_queue.set_shuffle(enabled)
        logger.info(f"Shuffle {'enabled' if enabled else 'disabled'}")

    @Slot(RepeatMode)
    def _on_repeat_mode_changed(self, mode: RepeatMode) -> None:
        self.play_queue.set_repeat_mode(mode)
        self.mobile_view_widget.set_repeat_mode(mode)
        logger.info(f"Repeat mode set to: {mode.name}")

    @Slot(int)
    def _on_player_duration_changed(self, duration_ms: int) -> None:
        """Triggered when duration changes. Updates database records and grid visually."""
        self.player_controls.update_duration(duration_ms)
        
        current_song = self.audio_player.get_current_song()
        if current_song and duration_ms > 0:
            duration_sec = duration_ms / 1000.0
            if abs(current_song.duration - duration_sec) > 1.0:
                current_song.duration = duration_sec
                MusicRepository.update_song_duration(current_song.filepath, duration_sec)
                self._update_song_in_list_data(current_song)

    @Slot(RepeatMode)
    def _on_mobile_repeat_changed(self, mode: RepeatMode) -> None:
        """Synchronizes repeat mode from mobile view to play queue and desktop controls."""
        self.play_queue.set_repeat_mode(mode)
        self.player_controls.set_repeat_mode(mode)
        logger.info(f"Repeat mode updated from mobile: {mode.name}")

    @Slot(Song, int)
    def _on_mobile_song_selected(self, song: Song, index: int) -> None:
        """Handles song selection from mobile library list."""
        self.play_queue.set_songs(self.mobile_view_widget._all_songs, start_index=index)
        self._play_song(song)

    @Slot(Song)
    def _on_delete_song_requested(self, song: Song) -> None:
        """Prompts the user to delete a song from the library catalog and optionally from storage."""
        if not song:
            return
        
        # 1. Ask for confirmation
        msg = QMessageBox(self)
        msg.setWindowTitle("Delete Song")
        msg.setText(f"How would you like to delete '{song.display_title}'?")
        msg.setInformativeText("Removing it from library will keep the file on disk.\nDeleting the file is permanent.")
        
        delete_file_btn = msg.addButton("Delete File", QMessageBox.ButtonRole.DestructiveRole)
        remove_lib_btn = msg.addButton("Remove from Library", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg.addButton(QMessageBox.StandardButton.Cancel)
        
        # Style the dialog to fit the dark theme QSS
        msg.setStyleSheet(self.styleSheet())
        
        msg.exec()
        clicked = msg.clickedButton()
        
        if clicked == cancel_btn:
            return
        
        filepath = song.filepath
        
        # If the song is currently playing, stop and unload it first to release any file lock
        current_song = self.audio_player.get_current_song()
        if current_song and current_song.filepath == filepath:
            self.audio_player.unload()
            self.player_controls.set_active_song(None)
            self.now_playing_panel.set_active_song(None)
            self.mobile_view_widget.set_active_song(None)
            self.statusBar().showMessage("Playback stopped as active song was deleted")
            
        # Delete file physically if requested
        if clicked == delete_file_btn:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f"Permanently deleted file from storage: {filepath}")
            except Exception as e:
                logger.error(f"Failed to delete physical file {filepath}: {e}", exc_info=True)
                QMessageBox.warning(self, "Error", f"Could not delete physical file: {e}\nRemoving from library catalog instead.")
        
        # Delete database entry
        MusicRepository.delete_song(filepath)
        
        # Remove from the queue
        self.play_queue.remove_song(filepath)
        
        # Refresh the UI lists
        all_songs = MusicRepository.get_all_songs()
        self.sidebar.set_library_count(len(all_songs))

        # Get updated songs for active view
        if self.song_list.active_playlist_id is not None:
            songs = MusicRepository.get_songs_by_playlist(self.song_list.active_playlist_id)
            self.song_list.set_view_data("tracks", songs)
            self.mobile_view_widget.set_songs(songs)
        elif self._current_view_favorites:
            songs = MusicRepository.get_favorites()
            self.song_list.set_view_data("tracks", songs)
            self.mobile_view_widget.set_songs(songs)
        elif self.song_list._view_type == "tracks":
            self.song_list.set_view_data("tracks", all_songs)
            self.mobile_view_widget.set_songs(all_songs)
        elif self.song_list._view_type == "albums":
            self._show_albums()
        elif self.song_list._view_type == "artists":
            self._show_artists()
        elif self.song_list._view_type == "folders":
            self.song_list.set_view_data("folders", MusicRepository.get_folders())
        elif self.song_list._view_type == "genres":
            self._show_genres()
            
        # Select the currently playing song in the list if still playing
        current = self.audio_player.get_current_song()
        if current:
            self.song_list.select_song_by_filepath(current.filepath)
            self.mobile_view_widget.set_active_song(current, self.player_controls.mini_art.pixmap())
        
        self.statusBar().showMessage(f"Deleted song: {song.display_title}")

    def resizeEvent(self, event) -> None:
        """Transitions between Desktop split-view and Mobile portrait view based on window width."""
        super().resizeEvent(event)
        if self.width() < 550:
            self.view_stack.setCurrentIndex(1)
        else:
            self.view_stack.setCurrentIndex(0)

    def closeEvent(self, event) -> None:
        """Clean up background threads on exit."""
        if self.active_scanner and self.active_scanner.isRunning():
            self.active_scanner.requestInterruption()
            self.active_scanner.wait()

        if self.active_artwork_loader and self.active_artwork_loader.isRunning():
            self.active_artwork_loader.terminate()
            self.active_artwork_loader.wait()

        self.settings["is_muted"] = self.audio_player.is_muted()
        ConfigService.save(self.settings)
        super().closeEvent(event)
