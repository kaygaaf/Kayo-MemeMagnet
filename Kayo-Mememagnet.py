import customtkinter  # pip install customtkinter
import threading
import time
import urllib.request
import json
import os
import tempfile
import tweepy  # pip install tweepy
import configparser

class KayoMemeMagnetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kayo-MemeMagnet")
        self.root.geometry("600x500")
        self.running = False
        self.posted_urls = self.load_posted_urls()
        self.config_file = 'config.ini'
        self.config = configparser.ConfigParser()
        self.load_config()

        # Set modern theme
        customtkinter.set_appearance_mode("System")  # Auto light/dark
        customtkinter.set_default_color_theme("blue")  # Clean blue theme

        # Input Frame
        input_frame = customtkinter.CTkFrame(root, corner_radius=10)
        input_frame.pack(pady=10, padx=10, fill="x")

        customtkinter.CTkLabel(input_frame, text="X Consumer Key:").grid(row=0, column=0, sticky="w", pady=5)
        self.consumer_key = customtkinter.CTkEntry(input_frame)
        self.consumer_key.grid(row=0, column=1, sticky="ew", pady=5)

        customtkinter.CTkLabel(input_frame, text="X Consumer Secret:").grid(row=1, column=0, sticky="w", pady=5)
        self.consumer_secret = customtkinter.CTkEntry(input_frame, show="*")
        self.consumer_secret.grid(row=1, column=1, sticky="ew", pady=5)

        customtkinter.CTkLabel(input_frame, text="X Access Token:").grid(row=2, column=0, sticky="w", pady=5)
        self.access_token = customtkinter.CTkEntry(input_frame)
        self.access_token.grid(row=2, column=1, sticky="ew", pady=5)

        customtkinter.CTkLabel(input_frame, text="X Access Secret:").grid(row=3, column=0, sticky="w", pady=5)
        self.access_secret = customtkinter.CTkEntry(input_frame, show="*")
        self.access_secret.grid(row=3, column=1, sticky="ew", pady=5)

        customtkinter.CTkLabel(input_frame, text="Subreddits (comma-separated):").grid(row=4, column=0, sticky="w", pady=5)
        self.subreddits_entry = customtkinter.CTkEntry(input_frame)
        self.subreddits_entry.insert(0, "memes,dankmemes")
        self.subreddits_entry.grid(row=4, column=1, sticky="ew", pady=5)

        customtkinter.CTkLabel(input_frame, text="Interval (minutes):").grid(row=5, column=0, sticky="w", pady=5)
        self.interval_entry = customtkinter.CTkEntry(input_frame)
        self.interval_entry.insert(0, "60")
        self.interval_entry.grid(row=5, column=1, sticky="ew", pady=5)

        customtkinter.CTkLabel(input_frame, text="Max Posts per Cycle:").grid(row=6, column=0, sticky="w", pady=5)
        self.max_posts_entry = customtkinter.CTkEntry(input_frame)
        self.max_posts_entry.insert(0, "3")
        self.max_posts_entry.grid(row=6, column=1, sticky="ew", pady=5)

        customtkinter.CTkLabel(input_frame, text="Min Upvotes:").grid(row=7, column=0, sticky="w", pady=5)
        self.min_upvotes_entry = customtkinter.CTkEntry(input_frame)
        self.min_upvotes_entry.insert(0, "1000")
        self.min_upvotes_entry.grid(row=7, column=1, sticky="ew", pady=5)

        input_frame.columnconfigure(1, weight=1)  # Expand entry fields

        # Button Frame
        button_frame = customtkinter.CTkFrame(root, corner_radius=10)
        button_frame.pack(pady=10, padx=10, fill="x")

        self.start_button = customtkinter.CTkButton(button_frame, text="Start", command=self.start)
        self.start_button.pack(side="left", padx=5)

        self.stop_button = customtkinter.CTkButton(button_frame, text="Stop", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=5)

        self.save_config_button = customtkinter.CTkButton(button_frame, text="Save Config", command=self.save_config)
        self.save_config_button.pack(side="left", padx=5)

        self.clear_log_button = customtkinter.CTkButton(button_frame, text="Clear Log", command=self.clear_log)
        self.clear_log_button.pack(side="left", padx=5)

        # Status Label
        self.status_label = customtkinter.CTkLabel(root, text="Status: Stopped", corner_radius=5)
        self.status_label.pack(pady=5, padx=10, fill="x")

        # Log Textbox
        self.log_text = customtkinter.CTkTextbox(root, wrap="word", height=150)
        self.log_text.pack(pady=10, padx=10, fill="both", expand=True)
        self.log_text.configure(state="disabled")  # Read-only

        self.log("App ready. Load or enter details and save config.")

    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            if 'X' in self.config:
                self.consumer_key.insert(0, self.config['X'].get('consumer_key', ''))
                self.consumer_secret.insert(0, self.config['X'].get('consumer_secret', ''))
                self.access_token.insert(0, self.config['X'].get('access_token', ''))
                self.access_secret.insert(0, self.config['X'].get('access_secret', ''))
            if 'Settings' in self.config:
                self.subreddits_entry.insert(0, self.config['Settings'].get('subreddits', 'memes,dankmemes'))
                self.interval_entry.insert(0, self.config['Settings'].get('interval', '60'))
                self.max_posts_entry.insert(0, self.config['Settings'].get('max_posts', '3'))
                self.min_upvotes_entry.insert(0, self.config['Settings'].get('min_upvotes', '1000'))
            self.log("Config loaded.")

    def save_config(self):
        self.config['X'] = {
            'consumer_key': self.consumer_key.get(),
            'consumer_secret': self.consumer_secret.get(),
            'access_token': self.access_token.get(),
            'access_secret': self.access_secret.get()
        }
        self.config['Settings'] = {
            'subreddits': self.subreddits_entry.get(),
            'interval': self.interval_entry.get(),
            'max_posts': self.max_posts_entry.get(),
            'min_upvotes': self.min_upvotes_entry.get()
        }
        with open(self.config_file, 'w') as f:
            self.config.write(f)
        self.log("Config saved.")

    def load_posted_urls(self):
        if os.path.exists('posted.json'):
            with open('posted.json', 'r') as f:
                return set(json.load(f))
        return set()

    def save_posted_urls(self):
        with open('posted.json', 'w') as f:
            json.dump(list(self.posted_urls), f)

    def fetch_popular_memes(self, subreddit, limit, min_upvotes):
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
        req = urllib.request.Request(url, headers={'User-Agent': 'KayoMemeMagnet/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        posts = data['data']['children']
        memes = []
        for post in posts:
            p_data = post['data']
            if p_data['score'] < min_upvotes:
                continue
            media_url = p_data['url']
            permalink = f"https://reddit.com{p_data['permalink']}"
            if p_data.get('is_video'):
                if 'secure_media' in p_data and p_data['secure_media'] and 'reddit_video' in p_data['secure_media']:
                    media_url = p_data['secure_media']['reddit_video']['fallback_url']
                    memes.append({'title': p_data['title'], 'url': media_url, 'is_video': True, 'permalink': permalink})
            elif media_url.endswith(('.jpg', '.png', '.gif')):
                memes.append({'title': p_data['title'], 'url': media_url, 'is_video': False, 'permalink': permalink})
        return memes

    def download_media(self, url):
        _, ext = os.path.splitext(url)
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            with urllib.request.urlopen(url) as response:
                tmp_file.write(response.read())
        file_size = os.path.getsize(tmp_file.name)
        if file_size > 512 * 1024 * 1024:  # X limit for videos
            os.remove(tmp_file.name)
            raise ValueError(f"Media too large: {file_size / (1024*1024):.2f} MB")
        return tmp_file.name

    def post_to_x(self, title, permalink, media_path):
        auth = tweepy.OAuth1UserHandler(self.consumer_key.get(), self.consumer_secret.get(), self.access_token.get(), self.access_secret.get())
        api = tweepy.API(auth)
        client = tweepy.Client(consumer_key=self.consumer_key.get(), consumer_secret=self.consumer_secret.get(),
                               access_token=self.access_token.get(), access_token_secret=self.access_secret.get())

        media = api.media_upload(media_path)
        tweet_text = f"{title} (Source: {permalink})"
        client.create_tweet(text=tweet_text, media_ids=[media.media_id])
        self.log(f"Posted: {tweet_text}")

    def run_loop(self):
        subreddits = [s.strip() for s in self.subreddits_entry.get().split(',')]
        interval = int(self.interval_entry.get()) * 60
        max_posts = int(self.max_posts_entry.get())
        min_upvotes = int(self.min_upvotes_entry.get())
        while self.running:
            try:
                self.status_label.configure(text="Status: Fetching...")
                posted_count = 0
                for subreddit in subreddits:
                    self.log(f"Fetching from r/{subreddit}...")
                    memes = self.fetch_popular_memes(subreddit, limit=50, min_upvotes=min_upvotes)
                    for meme in memes:
                        if meme['url'] in self.posted_urls:
                            continue
                        self.log(f"Processing: {meme['title']}")
                        try:
                            media_path = self.download_media(meme['url'])
                            self.post_to_x(meme['title'], meme['permalink'], media_path)
                            os.remove(media_path)
                            self.posted_urls.add(meme['url'])
                            self.save_posted_urls()
                            posted_count += 1
                            if posted_count >= max_posts:
                                break
                        except Exception as e:
                            self.log(f"Skip: {str(e)}")
                    if posted_count >= max_posts:
                        break
                self.log(f"Cycle complete. Sleeping for {interval // 60} minutes.")
                self.status_label.configure(text="Status: Sleeping")
            except Exception as e:
                self.log(f"Error in cycle: {str(e)}")
            time.sleep(interval)
        self.status_label.configure(text="Status: Stopped")

    def start(self):
        if not self.running:
            self.running = True
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            threading.Thread(target=self.run_loop, daemon=True).start()
            self.log("Started automation.")
            self.status_label.configure(text="Status: Running")

    def stop(self):
        self.running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.log("Stopping automation...")

if __name__ == "__main__":
    root = customtkinter.CTk()
    app = KayoMemeMagnetApp(root)
    root.mainloop()
