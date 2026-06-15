import os
import logging
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QObject, Signal, QUrl, QTimer
from music_player.models.song import Song

logger = logging.getLogger(__name__)


class AudioPlayer(QObject):
    """
    Service wrapping Qt Multimedia (QMediaPlayer, QAudioOutput) to manage song playback.
    """
    position_changed = Signal(int)   # Current position in milliseconds
    duration_changed = Signal(int)   # Total duration in milliseconds
    state_changed = Signal(QMediaPlayer.PlaybackState)
    song_finished = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)

        # Connect player signals
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_state_changed)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._player.errorOccurred.connect(self._on_error_occurred)

        self._current_song: Song | None = None
        self._target_filepath: str = ""
        self._is_switching = False  # True while we are switching songs
        self._volume = 70
        self._is_muted = False

        # Initialize default volume
        self.set_volume(self._volume)

    def play_song(self, song: Song) -> None:
        """Loads the given song and starts playback once it's loaded."""
        try:
            self._is_switching = True
            self._current_song = song
            self._target_filepath = song.filepath

            # Set source to the new song. This automatically stops any active playback.
            url = QUrl.fromLocalFile(song.filepath)
            self._player.setSource(url)

            logger.info(f"Loading song source: {song.filepath}")
        except Exception as e:
            self._is_switching = False
            logger.error(f"Failed to play song {song.filepath}: {e}", exc_info=True)

    def play(self) -> None:
        """Resumes playback if paused or stopped."""
        self._player.play()

    def pause(self) -> None:
        """Pauses playback."""
        self._player.pause()

    def stop(self) -> None:
        """Stops playback."""
        self._player.stop()

    def get_state(self) -> QMediaPlayer.PlaybackState:
        """Returns the current playback state."""
        return self._player.playbackState()

    def set_position(self, position_ms: int) -> None:
        """Seeks to a position in milliseconds."""
        self._player.setPosition(position_ms)

    def get_position(self) -> int:
        """Gets current position in milliseconds."""
        return self._player.position()

    def get_duration(self) -> int:
        """Gets current media duration in milliseconds."""
        return self._player.duration()

    def set_volume(self, volume: int) -> None:
        """Sets playback volume (0 - 100)."""
        self._volume = max(0, min(100, volume))
        if not self._is_muted:
            self._audio_output.setVolume(self._volume / 100.0)

    def get_volume(self) -> int:
        """Gets playback volume (0 - 100)."""
        return self._volume

    def set_muted(self, is_muted: bool) -> None:
        """Mutes or unmutes the audio output."""
        self._is_muted = is_muted
        self._audio_output.setMuted(is_muted)

    def is_muted(self) -> bool:
        """Checks if audio output is muted."""
        return self._is_muted

    def get_current_song(self) -> Song | None:
        """Returns the currently loaded song."""
        return self._current_song

    def _on_position_changed(self, position: int) -> None:
        if not self._is_switching:
            self.position_changed.emit(position)

    def _on_duration_changed(self, duration: int) -> None:
        if not self._is_switching:
            self.duration_changed.emit(duration)

    def _on_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        if not self._is_switching:
            self.state_changed.emit(state)

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if self._is_switching:
            current_source = self._player.source().toLocalFile()
            if current_source and os.path.normpath(current_source).lower() == os.path.normpath(self._target_filepath).lower():
                # We are switching songs; wait for media to reach a playable state.
                if status in (
                    QMediaPlayer.MediaStatus.LoadedMedia,
                    QMediaPlayer.MediaStatus.BufferedMedia,
                    QMediaPlayer.MediaStatus.InvalidMedia,
                ):
                    self._is_switching = False
                    logger.info(f"Song loaded. Status: {status}")

                    # Play the song if it loaded successfully
                    if status != QMediaPlayer.MediaStatus.InvalidMedia:
                        self._player.play()

                    # Sync the slider range for the new song.
                    dur = self._player.duration()
                    if dur > 0:
                        self.duration_changed.emit(dur)

                    # Reset the slider to the beginning of the new song.
                    self.position_changed.emit(0)
            return

        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            logger.info("End of media reached, emitting song_finished.")
            self.song_finished.emit()

    def _on_error_occurred(self, error: QMediaPlayer.Error, error_string: str) -> None:
        logger.error(f"QMediaPlayer error occurred: {error} - {error_string}")
        self._is_switching = False


