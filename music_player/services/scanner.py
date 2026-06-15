import os
import logging
from typing import List, Set
from PySide6.QtCore import QThread, Signal
from music_player.models.song import Song
from music_player.services.metadata import MetadataService

logger = logging.getLogger(__name__)

class LibraryScanner(QThread):
    """
    QThread to scan directories recursively for audio files and extract metadata.
    Avoids blocking the GUI thread.
    """
    song_found = Signal(Song)
    scan_progress = Signal(str)
    scan_finished = Signal(list)  # Emits list of all Song objects found

    def __init__(self, directory_path: str) -> None:
        super().__init__()
        self.directory_path = directory_path
        self.supported_formats: Set[str] = {'.mp3', '.flac', '.wav', '.ogg', '.m4a'}

    def run(self) -> None:
        """Core execution loop of the scanner thread."""
        logger.info(f"Starting library scan for folder: {self.directory_path}")
        songs: List[Song] = []

        if not os.path.exists(self.directory_path) or not os.path.isdir(self.directory_path):
            logger.error(f"Invalid directory path: {self.directory_path}")
            self.scan_progress.emit("Invalid directory path.")
            self.scan_finished.emit(songs)
            return

        try:
            for root, _, files in os.walk(self.directory_path):
                # Check for thread cancellation
                if self.isInterruptionRequested():
                    logger.info("Scan cancelled by user.")
                    self.scan_progress.emit("Scan cancelled.")
                    break

                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in self.supported_formats:
                        filepath = os.path.join(root, file).replace('\\', '/')
                        self.scan_progress.emit(f"Scanning: {file}")
                        
                        try:
                            # Extract metadata (handles exceptions internally)
                            song = MetadataService.extract_metadata(filepath)
                            songs.append(song)
                            self.song_found.emit(song)
                        except Exception as e:
                            logger.error(f"Error scanning file {filepath}: {e}")

            logger.info(f"Scan finished. Found {len(songs)} songs.")
            self.scan_progress.emit(f"Scan complete. Found {len(songs)} songs.")
            self.scan_finished.emit(songs)
            
        except Exception as e:
            logger.critical(f"Critical error during scanning: {e}", exc_info=True)
            self.scan_progress.emit("An error occurred during scanning.")
            self.scan_finished.emit(songs)
