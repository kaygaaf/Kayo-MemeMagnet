import customtkinter # pip install customtkinter
import threading
import time
import requests
import json
import os
import tempfile
import tweepy # pip install tweepy
import configparser
import html
import traceback
from urllib.parse import urlparse, unquote
import ffmpeg # pip install ffmpeg-python
from PIL import Image # pip install pillow
import base64
import re

class KayoMemeMagnetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kayo-MemeMagnet")
        self.root.geometry("600x500")
        self.running = False
        self.posted_urls = self.load_posted_urls()
        self.config_file = 'config.ini'
        self.config = configparser.ConfigParser()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'KayoMemeMagnet/1.0'})
        self.api = None
        self.client = None
        self.trending_hashtags = []
        self.last_trending_update = 0
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
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        posts = data['data']['children']
        memes = []
        for post in posts:
            p_data = post['data']
            if p_data['score'] < min_upvotes:
                continue
            media_url = html.unescape(p_data['url'])
            permalink = f"https://reddit.com{p_data['permalink']}"
            title = html.unescape(p_data['title'])
            if p_data.get('is_video'):
                if 'secure_media' in p_data and p_data['secure_media'] and 'reddit_video' in p_data['secure_media']:
                    video_url = html.unescape(p_data['secure_media']['reddit_video']['fallback_url']).split('?')[0]
                    audio_url = None
                    if p_data['secure_media']['reddit_video'].get('has_audio'):
                        base = video_url.rsplit('/', 1)[0]
                        audio_url = base + '/DASH_audio.mp4'
                    if audio_url:
                        memes.append({'title': title, 'video_url': video_url, 'audio_url': audio_url, 'is_video': True, 'permalink': permalink})
                    else:
                        memes.append({'title': title, 'url': video_url, 'is_video': True, 'permalink': permalink})
            elif media_url.endswith(('.jpg', '.png', '.gif')):
                memes.append({'title': title, 'url': media_url, 'is_video': False, 'permalink': permalink})
        return memes

    def get_media_info(self, path, title):
        ext = os.path.splitext(path)[1].lower()
        if ext in ('.jpg', '.png', '.gif'):
            try:
                with Image.open(path) as img:
                    width, height = img.size
                    file_size = os.path.getsize(path)
                    is_image = True
                    if ext == '.gif':
                        try:
                            img.seek(1)
                            is_image = False # Animated
                        except EOFError:
                            is_image = True
                    has_audio = False
                    duration = 0
                    bitrate = 'N/A'
                    fps = 'N/A'
                    codec = img.format.lower()
                    audio_codec = 'N/A'
                log_msg = f"Analyzed {title}: {'Image' if is_image else 'Animated GIF'}, size: {file_size / 1024:.2f} KB, resolution: {width}x{height}"
                if not is_image:
                    log_msg += f", codec: {codec}"
                self.log(log_msg)
                return {
                    'is_image': is_image,
                    'has_audio': has_audio,
                    'duration': duration,
                    'file_size': file_size,
                    'width': width,
                    'height': height
                }
            except Exception as e:
                self.log(f"Failed to analyze image {title} with PIL: {str(e)}")
                raise
        else:
            try:
                probe = ffmpeg.probe(path)
                format_info = probe.get('format', {})
                duration = float(format_info.get('duration', 0))
                file_size = int(format_info.get('size', 0))
                bitrate = int(format_info.get('bit_rate', 0)) // 1000 if 'bit_rate' in format_info else 'N/A'
                video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
                width, height, codec = 'N/A', 'N/A', 'N/A'
                fps = 'N/A'
                if video_stream:
                    width = video_stream.get('width', 'N/A')
                    height = video_stream.get('height', 'N/A')
                    codec = video_stream.get('codec_name', 'N/A')
                    fps = video_stream.get('r_frame_rate', 'N/A')
                audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
                has_audio = bool(audio_stream)
                audio_codec = audio_stream.get('codec_name', 'N/A') if audio_stream else 'N/A'
                is_image = duration == 0 or int(video_stream.get('nb_frames', 1)) <= 1
                log_msg = f"Analyzed {title}: {'Image' if is_image else 'Video'}, size: {file_size / 1024:.2f} KB, resolution: {width}x{height}, fps: {fps}"
                if not is_image:
                    log_msg += f", duration: {duration:.2f}s, bitrate: {bitrate} kbps"
                log_msg += f", video_codec: {codec}, has_audio: {has_audio}, audio_codec: {audio_codec}"
                self.log(log_msg)
                return {
                    'is_image': is_image,
                    'has_audio': has_audio,
                    'duration': duration,
                    'file_size': file_size,
                    'width': width,
                    'height': height
                }
            except ffmpeg.Error as e:
                self.log(f"Failed to probe video for {title}: FFmpeg error - {str(e)}. Check if FFmpeg is installed and in PATH.")
                raise
            except Exception as e:
                self.log(f"Failed to probe video for {title}: {str(e)}. Skipping video processing.")
                raise

    def compress_media(self, path, ext, info, title, max_size):
        file_size = info['file_size']
        if file_size <= max_size:
            return path
        self.log(f"Compressing {title} from {file_size / 1024 / 1024:.2f} MB to fit under {max_size / 1024 / 1024:.2f} MB limit")
        temp_dir = os.path.dirname(path)
        converted_path = os.path.join(temp_dir, f"compressed{ext}")
        try:
            if info['is_image']:
                with Image.open(path) as img:
                    if ext == '.jpg':
                        img.save(converted_path, quality=85, optimize=True)
                    elif ext == '.png':
                        img.save(converted_path, optimize=True, compress_level=9)
                    elif ext == '.gif':
                        if not info['is_image']:
                            self.log(f"Converting animated GIF {title} to MP4")
                            converted_path = os.path.join(temp_dir, "compressed.mp4")
                            ffmpeg.input(path).output(converted_path, vcodec='libx264', crf=28, preset='fast', format='mp4').run(overwrite_output=True)
                            ext = '.mp4'
                        else:
                            img.convert('RGB').save(converted_path.replace('.gif', '.jpg'), quality=85, optimize=True)
                            converted_path = converted_path.replace('.gif', '.jpg')
                            ext = '.jpg'
                    new_size = os.path.getsize(converted_path)
                    if new_size > max_size:
                        scale_factor = (max_size / new_size) ** 0.5 * 0.9
                        new_width = int(info['width'] * scale_factor)
                        new_height = int(info['height'] * scale_factor)
                        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
                        if ext == '.jpg':
                            resized_img.save(converted_path, quality=75, optimize=True)
                        elif ext == '.png':
                            resized_img.save(converted_path, optimize=True, compress_level=9)
            else:
                out = ffmpeg.input(path).output(
                    converted_path,
                    vcodec='libx264',
                    acodec='aac' if info['has_audio'] else None,
                    preset='fast',
                    crf=28,
                    b_v='1M',
                    b_a='128k' if info['has_audio'] else None,
                    s='640x360' if info['width'] > 640 else None,
                    format='mp4',
                    shortest=None
                )
                self.log(f"Running FFmpeg compression command: {out.compile()}")
                ffmpeg.run(out, overwrite_output=True)
            os.remove(path)
            new_info = self.get_media_info(converted_path, title)
            new_size = os.path.getsize(converted_path)
            if new_size > max_size:
                os.remove(converted_path)
                raise ValueError(f"Compressed media still too large: {new_size / 1024 / 1024:.2f} MB")
            self.log(f"Compressed {title} to {new_size / 1024 / 1024:.2f} MB")
            return converted_path
        except Exception as e:
            if os.path.exists(converted_path):
                os.remove(converted_path)
            raise ValueError(f"Compression failed: {str(e)}")

    def download_media(self, meme):
        temp_dir = tempfile.mkdtemp()
        video_path = audio_path = output_path = None
        try:
            if 'video_url' in meme and 'audio_url' in meme:
                video_url = meme['video_url']
                audio_url = meme['audio_url']
                parsed = urlparse(video_url)
                filename = os.path.basename(unquote(parsed.path))
                ext = os.path.splitext(filename)[1] or '.mp4'
                video_path = os.path.join(temp_dir, f"video{ext}")
                audio_path = os.path.join(temp_dir, "audio.mp3")
                self.log(f"Downloading video for {meme['title']} from {video_url}")
                with self.session.get(video_url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(video_path, 'wb') as f:
                        for chunk in r.iter_content(8192):
                            f.write(chunk)
                self.log(f"Downloaded video size: {os.path.getsize(video_path) / 1024:.2f} KB")
                try:
                    self.get_media_info(video_path, meme['title'] + " (video part)")
                except Exception as e:
                    self.log(f"Skipping video due to FFmpeg issue: {str(e)}")
                    raise
                self.log(f"Downloading audio for {meme['title']} from {audio_url}")
                with self.session.get(audio_url, stream=True, timeout=30) as r:
                    if r.status_code != 200:
                        self.log(f"Audio download failed with status {r.status_code}, trying alternative URLs")
                        alternative_urls = [
                            audio_url.replace('DASH_audio.mp4', 'audio.mp4'),
                            audio_url.replace('DASH_audio.mp4', 'DASH_AUDIO_128.mp4'),
                            audio_url.replace('DASH_audio.mp4', 'DASH_AUDIO_64.mp4')
                        ]
                        for alt_url in alternative_urls:
                            self.log(f"Trying alternative audio URL: {alt_url}")
                            r = self.session.get(alt_url, stream=True, timeout=30)
                            if r.status_code == 200:
                                break
                        r.raise_for_status()
                    with open(audio_path, 'wb') as f:
                        for chunk in r.iter_content(8192):
                            f.write(chunk)
                self.log(f"Downloaded audio size: {os.path.getsize(audio_path) / 1024:.2f} KB")
                output_path = os.path.join(temp_dir, f"merged.mp4")
                try:
                    inputs = [ffmpeg.input(video_path), ffmpeg.input(audio_path)]
                    out = ffmpeg.output(
                        inputs[0]['v:0'], # Select video stream from first input
                        inputs[1]['a:0'], # Select audio stream from second input
                        output_path,
                        vcodec='libx264',
                        acodec='aac',
                        preset='medium',
                        crf=23,
                        ar=44100,
                        ac=2,
                        format='mp4',
                        shortest=None
                    )
                    self.log(f"Running FFmpeg merge command: {out.compile()}")
                    ffmpeg.run(out, overwrite_output=True)
                    os.remove(video_path)
                    video_path = None
                    os.remove(audio_path)
                    audio_path = None
                    info = self.get_media_info(output_path, meme['title'] + " (merged)")
                    if not info['has_audio']:
                        self.log(f"Warning: No audio detected after merge for {meme['title']}. Attempting to post video without audio.")
                        os.remove(output_path)
                        output_path = None
                        return video_path # Fallback to video-only
                    ext = '.mp4'
                    max_size = 512 * 1024 * 1024 # Video limit for X
                    output_path = self.compress_media(output_path, ext, info, meme['title'], max_size)
                    return output_path
                except ffmpeg.Error as e:
                    self.log(f"FFmpeg merge failed for {meme['title']}: {str(e)}. Attempting to post video without audio.")
                    if os.path.exists(video_path):
                        info = self.get_media_info(video_path, meme['title'] + " (video only)")
                        ext = '.mp4'
                        max_size = 512 * 1024 * 1024
                        video_path = self.compress_media(video_path, ext, info, meme['title'], max_size)
                        return video_path
                    raise
            else:
                url = meme['url']
                parsed = urlparse(url)
                filename = os.path.basename(unquote(parsed.path))
                ext = os.path.splitext(filename)[1] or ('.mp4' if meme.get('is_video') else '.jpg')
                path = os.path.join(temp_dir, f"media{ext}")
                self.log(f"Downloading {'video' if meme.get('is_video') else 'image'} for {meme['title']} from {url}")
                with self.session.get(url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(path, 'wb') as f:
                        for chunk in r.iter_content(8192):
                            f.write(chunk)
                self.log(f"Downloaded size: {os.path.getsize(path) / 1024:.2f} KB")
                info = self.get_media_info(path, meme['title'])
                if ext.lower() in ('.jpg', '.png', '.webp'):
                    max_size = 5 * 1024 * 1024 # Image limit for X
                elif ext.lower() == '.gif':
                    max_size = 15 * 1024 * 1024 # GIF limit for X
                else:
                    max_size = 512 * 1024 * 1024 # Video limit for X
                path = self.compress_media(path, ext, info, meme['title'], max_size)
                return path
        except Exception as e:
            self.log(f"Download/processing failed for {meme['title']}: {str(e)}")
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
            if output_path and os.path.exists(output_path):
                os.remove(output_path)
            raise

    def init_api(self):
        if not self.api or not self.client:
            auth = tweepy.OAuth1UserHandler(
                self.consumer_key.get(),
                self.consumer_secret.get(),
                self.access_token.get(),
                self.access_secret.get(),
            )
            self.api = tweepy.API(auth)
            self.client = tweepy.Client(
                consumer_key=self.consumer_key.get(),
                consumer_secret=self.consumer_secret.get(),
                access_token=self.access_token.get(),
                access_token_secret=self.access_secret.get(),
            )

    def update_trending_hashtags(self, woeid: int = 1):
        now = time.time()
        if now - self.last_trending_update < 3600 and self.trending_hashtags:
            return
        try:
            self.init_api()
            trends = self.api.get_place_trends(id=woeid)
            self.trending_hashtags = [t['name'] for t in trends[0]['trends'] if t['name'].startswith('#')]
            self.last_trending_update = now
            if self.trending_hashtags:
                self.log(f"Trending hashtags refreshed: {', '.join(self.trending_hashtags[:5])}")
        except Exception as e:
            self.log(f"Trending hashtags fetch failed: {str(e)}")
            self.trending_hashtags = []
            self.last_trending_update = now

    def generate_hashtags(self, title: str, max_len: int) -> str:
        self.update_trending_hashtags()
        words = re.findall(r"\w+", title.lower())
        base_tags = ['#' + w for w in words[:3]]
        tags = []
        for tag in self.trending_hashtags:
            if tag.lower().lstrip('#') in words and tag not in tags:
                tags.append(tag)
        for tag in base_tags:
            if tag not in tags:
                tags.append(tag)
        result = ''
        for tag in tags:
            sep = ' ' if result else ''
            if len(result) + len(sep) + len(tag) <= max_len:
                result += sep + tag
            else:
                break
        return result

    def _format_tweet(self, title, permalink):
        # Obfuscated trademark string
        tm = base64.b64decode("S2F5by1NZW1lTWFnbmV0").decode('utf-8')
        source_str = f" (Source: {permalink} {tm})"
        base_len = 280 - len(source_str)
        hashtags = self.generate_hashtags(title, base_len - len(title) - 1)
        max_title_len = base_len - (len(hashtags) + 1 if hashtags else 0)
        if len(title) > max_title_len:
            title = title[:max_title_len - 3] + '...'
            hashtags = self.generate_hashtags(title, base_len - len(title) - 1)
        tweet = title
        if hashtags:
            tweet += ' ' + hashtags
        tweet += source_str
        return tweet

    def post_to_x(self, title, permalink, media_path):
        try:
            self.init_api()
            media = self.api.media_upload(media_path)
            tweet_text = self._format_tweet(title, permalink)
            self.client.create_tweet(text=tweet_text, media_ids=[media.media_id])
            self.log(f"Posted: {tweet_text}")
            return True
        except tweepy.errors.TweepyException as e:
            self.log(f"Post failed: {str(e)} for {permalink}")
            if e.response and e.response.status_code == 429:
                self.log("Rate limit hit. Waiting 15 minutes...")
                time.sleep(900)
            return False
        except Exception as e:
            self.log(f"Unexpected post error: {str(e)}")
            return False

    def run_loop(self):
        subreddits = [s.strip() for s in self.subreddits_entry.get().split(',')]
        interval = int(self.interval_entry.get()) * 60
        max_posts = int(self.max_posts_entry.get())
        min_upvotes = int(self.min_upvotes_entry.get())
        retry_delay = 300 # 5 minutes for retry if no posts
        max_retries = 3 # Maximum retries if no posts
        while self.running:
            try:
                retry_count = 0
                while self.running and retry_count <= max_retries:
                    self.status_label.configure(text="Status: Fetching...")
                    self.log(f"Starting cycle: interval {interval//60} min, max_posts {max_posts}, min_upvotes {min_upvotes}, retry {retry_count + 1}/{max_retries + 1}")
                    posted_count = 0
                    for subreddit in subreddits:
                        self.log(f"Fetching from r/{subreddit}")
                        memes = self.fetch_popular_memes(subreddit, 100, min_upvotes) # Increased limit
                        for meme in memes:
                            url_key = meme.get('url') or meme.get('video_url')
                            if url_key in self.posted_urls:
                                self.log(f"Skipping duplicate: {meme['title']}")
                                continue
                            self.log(f"Processing: {meme['title']}")
                            media_path = None
                            try:
                                media_path = self.download_media(meme)
                                if self.post_to_x(meme['title'], meme['permalink'], media_path):
                                    self.posted_urls.add(url_key)
                                    self.save_posted_urls()
                                    posted_count += 1
                                if media_path and os.path.exists(media_path):
                                    os.remove(media_path)
                            except Exception as e:
                                self.log(f"Skipped {meme['title']}: {str(e)}\n{traceback.format_exc()}")
                                if media_path and os.path.exists(media_path):
                                    os.remove(media_path)
                                continue # Continue to next meme
                            if posted_count >= max_posts:
                                break
                        if posted_count >= max_posts:
                            break
                    self.log(f"Cycle complete. Posted {posted_count} items.")
                    if posted_count > 0:
                        break # Exit retry loop if posts were made
                    retry_count += 1
                    if retry_count <= max_retries:
                        self.log(f"No new posts found. Retrying in {retry_delay / 60:.0f} minutes (retry {retry_count}/{max_retries}).")
                        self.status_label.configure(text=f"Status: Retrying in {retry_delay / 60:.0f} min")
                        for _ in range(retry_delay):
                            if not self.running:
                                self.log("Retry sleep interrupted by stop.")
                                break
                            time.sleep(1)
                    else:
                        self.log(f"Max retries ({max_retries}) reached with no new posts. Sleeping for full interval.")
                self.status_label.configure(text="Status: Sleeping")
                start_sleep = time.time()
                for _ in range(interval):
                    if not self.running:
                        self.log("Sleep interrupted by stop.")
                        break
                    time.sleep(1)
                else:
                    self.log(f"Slept for {(time.time() - start_sleep) / 60:.2f} minutes.")
            except Exception as e:
                self.log(f"Cycle error: {str(e)}\n{traceback.format_exc()}")
                time.sleep(60) # Prevent rapid looping on cycle errors
        self.status_label.configure(text="Status: Stopped")

    def start(self):
        if not self.running:
            self.running = True
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            threading.Thread(target=self.run_loop, daemon=True).start()
            self.log("Automation started.")
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
