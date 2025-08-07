import customtkinter  # pip install customtkinter
import threading
import time
import urllib.request
import json
import os
import tempfile
import tweepy  # pip install tweepy
import configparser
import html
import traceback
from urllib.parse import urlparse, unquote
import requests
import ffmpeg  # pip install ffmpeg-python

#this is the beta version of the mememagnet. I have been messing around with ffmpeg to analyze the video/audio files and compress them if needed. It's not working flawless yet so definitely WIP

class KayoMemeMagnetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kayo-MemeMagnet")
        self.root.geometry("600x500")
        self.running = False
        self.posted_urls = self.load_posted_urls()
        self.config_file = 'config.ini'
        self.config = configparser.ConfigParser()
        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")
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
        self.subreddits_entry.grid(row=4, column=1, sticky="ew", pady=5)
        customtkinter.CTkLabel(input_frame, text="Interval (minutes):").grid(row=5, column=0, sticky="w", pady=5)
        self.interval_entry = customtkinter.CTkEntry(input_frame)
        self.interval_entry.grid(row=5, column=1, sticky="ew", pady=5)
        customtkinter.CTkLabel(input_frame, text="Max Posts per Cycle:").grid(row=6, column=0, sticky="w", pady=5)
        self.max_posts_entry = customtkinter.CTkEntry(input_frame)
        self.max_posts_entry.grid(row=6, column=1, sticky="ew", pady=5)
        customtkinter.CTkLabel(input_frame, text="Min Upvotes:").grid(row=7, column=0, sticky="w", pady=5)
        self.min_upvotes_entry = customtkinter.CTkEntry(input_frame)
        self.min_upvotes_entry.grid(row=7, column=1, sticky="ew", pady=5)
        input_frame.columnconfigure(1, weight=1)
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
        self.status_label = customtkinter.CTkLabel(root, text="Status: Stopped", corner_radius=5)
        self.status_label.pack(pady=5, padx=10, fill="x")
        self.log_text = customtkinter.CTkTextbox(root, wrap="word", height=150)
        self.log_text.pack(pady=10, padx=10, fill="both", expand=True)
        self.log_text.configure(state="disabled")
        self.load_config()
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
            try:
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
            except Exception as e:
                self.log(f"Error loading config: {str(e)}. Using defaults.")
        else:
            self.log("No config file found. Using defaults.")
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
            media_url = html.unescape(media_url)
            if p_data.get('is_video'):
                if 'secure_media' in p_data and p_data['secure_media'] and 'reddit_video' in p_data['secure_media']:
                    video_url = p_data['secure_media']['reddit_video']['fallback_url']
                    video_url = html.unescape(video_url)
                    audio_url = p_data['secure_media']['reddit_video'].get('audio_url')
                    if audio_url:
                        audio_url = html.unescape(audio_url)
                        memes.append({'title': p_data['title'], 'video_url': video_url, 'audio_url': audio_url, 'is_video': True, 'permalink': permalink})
                    else:
                        memes.append({'title': p_data['title'], 'url': video_url, 'is_video': True, 'permalink': permalink})
            elif media_url.endswith(('.jpg', '.png', '.gif')):
                memes.append({'title': p_data['title'], 'url': media_url, 'is_video': False, 'permalink': permalink})
        return memes
    def download_media(self, meme):
        temp_dir = tempfile.gettempdir()
        if 'video_url' in meme and 'audio_url' in meme:
            video_url = meme['video_url']
            audio_url = meme['audio_url']
            parsed_video = urlparse(video_url)
            filename = os.path.basename(unquote(parsed_video.path))
            _, ext = os.path.splitext(filename)
            if not ext:
                ext = '.mp4'
            video_path = os.path.join(temp_dir, f"video{ext}")
            audio_path = os.path.join(temp_dir, f"audio.mp3")
            # Download video
            with requests.get(video_url, headers={'User-Agent': 'KayoMemeMagnet/1.0'}, stream=True) as response:
                response.raise_for_status()
                with open(video_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            # Download audio
            with requests.get(audio_url, headers={'User-Agent': 'KayoMemeMagnet/1.0'}, stream=True) as response:
                response.raise_for_status()
                with open(audio_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            # Merge and re-encode with ffmpeg
            output_path = os.path.join(temp_dir, f"output{ext}")
            try:
                out = (
                    ffmpeg.input(video_path)
                    .output(
                        ffmpeg.input(audio_path).audio,
                        output_path,
                        vcodec='libx264',
                        acodec='aac',
                        preset='medium',
                        crf=23,
                        ar=44100,
                        ac=2,
                        format='mp4',
                        shortest=None,
                        map=['0:v:0', '1:a:0']  # Consolidated map argument
                    )
                )
                ffmpeg.run(out, overwrite_output=True)
                os.remove(video_path)
                os.remove(audio_path)
                # Probe for audio details
                probe = ffmpeg.probe(output_path)
                audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']
                has_audio = bool(audio_streams)
                audio_info = audio_streams[0] if audio_streams else {}
                self.log(f"Merged {meme['title']} with audio: {has_audio}, codec: {audio_info.get('codec_name', 'None')}, duration: {probe.get('format', {}).get('duration', 'N/A')}")
                if not has_audio:
                    raise ValueError("No audio after merge")
                file_size = os.path.getsize(output_path)
                if file_size > 15 * 1024 * 1024:
                    self.log(f"Converting oversized file {meme['title']} from {file_size / 1024:.2f}KB to fit 15MB limit")
                    converted_path = os.path.join(temp_dir, f"converted{ext}")
                    out = (
                        ffmpeg.input(output_path)
                        .output(
                            converted_path,
                            vcodec='libx264',
                            acodec='aac',
                            preset='fast',
                            crf=28,
                            b_v='1M', # Video bitrate limit
                            b_a='128k', # Audio bitrate limit
                            s='640x360', # Downscale to 360p
                            format='mp4',
                            shortest=None
                        )
                    )
                    ffmpeg.run(out, overwrite_output=True)
                    os.remove(output_path)
                    file_size = os.path.getsize(converted_path)
                    if file_size > 15 * 1024 * 1024:
                        os.remove(converted_path)
                        raise ValueError(f"Converted media still too large (15MB limit): {file_size / (1024*1024):.2f} MB")
                    output_path = converted_path
                    self.log(f"Converted {meme['title']} to {file_size / 1024:.2f}KB")
            except ffmpeg.Error as e:
                self.log(f"FFmpeg merge or conversion failed: {str(e)}")
                if os.path.exists(output_path):
                    os.remove(output_path)
                raise
            file_size = os.path.getsize(output_path)
            if file_size > 15 * 1024 * 1024:
                os.remove(output_path)
                raise ValueError(f"Media too large (15MB limit): {file_size / (1024*1024):.2f} MB")
            return output_path
        else:
            url = meme['url']
            parsed_url = urlparse(url)
            filename = os.path.basename(unquote(parsed_url.path))
            _, ext = os.path.splitext(filename)
            if not ext:
                ext = '.mp4' if 'video' in url else '.jpg'
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                response = requests.get(url, headers={'User-Agent': 'KayoMemeMagnet/1.0'}, stream=True)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
            file_size = os.path.getsize(tmp_file.name)
            if file_size > 15 * 1024 * 1024:
                os.remove(tmp_file.name)
                raise ValueError(f"Media too large (15MB limit): {file_size / (1024*1024):.2f} MB")
            return tmp_file.name

    def post_to_x(self, title, permalink, media_path):
        auth = tweepy.OAuth1UserHandler(self.consumer_key.get(), self.consumer_secret.get(), self.access_token.get(), self.access_secret.get())
        api = tweepy.API(auth)
        client = tweepy.Client(consumer_key=self.consumer_key.get(), consumer_secret=self.consumer_secret.get(),
                               access_token=self.access_token.get(), access_token_secret=self.access_secret.get())
        try:
            media = api.media_upload(media_path)
            tweet_text = f"{title} (Source: {permalink}) Kayo-MemeMagnet"
            client.create_tweet(text=tweet_text, media_ids=[media.media_id])
            self.log(f"Posted: {tweet_text}")
            return True # Indicate success
        except tweepy.errors.TweepyException as e:
            self.log(f"Post failed: {str(e)} for URL: {permalink}")
            if "429" in str(e): # Rate limit
                self.log("Rate limit hit. Waiting 15 minutes...")
                time.sleep(15 * 60) # Wait 15 minutes (X rate limit window)
            return False # Indicate failure
        except Exception as e:
            self.log(f"Unexpected error in post: {str(e)}")
            return False

    def run_loop(self):
        subreddits = [s.strip() for s in self.subreddits_entry.get().split(',')]
        while self.running:
            try:
                self.status_label.configure(text="Status: Fetching...")
                interval = int(self.interval_entry.get()) * 60
                max_posts = int(self.max_posts_entry.get())
                min_upvotes = int(self.min_upvotes_entry.get())
                self.log(f"Starting loop with interval: {interval // 60} minutes, max_posts: {max_posts}, min_upvotes: {min_upvotes}")
                posted_count = 0
                for subreddit in subreddits:
                    self.log(f"Fetching from r/{subreddit}...")
                    memes = self.fetch_popular_memes(subreddit, limit=50, min_upvotes=min_upvotes)
                    for meme in memes:
                        if meme['url'] in self.posted_urls or ('video_url' in meme and meme['video_url'] in self.posted_urls):
                            continue
                        self.log(f"Processing: {meme['title']}")
                        try:
                            media_path = self.download_media(meme)
                            if self.post_to_x(meme['title'], meme['permalink'], media_path):
                                os.remove(media_path)
                                self.posted_urls.add(meme.get('url', meme.get('video_url', '')))
                                self.save_posted_urls()
                                posted_count += 1
                            else:
                                os.remove(media_path) # Clean up on failure
                        except Exception as e:
                            self.log(f"Skip: {str(e)} for URL: {meme.get('url', meme.get('video_url', ''))}\n{traceback.format_exc()}")
                        if posted_count >= max_posts:
                            break
                    if posted_count >= max_posts:
                        break
                if posted_count > 0:
                    self.log(f"Cycle complete. Posted {posted_count} items. Sleeping for {interval / 60:.2f} minutes.")
                else:
                    self.log("No new posts this cycle or all failed. Sleeping for {interval / 60:.2f} minutes.")
                self.status_label.configure(text="Status: Sleeping")
                actual_sleep = time.time() + interval
                time.sleep(interval)
                self.log(f"Woke up after {(time.time() - actual_sleep + interval) / 60:.2f} minutes.")
            except Exception as e:
                self.log(f"Error in cycle: {str(e)}\n{traceback.format_exc()}")
            if not self.running: # Ensure stop condition is respected
                break
        self.status_label.configure(text="Status: Stopped")

    def start(self):
        if not self.running:
            self.running = True
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")
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
