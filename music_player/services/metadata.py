import os
import logging
from typing import Optional, Tuple
from music_player.models.song import Song

logger = logging.getLogger(__name__)

# Try to import mutagen components
try:
    import mutagen
    from mutagen.mp3 import MP3
    from mutagen.easyid3 import EasyID3
    from mutagen.id3 import ID3, APIC
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    logger.warning("Mutagen is not available. Metadata extraction will fall back to file names.")

class MetadataService:
    """
    Extracts audio metadata and album artwork from local music files.
    """

    @staticmethod
    def extract_metadata(filepath: str) -> Song:
        """
        Reads tags and returns a Song instance. Falls back to filename if reading fails.
        """
        filepath = filepath.replace('\\', '/')
        filename_title = os.path.splitext(os.path.basename(filepath))[0]
        
        # Default fallback values
        title = filename_title
        artist = "Unknown Artist"
        album = "Unknown Album"
        duration = 0.0
        year = None
        genre = None
        artwork_data = None

        if not MUTAGEN_AVAILABLE:
            return Song(filepath=filepath, title=title, artist=artist, album=album, duration=duration)

        try:
            # 1. Use general mutagen.File to identify the container format dynamically
            audio = mutagen.File(filepath)
            
            if audio is not None:
                if audio.info is not None:
                    duration = audio.info.length
                
                # Check actual class types to parse tags correctly
                if isinstance(audio, MP3):
                    # Try reading metadata tags using EasyID3
                    try:
                        easy_tags = EasyID3(filepath)
                        title = easy_tags.get('title', [filename_title])[0]
                        artist = easy_tags.get('artist', ["Unknown Artist"])[0]
                        album = easy_tags.get('album', ["Unknown Album"])[0]
                        year = easy_tags.get('date', [None])[0]
                        genre = easy_tags.get('genre', [None])[0]
                    except Exception:
                        # Fallback to standard ID3 if EasyID3 fails
                        try:
                            id3_tags = ID3(filepath)
                            title = id3_tags.get('TIT2', [filename_title])[0]
                            artist = id3_tags.get('TPE1', ["Unknown Artist"])[0]
                            album = id3_tags.get('TALB', ["Unknown Album"])[0]
                            year = id3_tags.get('TDRC', [None])[0]
                            genre = id3_tags.get('TCON', [None])[0]
                        except Exception:
                            pass
                    
                    # Read Artwork
                    try:
                        id3 = ID3(filepath)
                        for key in id3.keys():
                            if key.startswith('APIC'):
                                artwork_data = id3[key].data
                                break
                    except Exception:
                        pass

                elif isinstance(audio, FLAC):
                    title = audio.get('title', [filename_title])[0]
                    artist = audio.get('artist', ["Unknown Artist"])[0]
                    album = audio.get('album', ["Unknown Album"])[0]
                    year = audio.get('date', [None])[0]
                    genre = audio.get('genre', [None])[0]
                    
                    # FLAC artwork
                    if audio.pictures:
                        artwork_data = audio.pictures[0].data

                elif isinstance(audio, OggVorbis):
                    title = audio.get('title', [filename_title])[0]
                    artist = audio.get('artist', ["Unknown Artist"])[0]
                    album = audio.get('album', ["Unknown Album"])[0]
                    year = audio.get('date', [None])[0]
                    genre = audio.get('genre', [None])[0]
                    
                    # Check for metadata cover art
                    for tag in audio.keys():
                        if tag.lower() == 'metadata_block_picture':
                            try:
                                from mutagen.flac import Picture
                                import base64
                                pic_data = base64.b64decode(audio[tag][0])
                                picture = Picture(pic_data)
                                artwork_data = picture.data
                            except Exception:
                                pass
                            break

                elif isinstance(audio, MP4):
                    title = audio.get('\xa9nam', [filename_title])[0]
                    artist = audio.get('\xa9ART', ["Unknown Artist"])[0]
                    album = audio.get('\xa9alb', ["Unknown Album"])[0]
                    year = audio.get('\xa9day', [None])[0]
                    genre = audio.get('\xa9gen', [None])[0]
                    
                    # MP4 artwork
                    covr = audio.get('covr')
                    if covr:
                        artwork_data = covr[0]  # Usually is bytes

                else:
                    # General fallback for WAV or unrecognized formats
                    title = audio.get('title', [filename_title])[0]
                    artist = audio.get('artist', ["Unknown Artist"])[0]
                    album = audio.get('album', ["Unknown Album"])[0]

            else:
                # If mutagen.File fails (e.g. returns None), try fallback based on file extension
                ext = os.path.splitext(filepath)[1].lower()
                if ext == '.mp3':
                    try:
                        audio_fallback = MP3(filepath)
                        duration = audio_fallback.info.length
                    except Exception:
                        pass

        except Exception as e:
            logger.warning(f"Error extracting metadata from {filepath}: {e}")

        # Final string sanitization and conversion
        title = str(title) if title else filename_title
        artist = str(artist) if artist else "Unknown Artist"
        album = str(album) if album else "Unknown Album"
        year = str(year) if year else None
        genre = str(genre) if genre else None

        return Song(
            filepath=filepath,
            title=title,
            artist=artist,
            album=album,
            duration=duration,
            year=year,
            genre=genre,
            artwork_data=artwork_data
        )

    @staticmethod
    def write_metadata(filepath: str, title: str, artist: str, album: str, genre: str) -> bool:
        """
        Attempts to write tags back to the physical file. Returns True if successful.
        """
        filepath = filepath.replace('\\', '/')
        if not MUTAGEN_AVAILABLE:
            return False
        try:
            audio = mutagen.File(filepath)
            ext = os.path.splitext(filepath)[1].lower()
            
            # MP3
            if (audio is not None and isinstance(audio, MP3)) or (audio is None and ext == '.mp3'):
                try:
                    try:
                        easy_tags = EasyID3(filepath)
                    except Exception:
                        try:
                            id3_temp = ID3()
                            id3_temp.save(filepath)
                        except Exception:
                            pass
                        easy_tags = EasyID3(filepath)
                    easy_tags['title'] = title
                    easy_tags['artist'] = artist
                    easy_tags['album'] = album
                    easy_tags['genre'] = genre
                    easy_tags.save()
                    return True
                except Exception:
                    try:
                        try:
                            id3_tags = ID3(filepath)
                        except Exception:
                            try:
                                id3_temp = ID3()
                                id3_temp.save(filepath)
                            except Exception:
                                pass
                            id3_tags = ID3(filepath)
                        from mutagen.id3 import TIT2, TPE1, TALB, TCON
                        id3_tags['TIT2'] = TIT2(encoding=3, text=title)
                        id3_tags['TPE1'] = TPE1(encoding=3, text=artist)
                        id3_tags['TALB'] = TALB(encoding=3, text=album)
                        id3_tags['TCON'] = TCON(encoding=3, text=genre)
                        id3_tags.save()
                        return True
                    except Exception:
                        pass
            
            # FLAC
            elif (audio is not None and isinstance(audio, FLAC)) or (audio is None and ext == '.flac'):
                if audio is None:
                    audio = FLAC(filepath)
                audio['title'] = title
                audio['artist'] = artist
                audio['album'] = album
                audio['genre'] = genre
                audio.save()
                return True
                
            # OGG
            elif (audio is not None and isinstance(audio, OggVorbis)) or (audio is None and ext in ('.ogg', '.oga')):
                if audio is None:
                    audio = OggVorbis(filepath)
                audio['title'] = title
                audio['artist'] = artist
                audio['album'] = album
                audio['genre'] = genre
                audio.save()
                return True
                
            # MP4 / M4A
            elif (audio is not None and isinstance(audio, MP4)) or (audio is None and ext in ('.m4a', '.mp4')):
                if audio is None:
                    audio = MP4(filepath)
                audio['\xa9nam'] = title
                audio['\xa9ART'] = artist
                audio['\xa9alb'] = album
                audio['\xa9gen'] = genre
                audio.save()
                return True
        except Exception as e:
            logger.warning(f"Failed to write metadata tags to file {filepath}: {e}")
        return False

