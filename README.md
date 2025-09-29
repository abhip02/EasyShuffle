# Spotify to Apple Music Downloader

I have an iPod Shuffle and I get lazy. Automatically download songs from a Spotify playlist, convert them to MP3 via YouTube, and import them into Apple Music.

## Usage
Update yt-dlp to avoid errors:
```bash
python3 -m pip install -U yt-dlp

```bash
python main.py --spotify_url "<spotify_playlist_url>" --playlist "My Apple Playlist"
