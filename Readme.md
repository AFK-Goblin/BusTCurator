# 🎵 BusTCurator
The BusT Spotify Playlist Manager with a visual dashboard.

## How to Use
1. **Download** the app (or clone the repo).
2. **Get Spotify Keys:**
   - Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
   - Log in and click "Create App".
   - Give it a name (e.g., "My Curator") and description.
   - For "Redirect URI", enter: `http://localhost:8080`
   - Save.
3. **Setup Secrets:**
   - Create a text file named `.env` in the same folder as the app.
   - Paste the following inside, replacing the X's with your new keys:
     ```
     SPOTIPY_CLIENT_ID=xxxxxxxxxxxxxxxx
     SPOTIPY_CLIENT_SECRET=xxxxxxxxxxxxxxxx
     SPOTIPY_REDIRECT_URI=http://localhost:8080
     ```
4. **Run the App!**
   - Double click `BusTCurator.exe`.
   - OR run via python: `python app.py`

## Features
- **Curate & Discover:** Filter by genre and add "Spice" (new music discovery).
- **Reader Mode:** Instantly filter out songs with lyrics.
- **Visual Stats:** See a breakdown of your library's genres.

## Coming soon
- **Transfer Playlists:** Transfer your spotify liked songs / playlist to Youtube music.