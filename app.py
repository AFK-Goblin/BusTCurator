import customtkinter as ctk
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from tkinter import messagebox
import threading
import random
import os
import math
import webbrowser
from dotenv import load_dotenv

# --- CONFIGURATION & THEME ---
# We load the env immediately, but we won't exit if it fails yet.
load_dotenv()

COLORS = {
    "bg": "#190a29",          
    "frame": "#251036",       
    "green": "#00ff9d",       
    "purple": "#8a2be2",      
    "pink": "#ff1493",        
    "orange": "#ff7700",      
    "yellow": "#ffdd00",      
    "text": "#e0e0e0"         
}

SCOPE = "user-library-read playlist-modify-public playlist-read-private"

# --- ANIMATED BACKGROUND (Reused for both windows) ---
class GroovyBackground(ctk.CTkCanvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, highlightthickness=0, bg=COLORS["bg"], **kwargs)
        self.width = 800
        self.height = 900
        self.stars = []
        self.notes = []
        self.bind("<Configure>", self.on_resize)
        
        for _ in range(70): self.add_star()
        for _ in range(5): self.add_note()
        self.animate()

    def on_resize(self, event):
        self.width = event.width
        self.height = event.height

    def add_star(self):
        x = random.randint(0, 1000)
        y = random.randint(0, 1000)
        size = random.randint(1, 3)
        fill = random.choice(["#ffffff", "#aaaaaa", "#777777"])
        star = self.create_oval(x, y, x+size, y+size, fill=fill, outline="")
        self.stars.append({"id": star, "speed": random.uniform(0.2, 0.8)})

    def add_note(self):
        x = random.randint(50, 750)
        y = random.randint(800, 900)
        char = random.choice(["♪", "♫", "♩", "♬"])
        color = random.choice([COLORS["green"], COLORS["pink"], COLORS["yellow"], COLORS["orange"]])
        font_size = random.randint(20, 30)
        note = self.create_text(x, y, text=char, fill=color, font=("Arial", font_size))
        self.notes.append({"id": note, "speed": random.uniform(1, 3), "wobble": random.uniform(0, 100)})

    def animate(self):
        for s in self.stars:
            self.move(s["id"], 0, 0.2 * s["speed"])
            coords = self.coords(s["id"])
            if coords and coords[1] > self.height:
                self.move(s["id"], 0, -self.height)

        for n in self.notes:
            n["wobble"] += 0.1
            dx = math.sin(n["wobble"]) * 1.5 
            dy = -1 * n["speed"]
            self.move(n["id"], dx, dy)
            coords = self.coords(n["id"])
            if coords and coords[1] < -50:
                self.move(n["id"], random.randint(-100, 100), self.height + 100)
        self.after(50, self.animate)

# --- SETUP WIZARD (Runs if .env is missing) ---
class SetupWizard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BusTCurator - First Run Setup")
        self.geometry("600x500")
        self.configure(fg_color=COLORS["bg"])
        
        self.bg_canvas = GroovyBackground(self, width=600, height=500)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        main_frame = ctk.CTkFrame(self, fg_color=COLORS["frame"], border_color=COLORS["green"], border_width=2)
        main_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.85)

        ctk.CTkLabel(main_frame, text="Welcome to BusTCurator!", font=("Rubik", 24, "bold"), text_color="white").pack(pady=(30, 10))
        ctk.CTkLabel(main_frame, text="To get started, we need your Spotify API Keys.", text_color=COLORS["text"]).pack()

        # Link Button
        link_btn = ctk.CTkButton(main_frame, text="Click here to get keys (Spotify Dashboard)", 
                                 command=self.open_spotify_dash, fg_color=COLORS["purple"], hover_color=COLORS["pink"])
        link_btn.pack(pady=10)

        ctk.CTkLabel(main_frame, text="(Create an App -> Settings -> Copy Client ID & Secret)", font=("Arial", 10), text_color="gray").pack()
        
        # Inputs
        self.entry_id = ctk.CTkEntry(main_frame, placeholder_text="Paste Client ID here", width=300)
        self.entry_id.pack(pady=(20, 10))
        
        self.entry_secret = ctk.CTkEntry(main_frame, placeholder_text="Paste Client Secret here", width=300, show="*")
        self.entry_secret.pack(pady=(0, 20))

        # Save Button
        ctk.CTkButton(main_frame, text="Save & Launch", command=self.save_keys, 
                      fg_color=COLORS["green"], text_color=COLORS["bg"], font=("Arial", 14, "bold")).pack(pady=20)
        
        self.success = False

    def open_spotify_dash(self):
        webbrowser.open("https://developer.spotify.com/dashboard")

    def save_keys(self):
        c_id = self.entry_id.get().strip()
        c_secret = self.entry_secret.get().strip()
        
        if not c_id or not c_secret:
            messagebox.showwarning("Missing Info", "Please paste both keys to continue.")
            return
            
        # Write to .env
        with open(".env", "w") as f:
            f.write(f"SPOTIPY_CLIENT_ID={c_id}\n")
            f.write(f"SPOTIPY_CLIENT_SECRET={c_secret}\n")
            f.write("SPOTIPY_REDIRECT_URI=http://localhost:8080\n")
            
        messagebox.showinfo("Success", "Keys saved! Launching the app...")
        self.success = True
        self.destroy()

# --- MAIN APP ---
class ScrollableCheckBoxFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["frame"], scrollbar_button_color=COLORS["purple"], **kwargs)
        self.checkboxes = []
        self.all_items = []

    def add_item(self, item_text, data_value):
        checkbox = ctk.CTkCheckBox(self, text=item_text, text_color=COLORS["text"], 
                                   fg_color=COLORS["green"], hover_color=COLORS["pink"],
                                   checkmark_color=COLORS["bg"])
        checkbox.pack(anchor="w", pady=2, padx=10)
        self.checkboxes.append({"cb": checkbox, "value": data_value, "text": item_text})
        self.all_items.append({"value": data_value, "text": item_text})

    def filter_items(self, search_query):
        for item in self.checkboxes: item["cb"].destroy()
        self.checkboxes = []
        search_query = search_query.lower()
        for item in self.all_items:
            if search_query in item["text"].lower():
                self.add_new_checkbox(item["text"], item["value"])

    def add_new_checkbox(self, text, value):
        checkbox = ctk.CTkCheckBox(self, text=text, text_color=COLORS["text"],
                                   fg_color=COLORS["green"], hover_color=COLORS["pink"],
                                   checkmark_color=COLORS["bg"])
        checkbox.pack(anchor="w", pady=2, padx=10)
        self.checkboxes.append({"cb": checkbox, "value": value, "text": text})

    def get_checked_values(self):
        return [item["value"] for item in self.checkboxes if item["cb"].get() == 1]
    
    def clear_all(self):
        for item in self.checkboxes: item["cb"].destroy()
        self.checkboxes = []
        self.all_items = []

class BusTCuratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BusTCurator 🎵")
        self.geometry("800x900")
        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=COLORS["bg"])

        self.bg_canvas = GroovyBackground(self, width=800, height=900)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, pady=(20, 10), sticky="ew")
        ctk.CTkLabel(self.header_frame, text="BusTCurator", font=("Rubik", 32, "bold"), text_color="white").pack()
        ctk.CTkLabel(self.header_frame, text="The Groovy Playlist Manager", font=("Arial", 14, "italic"), text_color=COLORS["green"]).pack()

        # Tabs
        self.tabview = ctk.CTkTabview(self, fg_color=COLORS["frame"], segmented_button_fg_color=COLORS["bg"],
                                      segmented_button_selected_color=COLORS["green"], segmented_button_selected_hover_color=COLORS["pink"],
                                      segmented_button_unselected_color=COLORS["frame"], text_color="white")
        self.tabview.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.tab_curate = self.tabview.add("Curate & Discover")
        self.tab_stats = self.tabview.add("Visual Stats")
        
        self.sp = None
        self.user_id = None
        self.genre_map = {} 
        self.authenticate_spotify()
        self.setup_curate_tab()
        self.setup_stats_tab()

        # Status Bar
        self.status_bar_frame = ctk.CTkFrame(self, height=40, fg_color=COLORS["frame"], border_color=COLORS["green"], border_width=2)
        self.status_bar_frame.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        self.status_label = ctk.CTkLabel(self.status_bar_frame, text="Ready. Stay Groovy.", text_color=COLORS["green"])
        self.status_label.pack(side="left", padx=15)
        self.progress_bar = ctk.CTkProgressBar(self.status_bar_frame, width=200, progress_color=COLORS["pink"])
        self.progress_bar.pack(side="right", padx=15, pady=10)
        self.progress_bar.set(0)

    def run_in_thread(self, target_func):
        thread = threading.Thread(target=target_func)
        thread.daemon = True
        thread.start()

    def authenticate_spotify(self):
        try:
            auth_manager = SpotifyOAuth(scope=SCOPE, open_browser=False)
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            self.user_id = self.sp.current_user()['id']
        except Exception as e:
            messagebox.showerror("Auth Error", f"Could not connect.\n{e}")
            self.destroy()

    def setup_curate_tab(self):
        self.tab_curate.grid_columnconfigure(0, weight=1)
        self.tab_curate.grid_rowconfigure(3, weight=1)

        ctrl_frame = ctk.CTkFrame(self.tab_curate, fg_color="transparent")
        ctrl_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.btn_scan = ctk.CTkButton(ctrl_frame, text="1. Scan Library", command=self.start_scan_thread,
                                      fg_color=COLORS["purple"], hover_color=COLORS["pink"], font=("Arial", 14, "bold"))
        self.btn_scan.pack(side="left", padx=5)

        self.playlist_name_entry = ctk.CTkEntry(ctrl_frame, placeholder_text="Playlist Name...", width=250,
                                                fg_color=COLORS["bg"], border_color=COLORS["green"], text_color="white")
        self.playlist_name_entry.pack(side="left", padx=5, fill="x", expand=True)

        self.btn_create = ctk.CTkButton(ctrl_frame, text="Create Mix", command=self.start_creation_thread, state="disabled",
                                        fg_color="gray", font=("Arial", 14, "bold"))
        self.btn_create.pack(side="right", padx=5)

        filter_frame = ctk.CTkFrame(self.tab_curate, fg_color="transparent")
        filter_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(filter_frame, text="Search Genre:", text_color=COLORS["yellow"]).pack(side="left", padx=5)
        self.search_entry = ctk.CTkEntry(filter_frame, width=150, fg_color=COLORS["bg"], border_color=COLORS["purple"], text_color="white")
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        self.var_instrumental = ctk.BooleanVar(value=False)
        self.chk_instrumental = ctk.CTkCheckBox(filter_frame, text="No Lyrics (Read Mode)", variable=self.var_instrumental,
                                                text_color=COLORS["green"], fg_color=COLORS["purple"], hover_color=COLORS["pink"])
        self.chk_instrumental.pack(side="left", padx=20)

        spice_frame = ctk.CTkFrame(self.tab_curate, fg_color="transparent")
        spice_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(spice_frame, text="Discovery Spice:", text_color=COLORS["orange"]).pack(side="left", padx=5)
        self.lbl_spice = ctk.CTkLabel(spice_frame, text="0%", text_color=COLORS["text"])
        self.lbl_spice.pack(side="right", padx=10)
        
        self.slider_spice = ctk.CTkSlider(spice_frame, from_=0, to=100, number_of_steps=10, command=self.update_spice_label,
                                          progress_color=COLORS["orange"], button_color=COLORS["green"], button_hover_color=COLORS["yellow"])
        self.slider_spice.set(0)
        self.slider_spice.pack(side="left", fill="x", expand=True, padx=10)

        self.genre_list = ScrollableCheckBoxFrame(self.tab_curate, width=500, height=300)
        self.genre_list.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

    def setup_stats_tab(self):
        self.tab_stats.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.tab_stats, text="Library Stats", font=("Rubik", 20, "bold"), text_color=COLORS["green"]).pack(pady=(20, 10))
        self.stats_text = ctk.CTkTextbox(self.tab_stats, width=500, height=350, fg_color=COLORS["bg"], text_color="white", border_color=COLORS["purple"], border_width=2)
        self.stats_text.pack(pady=10, padx=20, fill="both", expand=True)

    def update_spice_label(self, value):
        self.lbl_spice.configure(text=f"{int(value)}%")

    def on_search(self, event):
        self.genre_list.filter_items(self.search_entry.get())

    def start_scan_thread(self):
        self.btn_scan.configure(state="disabled")
        self.progress_bar.set(0)
        self.run_in_thread(self.scan_library)

    def scan_library(self):
        self.status_label.configure(text="Fetching your vibes...")
        try:
            results = self.sp.current_user_saved_tracks(limit=50)
            items = results['items']
            while results['next']:
                results = self.sp.next(results)
                items.extend(results['items'])
            
            artist_to_tracks = {} 
            artist_ids_list = []
            for item in items:
                if item.get('track') and item['track'].get('artists'):
                    t = item['track']
                    aid = t['artists'][0]['id']
                    if aid:
                        artist_ids_list.append(aid)
                        if aid not in artist_to_tracks: artist_to_tracks[aid] = []
                        artist_to_tracks[aid].append(t['id'])

            unique_artists = list(set(artist_ids_list))
            total_artists = len(unique_artists)
            self.genre_map = {} 
            
            for i in range(0, total_artists, 50):
                self.progress_bar.set(i / total_artists)
                self.status_label.configure(text=f"Analyzing artists {i}/{total_artists}...")
                chunk = unique_artists[i:i+50]
                artists_data = self.sp.artists(chunk)
                for artist in artists_data['artists']:
                    if artist.get('genres'):
                        for genre in artist['genres']:
                            if genre not in self.genre_map: self.genre_map[genre] = []
                            self.genre_map[genre].extend(artist_to_tracks.get(artist['id'], []))

            self.genre_list.clear_all()
            sorted_genres = sorted(self.genre_map.keys())
            
            self.stats_text.delete("0.0", "end")
            self.stats_text.insert("0.0", f"Total Songs Scanned: {len(items)}\nUnique Genres Found: {len(sorted_genres)}\n\n--- TOP GENRES ---\n")
            filtered_genres = []
            for g in sorted_genres:
                count = len(self.genre_map[g])
                if count >= 3: filtered_genres.append((g, count))
            
            for g, count in filtered_genres: self.genre_list.add_item(f"{g.title()} ({count})", g)
            top_10 = sorted(filtered_genres, key=lambda x: x[1], reverse=True)[:15]
            for g, c in top_10: self.stats_text.insert("end", f"• {g.title()} ({c} songs)\n")

            self.status_label.configure(text=f"Scan complete. Found {len(filtered_genres)} main genres.")
            self.progress_bar.set(1.0)
            self.btn_create.configure(state="normal", fg_color=COLORS["green"], text_color=COLORS["frame"])
        except Exception as e:
            self.status_label.configure(text="Scan Error")
            print(e)
        finally:
            self.btn_scan.configure(state="normal")

    def start_creation_thread(self):
        name = self.playlist_name_entry.get()
        genres = self.genre_list.get_checked_values()
        spice = self.slider_spice.get()
        only_inst = self.var_instrumental.get()

        if not name or not genres:
            messagebox.showwarning("Info", "Please enter a name and pick a genre.")
            return

        self.btn_create.configure(state="disabled")
        self.run_in_thread(lambda: self.create_playlist(name, genres, spice, only_inst))

    def create_playlist(self, name, genres, spice, only_instrumental):
        self.status_label.configure(text="Curating songs...")
        user_track_ids = set()
        for g in genres: user_track_ids.update(self.genre_map.get(g, []))
        final_track_ids = list(user_track_ids)
        
        if only_instrumental:
            self.status_label.configure(text="Filtering vocals (this takes a moment)...")
            instrumental_ids = []
            for i in range(0, len(final_track_ids), 100):
                self.progress_bar.set(i / len(final_track_ids))
                chunk = final_track_ids[i:i+100]
                features = self.sp.audio_features(chunk)
                for f in features:
                    if f and f['instrumentalness'] > 0.5: instrumental_ids.append(f['id'])
            final_track_ids = instrumental_ids

        if spice > 0 and final_track_ids:
            self.status_label.configure(text="Adding Spice (Discovery)...")
            target_new = int(len(final_track_ids) * (spice / 100))
            seed_tracks = random.sample(final_track_ids, min(5, len(final_track_ids)))
            try:
                target_inst = 0.6 if only_instrumental else None
                recs = self.sp.recommendations(seed_tracks=seed_tracks, limit=min(100, target_new), min_instrumentalness=target_inst)
                for r in recs['tracks']: final_track_ids.append(r['id'])
            except Exception as e: print(f"Discovery error: {e}")

        if not final_track_ids:
            messagebox.showinfo("Result", "No songs found after filtering.")
            self.btn_create.configure(state="normal")
            return

        try:
            self.status_label.configure(text=f"Creating '{name}'...")
            desc = f"Curated by BusTCurator. {int(spice)}% Spice. Genres: {', '.join(genres[:3])}"
            new_pl = self.sp.user_playlist_create(self.user_id, name, public=True, description=desc)
            random.shuffle(final_track_ids)
            for i in range(0, len(final_track_ids), 100): self.sp.playlist_add_items(new_pl['id'], final_track_ids[i:i+100])
            self.status_label.configure(text="Playlist Created Successfully!")
            self.progress_bar.set(1.0)
            messagebox.showinfo("Groovy!", f"Created '{name}' with {len(final_track_ids)} tracks.")
        except Exception as e: messagebox.showerror("Error", str(e))
        finally:
            self.btn_create.configure(state="normal")
            self.progress_bar.set(0)

# --- STARTUP LOGIC ---
if __name__ == "__main__":
    # Check if keys are missing
    if not os.getenv("SPOTIPY_CLIENT_ID") or not os.getenv("SPOTIPY_CLIENT_SECRET"):
        # Launch Setup Wizard
        setup_app = SetupWizard()
        setup_app.mainloop()
        
        # If setup was successful, reload environment and start main app
        if setup_app.success:
            load_dotenv(override=True)
            app = BusTCuratorApp()
            app.mainloop()
    else:
        # Keys exist, launch straight away
        app = BusTCuratorApp()
        app.mainloop()