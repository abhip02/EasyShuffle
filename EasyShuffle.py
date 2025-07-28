import os
import subprocess
import shutil
import yt_dlp
import argparse

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv


def load_credentials():
    load_dotenv()  # Automatically looks for a .env file
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise Exception("Spotify credentials not found in .env file.")
    
    return client_id, client_secret

client_id, client_secret = load_credentials()

# --- Config ---
SPOTIFY_CLIENT_ID = client_id
SPOTIFY_CLIENT_SECRET = client_secret
REDIRECT_URI = "https://example.com/callback"
DEFAULT_OUTPUT_DIR = "DownloadedMP3s"
DEFAULT_YOUTUBE_LINKS_FILE = "youtube_links.txt"

# --- Spotify Setup ---
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=REDIRECT_URI,
    scope="playlist-read-private"
))

# --- Utility Functions ---

def clear_output_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def get_tracks_from_spotify_playlist(playlist_url):
    playlist_id = playlist_url.split("/")[-1].split("?")[0]
    results = sp.playlist_items(playlist_id)
    tracks = []
    for item in results['items']:
        track = item['track']
        if track:
            name = track['name']
            artist = track['artists'][0]['name']
            query = f"{name} {artist}"
            tracks.append(query)
    return tracks

def search_youtube(query):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': 'in_playlist',
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                return f"https://www.youtube.com/watch?v={info['entries'][0]['id']}"
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
    return None

def create_youtube_link_file_from_spotify(playlist_url, output_file=DEFAULT_YOUTUBE_LINKS_FILE):
    queries = get_tracks_from_spotify_playlist(playlist_url)
    with open(output_file, "w") as f:
        for query in queries:
            url = search_youtube(query)
            if url:
                f.write(url + "\n")
                print(f"✓ {query} → {url}")
            else:
                print(f"✗ {query} → no result")

def read_youtube_links(file_path):
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

def download_mp3s(youtube_links, output_dir):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(youtube_links)

def import_to_music_playlist(folder_path, playlist_name):
    for filename in os.listdir(folder_path):
        if filename.endswith(".mp3"):
            full_path = os.path.abspath(os.path.join(folder_path, filename))
            apple_script = f'''
            set theFile to POSIX file "{full_path}" as alias
            tell application "Music"
                add theFile to playlist "{playlist_name}"
            end tell
            '''
            subprocess.run(["osascript", "-e", apple_script])

def import_to_new_music_playlist(folder_path, playlist_name):
    create_script = f'''
    tell application "Music"
        if not (exists playlist "{playlist_name}") then
            make new user playlist with properties {{name:"{playlist_name}"}}
        end if
    end tell
    '''
    subprocess.run(["osascript", "-e", create_script])
    import_to_music_playlist(folder_path, playlist_name)

def cleanup_folder(folder_path, extensions=[".mp3"]):
    for filename in os.listdir(folder_path):
        if any(filename.endswith(ext) for ext in extensions):
            os.remove(os.path.join(folder_path, filename))
    print(f"🧹 Cleaned up {folder_path}")

# --- Main Function ---
def main(spotify_url=None, apple_playlist="Recently Downloaded"):
    output_dir = DEFAULT_OUTPUT_DIR
    youtube_links_file = DEFAULT_YOUTUBE_LINKS_FILE

    clear_output_dir(output_dir)

    if spotify_url:
        print("🔗 Getting YouTube links from Spotify playlist...")
        create_youtube_link_file_from_spotify(spotify_url, youtube_links_file)

    print("📥 Reading YouTube links...")
    youtube_links = read_youtube_links(youtube_links_file)

    print("🎧 Downloading MP3s...")
    download_mp3s(youtube_links, output_dir)

    print(f"🎶 Importing into Apple Music playlist: {apple_playlist}")
    import_to_new_music_playlist(output_dir, apple_playlist)
    
    print("🧹 Cleaning up downloaded files...")
    cleanup_folder(output_dir)

    print("✅ Done!")

# --- Entry Point ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download songs from Spotify playlist and import to Apple Music.")
    parser.add_argument("--spotify_url", type=str, default=None, help="Spotify playlist URL")
    parser.add_argument("--playlist", type=str, default="Recently Downloaded", help="Apple Music playlist name")
    args = parser.parse_args()

    main(spotify_url=args.spotify_url, apple_playlist=args.playlist)
