import os
import logging
from typing import List, Optional, Dict, Any
from music_player.models.song import Song
from music_player.database.connection import DbConnection

logger = logging.getLogger(__name__)

class MusicRepository:
    """
    Data Access Layer (Repository Pattern) for SQLite database operations.
    """

    @staticmethod
    def _row_to_song(row: Any) -> Song:
        """Helper to map an SQLite row dict to a Song object."""
        return Song(
            filepath=row['filepath'],
            title=row['title'],
            artist=row['artist'] or "Unknown Artist",
            album=row['album'] or "Unknown Album",
            duration=row['duration'] or 0.0,
            year=row['year'],
            genre=row['genre'],
            favorite=bool(row['favorite']),
            play_count=row['play_count'] or 0,
            artwork_data=None  # Artwork is loaded on demand from file to save memory
        )

    @classmethod
    def upsert_song(cls, song: Song) -> None:
        """Saves a song into database. Updates if filepath already exists."""
        conn = DbConnection.get_connection()
        cursor = conn.cursor()
        try:
            # Check if this filepath already exists (case-insensitive)
            cursor.execute("SELECT id FROM songs WHERE LOWER(filepath) = LOWER(?)", (song.filepath,))
            exists_filepath = cursor.fetchone()
            
            if not exists_filepath:
                # File path doesn't exist yet (this is a new import)
                filename = os.path.basename(song.filepath).lower()
                cursor.execute("SELECT filepath, title FROM songs")
                all_songs = cursor.fetchall()
                for row in all_songs:
                    row_filepath = row['filepath']
                    row_title = row['title']
                    
                    # Check duplicate filename (e.g. "song.mp3" == "song.mp3")
                    if os.path.basename(row_filepath).lower() == filename:
                        logger.info(f"Skipping duplicate song by filename: {song.filepath}")
                        return
                    
                    # Check duplicate metadata title
                    if song.title and row_title and song.title.strip().lower() == row_title.strip().lower():
                        logger.info(f"Skipping duplicate song by title: {song.filepath}")
                        return

            # 1. Add / Resolve Artist
            artist_id = None
            if song.artist:
                cursor.execute("INSERT OR IGNORE INTO artists (name) VALUES (?)", (song.artist,))
                cursor.execute("SELECT id FROM artists WHERE name = ?", (song.artist,))
                artist_row = cursor.fetchone()
                if artist_row:
                    artist_id = artist_row['id']

            # 2. Add / Resolve Album
            album_id = None
            if song.album:
                cursor.execute(
                    "INSERT OR IGNORE INTO albums (name, artist_id) VALUES (?, ?)", 
                    (song.album, artist_id)
                )
                cursor.execute(
                    "SELECT id FROM albums WHERE name = ? AND (artist_id = ? OR (artist_id IS NULL AND ? IS NULL))", 
                    (song.album, artist_id, artist_id)
                )
                album_row = cursor.fetchone()
                if album_row:
                    album_id = album_row['id']

            # 3. Upsert Song record
            cursor.execute("""
                INSERT INTO songs (filepath, title, artist_id, album_id, duration, year, genre)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(filepath) DO UPDATE SET
                    title = excluded.title,
                    artist_id = excluded.artist_id,
                    album_id = excluded.album_id,
                    duration = excluded.duration,
                    year = excluded.year,
                    genre = excluded.genre
            """, (
                song.filepath,
                song.title,
                artist_id,
                album_id,
                song.duration,
                song.year,
                song.genre
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error upserting song in database {song.filepath}: {e}", exc_info=True)
        finally:
            conn.close()

    @classmethod
    def get_all_songs(cls) -> List[Song]:
        """Returns all songs in the library sorted by title."""
        conn = DbConnection.get_connection()
        songs: List[Song] = []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, ar.name as artist, al.name as album
                FROM songs s
                LEFT JOIN artists ar ON s.artist_id = ar.id
                LEFT JOIN albums al ON s.album_id = al.id
                ORDER BY s.title COLLATE NOCASE ASC
            """)
            rows = cursor.fetchall()
            for row in rows:
                songs.append(cls._row_to_song(row))
        except Exception as e:
            logger.error(f"Error fetching songs from database: {e}", exc_info=True)
        finally:
            conn.close()
        return songs

    @classmethod
    def update_song_metadata(cls, filepath: str, title: str, artist: str, album: str, genre: str) -> None:
        """Updates the metadata (title, artist, album, genre) of a song in the database."""
        conn = DbConnection.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Resolve/Add Artist
            artist_id = None
            if artist:
                cursor.execute("INSERT OR IGNORE INTO artists (name) VALUES (?)", (artist,))
                cursor.execute("SELECT id FROM artists WHERE name = ?", (artist,))
                artist_row = cursor.fetchone()
                if artist_row:
                    artist_id = artist_row['id']

            # 2. Resolve/Add Album
            album_id = None
            if album:
                cursor.execute(
                    "INSERT OR IGNORE INTO albums (name, artist_id) VALUES (?, ?)", 
                    (album, artist_id)
                )
                cursor.execute(
                    "SELECT id FROM albums WHERE name = ? AND (artist_id = ? OR (artist_id IS NULL AND ? IS NULL))", 
                    (album, artist_id, artist_id)
                )
                album_row = cursor.fetchone()
                if album_row:
                    album_id = album_row['id']

            # 3. Update Song
            cursor.execute("""
                UPDATE songs
                SET title = ?, artist_id = ?, album_id = ?, genre = ?
                WHERE filepath = ?
            """, (title, artist_id, album_id, genre, filepath))
            
            conn.commit()
            logger.info(f"Updated metadata in DB for {filepath}: {title} - {artist} - {album} - {genre}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating metadata in database for {filepath}: {e}", exc_info=True)
        finally:
            conn.close()

    @classmethod
    def update_song_duration(cls, filepath: str, duration: float) -> None:
        """Updates the duration of a song in the database."""
        conn = DbConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE songs SET duration = ? WHERE filepath = ?", (duration, filepath))
            conn.commit()
            logger.info(f"Updated duration in DB for {filepath} to {duration}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating duration in database for {filepath}: {e}")
        finally:
            conn.close()

    @classmethod
    def update_favorite(cls, filepath: str, is_favorite: bool) -> None:
        """Sets favorite status (0 or 1) for a song."""
        conn = DbConnection.get_connection()
        cursor = conn.cursor()
        try:
            val = 1 if is_favorite else 0
            cursor.execute("UPDATE songs SET favorite = ? WHERE filepath = ?", (val, filepath))
            conn.commit()
            logger.info(f"Updated favorite status for {filepath} to {is_favorite}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating favorite in database for {filepath}: {e}")
        finally:
            conn.close()

    @classmethod
    def increment_play_count(cls, filepath: str) -> None:
        """Increments play count and updates last played timestamp."""
        conn = DbConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE songs 
                SET play_count = play_count + 1, 
                    last_played = datetime('now', 'localtime') 
                WHERE filepath = ?
            """, (filepath,))
            
            # Get song ID to log in recent_plays
            cursor.execute("SELECT id FROM songs WHERE filepath = ?", (filepath,))
            row = cursor.fetchone()
            if row:
                song_id = row['id']
                cursor.execute("INSERT INTO recent_plays (song_id) VALUES (?)", (song_id,))
                
            conn.commit()
            logger.info(f"Incremented play count for {filepath}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error incrementing play count for {filepath}: {e}")
        finally:
            conn.close()

    @classmethod
    def get_favorites(cls) -> List[Song]:
        """Returns all favorited songs."""
        conn = DbConnection.get_connection()
        songs: List[Song] = []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, ar.name as artist, al.name as album
                FROM songs s
                LEFT JOIN artists ar ON s.artist_id = ar.id
                LEFT JOIN albums al ON s.album_id = al.id
                WHERE s.favorite = 1
                ORDER BY s.title COLLATE NOCASE ASC
            """)
            rows = cursor.fetchall()
            for row in rows:
                songs.append(cls._row_to_song(row))
        except Exception as e:
            logger.error(f"Error fetching favorites: {e}", exc_info=True)
        finally:
            conn.close()
        return songs

    # --- Lyrics Cache Methods ---

    @classmethod
    def get_cached_lyrics(cls, artist: str, title: str) -> Optional[str]:
        """Returns cached lyrics from DB if they exist."""
        conn = DbConnection.get_connection()
        lyrics: Optional[str] = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT lyrics FROM lyrics_cache WHERE LOWER(artist) = LOWER(?) AND LOWER(title) = LOWER(?)",
                (artist, title)
            )
            row = cursor.fetchone()
            if row:
                lyrics = row['lyrics']
        except Exception as e:
            logger.error(f"Error fetching cached lyrics from DB: {e}")
        finally:
            conn.close()
        return lyrics

    @classmethod
    def cache_lyrics(cls, artist: str, title: str, lyrics: str) -> None:
        """Stores downloaded lyrics in the database cache."""
        conn = DbConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO lyrics_cache (artist, title, lyrics)
                VALUES (?, ?, ?)
            """, (artist, title, lyrics))
            conn.commit()
            logger.info(f"Cached lyrics in DB for: {artist} - {title}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error caching lyrics in DB: {e}")
        finally:
            conn.close()

    # --- Folder & Grouping Methods ---

    @classmethod
    def add_folder(cls, path: str) -> None:
        """Saves a unique folder path into the database, normalized to forward slashes."""
        conn = DbConnection.get_connection()
        cursor = conn.cursor()
        try:
            path_norm = path.replace('\\', '/')
            cursor.execute("INSERT OR IGNORE INTO folders (path) VALUES (?)", (path_norm,))
            conn.commit()
            logger.info(f"Added folder path to SQLite: {path_norm}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to add folder path {path}: {e}")
        finally:
            conn.close()

    @classmethod
    def get_all_folders(cls) -> List[Dict[str, Any]]:
        """Returns a list of all normalized folder paths."""
        conn = DbConnection.get_connection()
        folders = []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, path FROM folders ORDER BY path ASC")
            rows = cursor.fetchall()
            for row in rows:
                folders.append(dict(row))
        except Exception as e:
            logger.error(f"Error getting folders: {e}")
        finally:
            conn.close()
        return folders

    @classmethod
    def get_folders(cls) -> List[Dict[str, Any]]:
        """Returns folders list with calculated track counts."""
        conn = DbConnection.get_connection()
        folders = []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, path FROM folders ORDER BY path ASC")
            folder_rows = cursor.fetchall()
            for row in folder_rows:
                folder_path = row['path'].replace('\\', '/')
                # Get song count under this folder path
                cursor.execute("SELECT COUNT(id) as track_count FROM songs WHERE filepath LIKE ?", (folder_path + '%',))
                count_row = cursor.fetchone()
                track_count = count_row['track_count'] if count_row else 0
                folders.append({
                    'id': row['id'],
                    'path': row['path'],
                    'track_count': track_count
                })
        except Exception as e:
            logger.error(f"Error getting folders: {e}")
        finally:
            conn.close()
        return folders

    @classmethod
    def delete_folder(cls, path: str) -> None:
        """Deletes folder from DB and purges all tracks belonging to it."""
        conn = DbConnection.get_connection()
        cursor = conn.cursor()
        try:
            path_norm = path.replace('\\', '/')
            cursor.execute("DELETE FROM folders WHERE path = ?", (path_norm,))
            # Delete corresponding songs
            cursor.execute("DELETE FROM songs WHERE filepath LIKE ?", (path_norm + '%',))
            conn.commit()
            logger.info(f"Deleted folder {path_norm} and purged its songs from DB.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting folder {path}: {e}")
        finally:
            conn.close()

    @classmethod
    def clean_missing_songs(cls, folder_path: str) -> None:
        """Deletes database records for songs under folder_path that no longer exist on disk."""
        conn = DbConnection.get_connection()
        cursor = conn.cursor()
        try:
            folder_path = folder_path.replace('\\', '/')
            cursor.execute("SELECT filepath FROM songs WHERE filepath LIKE ?", (folder_path + '%',))
            rows = cursor.fetchall()
            to_delete = []
            for row in rows:
                if not os.path.exists(row['filepath']):
                    to_delete.append(row['filepath'])
            
            if to_delete:
                cursor.executemany("DELETE FROM songs WHERE filepath = ?", [(path,) for path in to_delete])
                conn.commit()
                logger.info(f"Cleaned {len(to_delete)} missing songs from database under {folder_path}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error cleaning missing songs: {e}")
        finally:
            conn.close()

    @classmethod
    def get_albums(cls) -> List[Dict[str, Any]]:
        """Returns all albums with artist names and song counts."""
        conn = DbConnection.get_connection()
        albums = []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT al.name as album, ar.name as artist, COUNT(s.id) as track_count
                FROM albums al
                LEFT JOIN artists ar ON al.artist_id = ar.id
                JOIN songs s ON s.album_id = al.id
                GROUP BY al.id
                ORDER BY al.name COLLATE NOCASE ASC
            """)
            rows = cursor.fetchall()
            for row in rows:
                albums.append(dict(row))
        except Exception as e:
            logger.error(f"Error getting albums: {e}")
        finally:
            conn.close()
        return albums

    @classmethod
    def get_artists(cls) -> List[Dict[str, Any]]:
        """Returns all artists with corresponding song counts."""
        conn = DbConnection.get_connection()
        artists = []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ar.name as artist, COUNT(s.id) as track_count
                FROM artists ar
                JOIN songs s ON s.artist_id = ar.id
                GROUP BY ar.id
                ORDER BY ar.name COLLATE NOCASE ASC
            """)
            rows = cursor.fetchall()
            for row in rows:
                artists.append(dict(row))
        except Exception as e:
            logger.error(f"Error getting artists: {e}")
        finally:
            conn.close()
        return artists

    @classmethod
    def get_songs_by_album(cls, album_name: str) -> List[Song]:
        """Returns all songs belonging to a specific album name."""
        conn = DbConnection.get_connection()
        songs: List[Song] = []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, ar.name as artist, al.name as album
                FROM songs s
                LEFT JOIN artists ar ON s.artist_id = ar.id
                JOIN albums al ON s.album_id = al.id
                WHERE al.name = ?
                ORDER BY s.title COLLATE NOCASE ASC
            """, (album_name,))
            rows = cursor.fetchall()
            for row in rows:
                songs.append(cls._row_to_song(row))
        except Exception as e:
            logger.error(f"Error getting songs by album {album_name}: {e}")
        finally:
            conn.close()
        return songs

    @classmethod
    def get_songs_by_artist(cls, artist_name: str) -> List[Song]:
        """Returns all songs belonging to a specific artist name."""
        conn = DbConnection.get_connection()
        songs: List[Song] = []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, ar.name as artist, al.name as album
                FROM songs s
                JOIN artists ar ON s.artist_id = ar.id
                LEFT JOIN albums al ON s.album_id = al.id
                WHERE ar.name = ?
                ORDER BY s.title COLLATE NOCASE ASC
            """, (artist_name,))
            rows = cursor.fetchall()
            for row in rows:
                songs.append(cls._row_to_song(row))
        except Exception as e:
            logger.error(f"Error getting songs by artist {artist_name}: {e}")
        finally:
            conn.close()
        return songs

    @classmethod
    def get_songs_by_folder(cls, folder_path: str) -> List[Song]:
        """Returns all songs under a folder path."""
        conn = DbConnection.get_connection()
        songs: List[Song] = []
        try:
            folder_path = folder_path.replace('\\', '/')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, ar.name as artist, al.name as album
                FROM songs s
                LEFT JOIN artists ar ON s.artist_id = ar.id
                LEFT JOIN albums al ON s.album_id = al.id
                WHERE s.filepath LIKE ?
                ORDER BY s.title COLLATE NOCASE ASC
            """, (folder_path + '%',))
            rows = cursor.fetchall()
            for row in rows:
                songs.append(cls._row_to_song(row))
        except Exception as e:
            logger.error(f"Error getting songs by folder {folder_path}: {e}")
        finally:
            conn.close()
        return songs

    @classmethod
    def create_playlist(cls, name: str) -> Optional[int]:
        """Creates a new playlist and returns its ID."""
        conn = DbConnection.get_connection()
        cursor = conn.cursor()
        playlist_id = None
        try:
            cursor.execute("INSERT INTO playlists (name) VALUES (?)", (name,))
            conn.commit()
            playlist_id = cursor.lastrowid
            logger.info(f"Created playlist: {name} with ID {playlist_id}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating playlist {name}: {e}")
        finally:
            conn.close()
        return playlist_id

    @classmethod
    def delete_playlist(cls, playlist_id: int) -> None:
        """Deletes a playlist by its ID."""
        conn = DbConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
            conn.commit()
            logger.info(f"Deleted playlist ID {playlist_id}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting playlist ID {playlist_id}: {e}")
        finally:
            conn.close()

    @classmethod
    def get_playlists(cls) -> List[Dict[str, Any]]:
        """Returns all playlists with track counts."""
        conn = DbConnection.get_connection()
        playlists = []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.name, COUNT(ps.song_id) as track_count
                FROM playlists p
                LEFT JOIN playlist_songs ps ON p.id = ps.playlist_id
                GROUP BY p.id
                ORDER BY p.name COLLATE NOCASE ASC
            """)
            rows = cursor.fetchall()
            playlists = [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting playlists: {e}")
        finally:
            conn.close()
        return playlists

    @classmethod
    def add_song_to_playlist(cls, song_filepath: str, playlist_id: int) -> bool:
        """Adds a song to a playlist. Returns True if successful."""
        conn = DbConnection.get_connection()
        cursor = conn.cursor()
        try:
            # Get song ID
            cursor.execute("SELECT id FROM songs WHERE filepath = ?", (song_filepath,))
            song_row = cursor.fetchone()
            if not song_row:
                return False
            song_id = song_row['id']

            # Get current max position
            cursor.execute("SELECT IFNULL(MAX(position), 0) as max_pos FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
            pos_row = cursor.fetchone()
            next_pos = (pos_row['max_pos'] if pos_row else 0) + 1

            cursor.execute("""
                INSERT OR IGNORE INTO playlist_songs (playlist_id, song_id, position)
                VALUES (?, ?, ?)
            """, (playlist_id, song_id, next_pos))
            conn.commit()
            logger.info(f"Added song ID {song_id} to playlist ID {playlist_id}")
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding song {song_filepath} to playlist ID {playlist_id}: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    def remove_song_from_playlist(cls, song_filepath: str, playlist_id: int) -> None:
        """Removes a song from a playlist."""
        conn = DbConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM songs WHERE filepath = ?", (song_filepath,))
            song_row = cursor.fetchone()
            if not song_row:
                return
            song_id = song_row['id']

            cursor.execute("DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?", (playlist_id, song_id))
            conn.commit()
            logger.info(f"Removed song ID {song_id} from playlist ID {playlist_id}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error removing song {song_filepath} from playlist ID {playlist_id}: {e}")
        finally:
            conn.close()

    @classmethod
    def get_songs_by_playlist(cls, playlist_id: int) -> List[Song]:
        """Returns all songs in a playlist sorted by position."""
        conn = DbConnection.get_connection()
        songs: List[Song] = []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, ar.name as artist, al.name as album
                FROM songs s
                JOIN playlist_songs ps ON s.id = ps.song_id
                LEFT JOIN artists ar ON s.artist_id = ar.id
                LEFT JOIN albums al ON s.album_id = al.id
                WHERE ps.playlist_id = ?
                ORDER BY ps.position ASC
            """, (playlist_id,))
            rows = cursor.fetchall()
            for row in rows:
                songs.append(cls._row_to_song(row))
        except Exception as e:
            logger.error(f"Error getting songs by playlist ID {playlist_id}: {e}")
        finally:
            conn.close()
        return songs

    @classmethod
    def get_all_genres(cls) -> List[str]:
        """Returns a list of all distinct genres in the library."""
        conn = DbConnection.get_connection()
        genres = []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT genre 
                FROM songs 
                WHERE genre IS NOT NULL AND genre != '' 
                ORDER BY genre COLLATE NOCASE ASC
            """)
            rows = cursor.fetchall()
            genres = [row['genre'] for row in rows]
        except Exception as e:
            logger.error(f"Error fetching genres: {e}")
        finally:
            conn.close()
        return genres
