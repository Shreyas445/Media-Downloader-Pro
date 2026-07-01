import yt_dlp
import instaloader
import os
import re
import webview
import threading
import sys
import webbrowser
import urllib.request

APP_VERSION = "2.0.0"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_ffmpeg_path():
    """ Locate ffmpeg.exe in bundled directories or system path. """
    search_dirs = []
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        search_dirs.extend([
            os.path.join(exe_dir, 'tools'),
            os.path.join(exe_dir, 'tools', 'ffmpeg'),
            exe_dir,
        ])
        if hasattr(sys, '_MEIPASS'):
            search_dirs.extend([
                os.path.join(sys._MEIPASS, 'tools'),
                os.path.join(sys._MEIPASS, 'tools', 'ffmpeg'),
                sys._MEIPASS,
            ])
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
        search_dirs.extend([
            os.path.join(exe_dir, 'tools'),
            os.path.join(exe_dir, 'tools', 'ffmpeg'),
            exe_dir,
        ])

    for d in search_dirs:
        if os.path.isfile(os.path.join(d, 'ffmpeg.exe')):
            return d
    return None


def detect_platform(url):
    """Detect which platform a URL belongs to."""
    url_lower = url.lower().strip()
    if any(domain in url_lower for domain in ['youtube.com', 'youtu.be', 'youtube-nocookie.com']):
        return 'youtube'
    elif any(domain in url_lower for domain in ['instagram.com', 'instagr.am']):
        return 'instagram'
    else:
        return 'unknown'


# =====================================================================
# DOWNLOADER ENGINES (insta-dl & hikari-instagram-downloader philosophy)
# =====================================================================

class NullLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

class YtDlpEngine:
    """Engine using yt-dlp to extract metadata."""
    def __init__(self, ffmpeg_path):
        self._ffmpeg_path = ffmpeg_path

    def _get_opts(self):
        opts = {'quiet': True, 'no_warnings': True, 'logger': NullLogger()}
        if self._ffmpeg_path:
            opts['ffmpeg_location'] = self._ffmpeg_path
        return opts

    def fetch_info(self, url):
        platform = detect_platform(url)
        ydl_opts = self._get_opts()
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if platform == 'youtube':
                return self._parse_youtube(info)
            elif platform == 'instagram':
                return self._parse_instagram(info)
            else:
                return self._parse_generic(info)

    def _parse_youtube(self, info):
        formats = info.get('formats', [])
        video_formats = []
        audio_formats = []
        
        best_audio = max(
            [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none'],
            key=lambda f: f.get('filesize', 0) or f.get('filesize_approx', 0),
            default=None
        )
        best_audio_size = best_audio.get('filesize', 0) or best_audio.get('filesize_approx', 0) if best_audio else 0

        for f in formats:
            vcodec = f.get('vcodec')
            if vcodec and vcodec != 'none':
                h = f.get('height') or 0
                w = f.get('width') or 0
                # For vertical Shorts/Reels, height is larger than width (e.g., 1080x1920)
                # The standard resolution label (1080p, 720p, etc.) is min(w, h)
                res = min(w, h) if (w > 0 and h > 0) else (h or w)
                if res >= 144:
                    if 2000 <= res <= 2200: res = 2160
                    elif 1400 <= res <= 1500: res = 1440
                    elif 1000 <= res <= 1100: res = 1080
                    elif 700 <= res <= 750: res = 720
                    elif 470 <= res <= 500: res = 480
                    elif 350 <= res <= 370: res = 360
                    elif 230 <= res <= 250: res = 240

                    size = f.get('filesize', 0) or f.get('filesize_approx', 0)
                    acodec = f.get('acodec', 'none')
                    if acodec == 'none' or acodec is None:
                        size += best_audio_size
                        format_id = f"{f['format_id']}+bestaudio"
                    else:
                        format_id = f['format_id']
                        
                    video_formats.append({
                        'format_id': format_id,
                        'resolution': f"{res}p",
                        'fps': f.get('fps') or 30,
                        'filesize': size,
                        'ext': f.get('ext', '')
                    })

        video_dict = {}
        for f in video_formats:
            key = f['resolution']
            if key not in video_dict:
                video_dict[key] = f
            else:
                curr = video_dict[key]
                f_is_mp4 = (f['ext'] == 'mp4')
                curr_is_mp4 = (curr['ext'] == 'mp4')
                if (f_is_mp4 and not curr_is_mp4) or (f_is_mp4 == curr_is_mp4 and f['fps'] > curr['fps']):
                    video_dict[key] = f
        
        sorted_videos = sorted(
            list(video_dict.values()), 
            key=lambda x: int(x['resolution'].replace('p', '')), 
            reverse=True
        )

        if not sorted_videos:
            sorted_videos.append({
                'format_id': 'bestvideo+bestaudio/best',
                'resolution': 'Best Quality',
                'fps': 30,
                'filesize': 0
            })

        for f in [128, 192, 256, 320]:
            duration = info.get('duration', 0)
            approx_bytes = (f * 1000 / 8) * duration
            audio_formats.append({
                'format_id': 'bestaudio/best',
                'bitrate': f"{f}kbps",
                'target_bitrate': str(f),
                'filesize': approx_bytes
            })

        return {
            'platform': 'youtube',
            'title': info.get('title', 'Unknown'),
            'thumbnail': info.get('thumbnail', ''),
            'duration': info.get('duration', 0),
            'channel': info.get('uploader', 'Unknown'),
            'video': sorted_videos,
            'audio': audio_formats
        }

    def _parse_instagram(self, info):
        entries = info.get('entries', [info]) if info.get('_type') == 'playlist' else [info]
        media_items = []
        for i, entry in enumerate(entries):
            item = {
                'index': i,
                'title': entry.get('title', entry.get('description', 'Instagram Media'))[:80],
                'thumbnail': entry.get('thumbnail', ''),
                'type': 'video' if entry.get('ext') in ['mp4', 'webm'] or entry.get('vcodec') != 'none' else 'image',
            }
            formats = entry.get('formats', [])
            best = max(formats, key=lambda f: (f.get('height') or 0) * (f.get('width') or 0), default=None) if formats else None
            
            item['format_id'] = best.get('format_id', 'best') if best else 'best'
            item['resolution'] = f"{best.get('height', '?')}p" if best and best.get('height') else 'Best'
            item['filesize'] = best.get('filesize', 0) or best.get('filesize_approx', 0) if best else 0
            media_items.append(item)

        return {
            'platform': 'instagram',
            'title': info.get('title', info.get('description', 'Instagram Post'))[:80],
            'thumbnail': info.get('thumbnail', entries[0].get('thumbnail', '') if entries else ''),
            'uploader': info.get('uploader', info.get('uploader_id', 'Unknown')),
            'media': media_items
        }

    def _parse_generic(self, info):
        video_formats = []
        formats = info.get('formats', [])
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('height'):
                video_formats.append({
                    'format_id': f.get('format_id', 'best'),
                    'resolution': f"{f.get('height', '?')}p",
                    'fps': f.get('fps', 30),
                    'filesize': f.get('filesize', 0) or f.get('filesize_approx', 0)
                })

        video_dict = {}
        for f in video_formats:
            key = f['resolution']
            if key not in video_dict or video_dict[key].get('fps', 0) < f.get('fps', 0):
                video_dict[key] = f

        sorted_videos = sorted(
            list(video_dict.values()),
            key=lambda x: int(x['resolution'].replace('p', '').replace('?', '0')),
            reverse=True
        )

        if not sorted_videos:
            sorted_videos.append({
                'format_id': 'bestvideo+bestaudio/best',
                'resolution': 'Best Quality',
                'fps': 30,
                'filesize': 0
            })

        return {
            'platform': 'generic',
            'title': info.get('title', 'Unknown'),
            'thumbnail': info.get('thumbnail', ''),
            'video': sorted_videos,
            'audio': [{
                'format_id': 'bestaudio/best',
                'bitrate': '192kbps',
                'target_bitrate': '192',
                'filesize': 0
            }]
        }


class InstaloaderEngine:
    """Engine using the Instaloader API queries for high-quality Instagram parsing."""
    def __init__(self):
        self.L = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True
        )

    def fetch_info(self, url):
        match = re.search(r'/(?:p|reel|reels|tv)/([^/?#]+)', url)
        if not match:
            return None
        shortcode = match.group(1)
        
        post = instaloader.Post.from_shortcode(self.L.context, shortcode)
        
        media_items = []
        if post.typename == 'GraphSidecar':
            for i, node in enumerate(post.get_sidecar_nodes()):
                media_items.append({
                    'index': i,
                    'title': f"Slide {i+1}",
                    'thumbnail': node.display_url,
                    'type': 'video' if node.is_video else 'image',
                    'format_id': node.video_url if node.is_video else node.display_url,
                    'resolution': 'Best',
                    'filesize': 0
                })
        else:
            media_items.append({
                'index': 0,
                'title': post.title or post.caption or 'Instagram Post',
                'thumbnail': post.url,
                'type': 'video' if post.is_video else 'image',
                'format_id': post.video_url if post.is_video else post.url,
                'resolution': 'Best',
                'filesize': 0
            })
            
        return {
            'platform': 'instagram',
            'title': (post.title or post.caption or 'Instagram Post')[:80],
            'thumbnail': post.url,
            'uploader': post.owner_username,
            'media': media_items
        }


class ProxyScraperEngine:
    """Proxy engine parsing meta tags from multiple mirror proxies (fallback of last resort)."""
    def fetch_info(self, url):
        match = re.search(r'/(?:p|reel|reels|tv)/([^/?#]+)', url)
        if not match:
            return None
        
        shortcode = match.group(1)
        is_reel = '/reel/' in url or '/reels/' in url
        path_type = 'reel' if is_reel else 'p'
        
        # Multiple proxies to try if one is down or blocked
        proxies = [
            "https://ddinstagram.com",
            "https://www.ddinstagram.com",
            "https://vxinstagram.com",
            "https://d.vxinstagram.com",
            "https://fxig.seria.moe"
        ]
        
        # Use Discord bot user agent so the proxies return simple OG tags instead of blocking us
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11.6; rv:92.0) Gecko/20100101 Firefox/92.0 Discordbot/2.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        for proxy in proxies:
            dd_url = f"{proxy}/{path_type}/{shortcode}/"
            req = urllib.request.Request(dd_url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    html = response.read().decode('utf-8', errors='ignore')
                    
                    video_match = re.search(r'<meta[^>]*property=["\']og:video["\'][^>]*content=["\']([^"\']+)["\']', html)
                    if not video_match:
                        video_match = re.search(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:video["\']', html)
                        
                    image_match = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html)
                    if not image_match:
                        image_match = re.search(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', html)
                        
                    title_match = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', html)
                    if not title_match:
                        title_match = re.search(r'<title>([^<]+)</title>', html)
                        
                    title = title_match.group(1) if title_match else 'Instagram Media'
                    title = re.sub(r'\s+', ' ', title).strip()
                    if title.endswith('on Instagram'):
                        title = title.split('on Instagram')[0].strip()
                    
                    if video_match:
                        video_url = video_match.group(1).replace('&amp;', '&')
                        thumb_url = image_match.group(1).replace('&amp;', '&') if image_match else ''
                        return {
                            'platform': 'instagram',
                            'title': title[:80],
                            'thumbnail': thumb_url,
                            'uploader': 'Instagram',
                            'media': [{
                                'index': 0,
                                'title': title[:80],
                                'thumbnail': thumb_url,
                                'type': 'video',
                                'format_id': video_url,
                                'resolution': 'Best',
                                'filesize': 0
                            }]
                        }
                    elif image_match:
                        image_url = image_match.group(1).replace('&amp;', '&')
                        return {
                            'platform': 'instagram',
                            'title': title[:80],
                            'thumbnail': image_url,
                            'uploader': 'Instagram',
                            'media': [{
                                'index': 0,
                                'title': title[:80],
                                'thumbnail': image_url,
                                'type': 'image',
                                'format_id': image_url,
                                'resolution': 'Best',
                                'filesize': 0
                            }]
                        }
            except Exception as e:
                print(f"[Debug] Proxy {proxy} failed: {e}")
                continue
                
        return None


# =====================================================================
# MAIN WINDOW API LAYER
# =====================================================================

class MediaDownloaderAPI:
    def __init__(self):
        self._window = None
        self._ffmpeg_path = get_ffmpeg_path()
        
        # Initialize engines
        self.ytdlp_engine = YtDlpEngine(self._ffmpeg_path)
        self.instaloader_engine = InstaloaderEngine()
        self.proxy_engine = ProxyScraperEngine()

    def set_window(self, window):
        self._window = window

    def get_app_version(self):
        return APP_VERSION

    def get_platform(self, url):
        return detect_platform(url)

    def open_link(self, url):
        webbrowser.open(url)

    def clean_filenames(self, folder_path):
        for filename in os.listdir(folder_path):
            if not (filename.endswith(".mp3") or filename.endswith(".mp4")):
                continue
                
            old_path = os.path.join(folder_path, filename)
            name, ext = os.path.splitext(filename)
            new_name = name.lower().replace(" ", "_")
            match = re.match(r'^(\d+)_*(.*)', new_name)
            if match:
                number = match.group(1)
                rest_of_name = match.group(2)
                new_name = f"{rest_of_name}_{number}" if rest_of_name else number
            
            new_name = re.sub(r'_+', '_', new_name).strip('_')
            new_path = os.path.join(folder_path, new_name + ext)
            
            if old_path != new_path:
                counter = 1
                while os.path.exists(new_path):
                    new_path = os.path.join(folder_path, f"{new_name}_{counter}{ext}")
                    counter += 1
                os.rename(old_path, new_path)

    def select_folder(self):
        if self._window:
            result = self._window.create_file_dialog(webview.FileDialog.FOLDER)
            if result and len(result) > 0:
                return result[0]
        return ""

    def fetch_info(self, url):
        platform = detect_platform(url)
        
        # 1. YouTube goes straight to yt-dlp
        if platform == 'youtube':
            try:
                return self.ytdlp_engine.fetch_info(url)
            except Exception as e:
                return {'error': self._clean_error(e)}
                
        # 2. Instagram runs Fallback Pipeline (yt-dlp -> instaloader -> proxy)
        elif platform == 'instagram':
            # Engine 1: Try YtDlp
            try:
                data = self.ytdlp_engine.fetch_info(url)
                if data: return data
                raise ValueError("Engine returned None")
            except Exception:
                print("[Fallback] yt-dlp blocked. Switching to Instaloader...")
                
                # Engine 2: Try Instaloader API query
                try:
                    data = self.instaloader_engine.fetch_info(url)
                    if data: return data
                    raise ValueError("Engine returned None")
                except Exception:
                    print("[Fallback] Instaloader blocked. Switching to ddinstagram proxy...")
                    
                    # Engine 3: Try Proxy Scraping
                    try:
                        data = self.proxy_engine.fetch_info(url)
                        if data:
                            return data
                        raise ValueError("Engine returned None")
                    except Exception as e3:
                        print(f"[Fallback] ddinstagram proxy failed: {e3}")
            
            print("[Error] All 3 Instagram engines failed.")
            return {'error': 'Failed to retrieve media. Instagram is currently blocking requests.'}
            
        # 3. Generic handler
        else:
            try:
                return self.ytdlp_engine.fetch_info(url)
            except Exception as e:
                return {'error': self._clean_error(e)}

    def _clean_error(self, e):
        error_msg = str(e)
        error_msg = re.sub(r'(?:\x1b|\\x1b|[\u001b\u009b])\[[0-9;]*[a-zA-Z]', '', error_msg)
        error_msg = re.sub(r'(?i)^error:\s*', '', error_msg).strip()
        if 'login' in error_msg.lower() or 'private' in error_msg.lower():
            return 'This content is private or requires login.'
        elif 'not found' in error_msg.lower() or '404' in error_msg:
            return 'Content not found. Please check the URL.'
        elif 'ffmpeg' in error_msg.lower():
            return 'FFmpeg is missing. Please reinstall.'
        return error_msg

    def start_download(self, url, format_id, is_audio, split_chapters, output_folder, start_time=None, end_time=None):
        thread = threading.Thread(
            target=self._download_thread, 
            args=(url, format_id, is_audio, split_chapters, output_folder, start_time, end_time)
        )
        thread.start()
        return {'status': 'started'}

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str') or '0%'
            percent_str = re.sub(r'(?:\x1b|\\x1b|[\u001b\u009b])\[[0-9;]*[a-zA-Z]', '', str(percent_str)).strip()
            speed = d.get('_speed_str') or ''
            speed = re.sub(r'(?:\x1b|\\x1b|[\u001b\u009b])\[[0-9;]*[a-zA-Z]', '', str(speed)).strip()

            try:
                percent = float(percent_str.replace('%', ''))
                if self._window:
                    self._window.evaluate_js(f"window.updateProgress({percent}, 'Downloading... {speed}')")
            except:
                pass
        elif d['status'] == 'finished':
            if self._window:
                self._window.evaluate_js(f"window.updateProgress(100, 'Processing file...')")

    def _download_thread(self, url, format_id, is_audio, split_chapters, output_folder, start_time=None, end_time=None):
        if not output_folder:
            output_folder = os.path.join(os.path.expanduser("~"), "Downloads")
            
        os.makedirs(output_folder, exist_ok=True)

        ydl_opts = {
            'progress_hooks': [self._progress_hook],
            'keepvideo': False,
            'postprocessors': [],
            'quiet': True,
            'no_warnings': True,
            'logger': NullLogger(),
            'overwrites': True,
        }

        if self._ffmpeg_path:
            ydl_opts['ffmpeg_location'] = self._ffmpeg_path

        # Determine if we are trimming
        is_trimming = (start_time is not None or end_time is not None)
        start_sec = 0.0
        end_sec = float('inf')

        if is_trimming:
            try:
                start_sec = float(start_time) if start_time else 0.0
                end_sec = float(end_time) if end_time else float('inf')
                from yt_dlp.utils import download_range_func
                ydl_opts['download_ranges'] = download_range_func(None, [(start_sec, end_sec)])
            except Exception:
                is_trimming = False

        # Build output filename
        trim_suffix = ""
        if is_trimming:
            trim_suffix = f"_trim_{int(start_sec)}s-{int(end_sec)}s"

        # If format_id is a direct URL link (from fallback engines), download it directly
        download_url = url
        if format_id.startswith('http://') or format_id.startswith('https://'):
            download_url = format_id
            ydl_opts['format'] = 'best'
            
            match = re.search(r'/(?:p|reel|reels|tv)/([^/?#]+)', url)
            shortcode = match.group(1) if match else 'media'
            ext = 'jpg' if ('.jpg' in download_url or '.webp' in download_url) else 'mp4'
            ydl_opts['outtmpl'] = {
                'default': os.path.join(output_folder, f'instagram_{shortcode}.{ext}')
            }
        else:
            ydl_opts['outtmpl'] = {
                'chapter': os.path.join(output_folder, f'%(section_title)s{trim_suffix}.%(ext)s'),
                'default': os.path.join(output_folder, f'%(title)s{trim_suffix}.%(ext)s')
            }

        # Apply standard Audio/Video options
        platform = detect_platform(url)
        if is_audio:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': format_id if format_id and not format_id.startswith('http') else '192', 
            })
        else:
            if not download_url.startswith('http'):
                if platform == 'instagram':
                    ydl_opts['format'] = 'best'
                else:
                    ydl_opts['format'] = format_id
                    ydl_opts['merge_output_format'] = 'mp4'

        if split_chapters and platform == 'youtube':
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegMetadata',
                'add_chapters': True,
                'add_metadata': True,
            })
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegSplitChapters',
                'force_keyframes': False,
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(download_url, download=True)

            # If any video download outputs as webm/mkv (e.g., Shorts, AV1, or trimmed clips),
            # convert to universally compatible H.264+AAC MP4.
            if not is_audio:
                downloaded = None
                rd = info.get('requested_downloads', [])
                if rd:
                    downloaded = rd[0].get('filepath', '')
                if not downloaded:
                    import glob
                    pattern_suffix = trim_suffix if is_trimming else ""
                    matches = glob.glob(os.path.join(output_folder, f'*{pattern_suffix}.*'))
                    video_matches = [m for m in matches if m.endswith(('.webm', '.mkv', '.mp4'))]
                    if video_matches:
                        downloaded = max(video_matches, key=os.path.getmtime)

                if downloaded and not downloaded.endswith('.mp4') and os.path.isfile(downloaded):
                    mp4_path = os.path.splitext(downloaded)[0] + '.mp4'
                    ffmpeg_exe = 'ffmpeg'
                    if self._ffmpeg_path:
                        candidate = os.path.join(self._ffmpeg_path, 'ffmpeg.exe')
                        if os.path.isfile(candidate):
                            ffmpeg_exe = candidate

                    import subprocess
                    subprocess.run(
                        [ffmpeg_exe, '-i', downloaded,
                         '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
                         '-c:a', 'aac', '-b:a', '192k',
                         '-movflags', '+faststart',
                         '-y', mp4_path],
                        capture_output=True, timeout=600
                    )
                    if os.path.isfile(mp4_path) and os.path.getsize(mp4_path) > 0:
                        os.remove(downloaded)

            self.clean_filenames(output_folder)
            
            if self._window:
                self._window.evaluate_js(f"window.updateProgress(100, 'Download Complete! 🎉')")
        except Exception as e:
            error_msg = str(e)
            error_msg = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', error_msg)
            error_msg = re.sub(r'(?i)^error:\s*', '', error_msg).strip()
            error_msg = error_msg.replace("'", "\\'").replace('"', '\\"')
            if self._window:
                self._window.evaluate_js(f"window.updateProgress(0, 'Error: {error_msg}')")


if __name__ == '__main__':
    api = MediaDownloaderAPI()
    ui_path = resource_path('ui/index.html')
    icon_path = resource_path('icon.ico')

    window = webview.create_window(
        'Media Downloader Pro', 
        url=ui_path, 
        js_api=api,
        width=750, 
        height=700,
        resizable=False,
        background_color='#090a0f'
    )
    
    api.set_window(window)

    if sys.platform == 'win32':
        import ctypes
        myappid = 'antigravity.mediadownloaderpro.v2'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
    webview.start(debug=False, http_server=True, icon=icon_path if os.path.exists(icon_path) else None)