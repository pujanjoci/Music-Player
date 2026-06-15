import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QObject

class LoadPlayDebugger(QObject):
    def __init__(self, player, filepath):
        super().__init__()
        self.player = player
        self.filepath = filepath
        self.player.positionChanged.connect(self.on_position)
        self.player.durationChanged.connect(self.on_duration)
        self.player.playbackStateChanged.connect(self.on_state)
        self.player.mediaStatusChanged.connect(self.on_status)
        
    def on_position(self, pos):
        print(f"[SIGNAL] positionChanged({pos}) | state={self.player.playbackState()} | status={self.player.mediaStatus()}")
        
    def on_duration(self, dur):
        print(f"[SIGNAL] durationChanged({dur}) | state={self.player.playbackState()} | status={self.player.mediaStatus()}")
        
    def on_state(self, state):
        print(f"[SIGNAL] playbackStateChanged({state}) | state={self.player.playbackState()} | status={self.player.mediaStatus()}")
        
    def on_status(self, status):
        print(f"[SIGNAL] mediaStatusChanged({status}) | state={self.player.playbackState()} | status={self.player.mediaStatus()}")
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            print("--- LoadedMedia reached, calling play() ---")
            self.player.play()

def main():
    app = QApplication(sys.argv)
    
    from music_player.database.connection import DbConnection
    from music_player.database.repository import MusicRepository
    DbConnection.initialize()
    songs = MusicRepository.get_all_songs()
    if not songs:
        return
        
    song = songs[0]
    player = QMediaPlayer()
    audio_output = QAudioOutput()
    player.setAudioOutput(audio_output)
    
    debugger = LoadPlayDebugger(player, song.filepath)
    
    print("\n--- Setting Source (without calling play() immediately) ---")
    player.setSource(QUrl.fromLocalFile(song.filepath))
    
    # Process events for 3 seconds
    start = time.time()
    while time.time() - start < 3.0:
        app.processEvents()
        time.sleep(0.01)
        
    print("\n--- Done ---")

if __name__ == "__main__":
    main()
