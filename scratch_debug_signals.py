import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QObject

class SignalDebugger(QObject):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.player.positionChanged.connect(self.on_position)
        self.player.durationChanged.connect(self.on_duration)
        self.player.playbackStateChanged.connect(self.on_state)
        self.player.mediaStatusChanged.connect(self.on_status)
        self.player.errorOccurred.connect(self.on_error)
        
    def on_position(self, pos):
        print(f"[SIGNAL] positionChanged({pos}) | player.position()={self.player.position()} | player.duration()={self.player.duration()} | state={self.player.playbackState()} | status={self.player.mediaStatus()}")
        
    def on_duration(self, dur):
        print(f"[SIGNAL] durationChanged({dur}) | player.position()={self.player.position()} | player.duration()={self.player.duration()} | state={self.player.playbackState()} | status={self.player.mediaStatus()}")
        
    def on_state(self, state):
        print(f"[SIGNAL] playbackStateChanged({state}) | player.position()={self.player.position()} | player.duration()={self.player.duration()} | state={self.player.playbackState()} | status={self.player.mediaStatus()}")
        
    def on_status(self, status):
        print(f"[SIGNAL] mediaStatusChanged({status}) | player.position()={self.player.position()} | player.duration()={self.player.duration()} | state={self.player.playbackState()} | status={self.player.mediaStatus()}")
        
    def on_error(self, err, err_str):
        print(f"[SIGNAL] errorOccurred({err}, {err_str})")

def main():
    app = QApplication(sys.argv)
    
    from music_player.database.connection import DbConnection
    from music_player.database.repository import MusicRepository
    DbConnection.initialize()
    songs = MusicRepository.get_all_songs()
    if len(songs) < 2:
        print("Need at least 2 songs")
        return
        
    song1 = songs[0]
    song2 = songs[1]
    
    player = QMediaPlayer()
    audio_output = QAudioOutput()
    player.setAudioOutput(audio_output)
    
    debugger = SignalDebugger(player)
    
    print("\n--- Play Song 1 ---")
    player.setSource(QUrl.fromLocalFile(song1.filepath))
    player.play()
    
    # Process events for 1 second
    start = time.time()
    while time.time() - start < 1.0:
        app.processEvents()
        time.sleep(0.01)
        
    print("\n--- Switch to Song 2 ---")
    # Simulate our play_song logic:
    # 1. stop()
    # 2. setSource()
    # 3. play()
    player.stop()
    player.setSource(QUrl.fromLocalFile(song2.filepath))
    player.play()
    
    # Process events for 2 seconds
    start = time.time()
    while time.time() - start < 2.0:
        app.processEvents()
        time.sleep(0.01)
        
    print("\n--- Done ---")

if __name__ == "__main__":
    main()
