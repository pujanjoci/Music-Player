import sys
import logging
from PySide6.QtWidgets import QApplication
from music_player.database.connection import DbConnection
from music_player.ui.main_window import MainWindow

def setup_logging() -> None:
    """Configures application-wide logging formats and outputs."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main() -> None:
    """Application main entry point."""
    setup_logging()
    logger = logging.getLogger("music_player")
    logger.info("Initializing Music Player (Offline)...")

    # Initialize SQLite Database
    try:
        DbConnection.initialize()
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("Music Player (Offline)")
    app.setOrganizationName("MusicPlayer")
    
    # Create and display the main window
    window = MainWindow()
    window.show()

    logger.info("App loaded. Starting event loop.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
