import os
import sqlite3
import logging
from typing import Generator

logger = logging.getLogger(__name__)

DB_DIR = os.path.join(os.path.expanduser("~"), ".antigravity_music_player")
DB_PATH = os.path.join(DB_DIR, "music_player.db")

class DbConnection:
    """
    Manages SQLite database connections and runs migrations.
    """
    @staticmethod
    def initialize() -> None:
        """Creates the database directory and tables if they do not exist."""
        try:
            os.makedirs(DB_DIR, exist_ok=True)
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON;")

            # 1. Artists Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS artists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                );
            """)

            # 2. Albums Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS albums (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    artist_id INTEGER,
                    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
                    UNIQUE(name, artist_id)
                );
            """)

            # 3. Songs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filepath TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    artist_id INTEGER,
                    album_id INTEGER,
                    duration REAL DEFAULT 0.0,
                    year TEXT,
                    genre TEXT,
                    favorite INTEGER DEFAULT 0 CHECK(favorite IN (0, 1)),
                    play_count INTEGER DEFAULT 0,
                    last_played TEXT,
                    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE SET NULL,
                    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE SET NULL
                );
            """)

            # 4. Playlists Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 5. Playlist Songs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlist_songs (
                    playlist_id INTEGER,
                    song_id INTEGER,
                    position INTEGER,
                    PRIMARY KEY (playlist_id, song_id),
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
                    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
                );
            """)

            # 6. Lyrics Cache Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lyrics_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artist TEXT NOT NULL,
                    title TEXT NOT NULL,
                    lyrics TEXT NOT NULL,
                    cached_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(artist, title)
                );
            """)

            # 7. Recent Plays Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recent_plays (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    song_id INTEGER,
                    played_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
                );
            """)

            # 8. Folders Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    added_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Run normalization and duplicate cleanup migration on startup
            cursor.execute("SELECT id, filepath, title FROM songs ORDER BY id ASC")
            songs = cursor.fetchall()
            seen_filenames = set()
            seen_titles = set()
            songs_to_delete = []
            for song in songs:
                fp = song['filepath']
                title = song['title']
                filename = os.path.basename(fp).lower()
                
                # Normalize filepath first
                norm_fp = fp.replace('\\', '/')
                if fp != norm_fp:
                    # Check if norm_fp already exists in database
                    cursor.execute("SELECT id FROM songs WHERE filepath = ?", (norm_fp,))
                    dup = cursor.fetchone()
                    if dup:
                        songs_to_delete.append(song['id'])
                        continue
                    else:
                        cursor.execute("UPDATE songs SET filepath = ? WHERE id = ?", (norm_fp, song['id']))
                        fp = norm_fp
                
                # Check duplicates by filename
                if filename in seen_filenames:
                    songs_to_delete.append(song['id'])
                    continue
                
                # Check duplicates by title
                norm_title = title.strip().lower() if title else ""
                if norm_title and norm_title in seen_titles:
                    songs_to_delete.append(song['id'])
                    continue
                    
                seen_filenames.add(filename)
                if norm_title:
                    seen_titles.add(norm_title)
                    
            if songs_to_delete:
                cursor.executemany("DELETE FROM songs WHERE id = ?", [(sid,) for sid in songs_to_delete])

            # Normalize folders path
            cursor.execute("SELECT id, path FROM folders ORDER BY id ASC")
            folders = cursor.fetchall()
            seen_folders = set()
            folders_to_delete = []
            for folder in folders:
                p = folder['path']
                norm_p = p.replace('\\', '/').rstrip('/')
                if p != norm_p:
                    # Check if norm_p already exists
                    cursor.execute("SELECT id FROM folders WHERE path = ?", (norm_p,))
                    dup = cursor.fetchone()
                    if dup:
                        folders_to_delete.append(folder['id'])
                        continue
                    else:
                        cursor.execute("UPDATE folders SET path = ? WHERE id = ?", (norm_p, folder['id']))
                        p = norm_p
                
                norm_p_lower = p.lower()
                if norm_p_lower in seen_folders:
                    folders_to_delete.append(folder['id'])
                else:
                    seen_folders.add(norm_p_lower)
                    
            if folders_to_delete:
                cursor.executemany("DELETE FROM folders WHERE id = ?", [(fid,) for fid in folders_to_delete])

            conn.commit()
            conn.close()
            logger.info("Database initialized and migrated successfully.")
        except Exception as e:
            logger.critical(f"Failed to initialize database: {e}", exc_info=True)
            raise

    @staticmethod
    def get_connection() -> sqlite3.Connection:
        """Returns a new sqlite3 connection with foreign keys enabled."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Access columns by name
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
