import yt_dlp
import os
import re
import webview
import threading
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class YoutubeDownloaderAPI:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

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
                if rest_of_name:
                    new_name = f"{rest_of_name}_{number}"
                else:
                    new_name = number
            
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
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            video_formats = []
            audio_formats = []
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                formats = info.get('formats', [])
                
                # Best Audio format size (for approximating video+audio total size)
                best_audio = None
                for f in formats:
                    if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                        if not best_audio or f.get('filesize', 0) > best_audio.get('filesize', 0):
                            best_audio = f
                            
                best_audio_size = best_audio.get('filesize') or best_audio.get('filesize_approx') or 0

                # Process Video Formats (MP4 only for simplicity)
                for f in formats:
                    if f.get('ext') == 'mp4' and f.get('vcodec') != 'none':
                        res = f.get('height', 0)
                        if res in [2160, 1440, 1080, 720, 480]: # 4K down to 480p
                            size = f.get('filesize') or f.get('filesize_approx') or 0
                            # If video only stream, add audio size
                            if f.get('acodec') == 'none':
                                size += best_audio_size
                                
                            video_formats.append({
                                'format_id': f"{f['format_id']}+bestaudio",
                                'resolution': f"{res}p",
                                'fps': f.get('fps', 30),
                                'filesize': size
                            })

                # Deduplicate Video by Resolution (keep highest FPS/bitrate)
                video_dict = {}
                for f in video_formats:
                    # Prefer higher FPS if same resolution
                    key = f['resolution']
                    if key not in video_dict or video_dict[key]['fps'] < f['fps']:
                        video_dict[key] = f
                
                # Sort videos desc by resolution integer
                sorted_videos = sorted(
                    list(video_dict.values()), 
                    key=lambda x: int(x['resolution'].replace('p', '')), 
                    reverse=True
                )

                # Process Audio Formats
                for f in [128, 192, 256, 320]:
                    # We will just let yt_dlp extract the best audio and convert it to the requested bitrate using FFmpeg.
                    # Estimate size: (bitrate * 1000 / 8) * duration
                    duration = info.get('duration', 0)
                    approx_bytes = (f * 1000 / 8) * duration
                    
                    audio_formats.append({
                        'format_id': 'bestaudio/best', # The backend will use FFmpeg to force this bitrate
                        'bitrate': f"{f}kbps",
                        'target_bitrate': str(f),
                        'filesize': approx_bytes
                    })

                return {
                    'video': sorted_videos,
                    'audio': audio_formats
                }
        except Exception as e:
            return {'error': str(e)}

    def start_download(self, url, format_id, is_audio, split_chapters, output_folder):
        # We start this in a new thread so we can return success immediately to JS and not block the UI
        thread = threading.Thread(target=self._download_thread, args=(url, format_id, is_audio, split_chapters, output_folder))
        thread.start()
        return {'status': 'started'}

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0%')
            percent_str = re.sub(r'\x1b\[[0-9;]*m', '', percent_str).strip()
            
            speed = d.get('_speed_str', '')
            speed = re.sub(r'\x1b\[[0-9;]*m', '', speed).strip()

            try:
                percent = float(percent_str.replace('%', ''))
                if self._window:
                    self._window.evaluate_js(f"window.updateProgress({percent}, 'Downloading... {speed}')")
            except:
                pass
        elif d['status'] == 'finished':
            if self._window:
                self._window.evaluate_js(f"window.updateProgress(100, 'Processing file (this may take a moment)...')")

    def _download_thread(self, url, format_id, is_audio, split_chapters, output_folder):
        # Use user chosen output folder or default and make sure it exists
        if not output_folder:
            output_folder = os.path.join(os.path.expanduser("~"), "Downloads")
            
        os.makedirs(output_folder, exist_ok=True)

        ydl_opts = {
            'js_runtimes': {'node': {}},
            'remote_components': ['ejs:github'],
            'outtmpl': {
                'chapter': os.path.join(output_folder, '%(section_title)s.%(ext)s'),
                'default': os.path.join(output_folder, '%(title)s.%(ext)s')
            },
            'progress_hooks': [self._progress_hook],
            'keepvideo': False,
            'postprocessors': []
        }

        # Handle Audio logic
        if is_audio:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': format_id if format_id else '192', 
            })
        else:
            ydl_opts['format'] = format_id # e.g. "137+bestaudio"
            ydl_opts['merge_output_format'] = 'mp4'

        if split_chapters:
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
                ydl.download([url])
            
            self.clean_filenames(output_folder)
            
            if self._window:
                self._window.evaluate_js(f"window.updateProgress(100, 'Download Complete! 🎉 Files saved in ./downloads')")
        except Exception as e:
            if self._window:
                self._window.evaluate_js(f"window.updateProgress(0, 'Error: {str(e)}')")

if __name__ == '__main__':
    api = YoutubeDownloaderAPI()
    
    # We load the ui relative to the executable if bundled, or from folder
    ui_path = resource_path('ui/index.html')
    icon_path = resource_path('icon.ico')

    window = webview.create_window(
        'Media Downloader Pro', 
        url=f'file://{ui_path}', 
        js_api=api,
        width=700, 
        height=650,
        resizable=False,
        background_color='#1a1b1e'
    )
    
    api.set_window(window)
    # The icon parameter isn't officially supported in pure create_window in this manner natively across all OSs, 
    # but PyInstaller will manage the app taskbar icon via the executable itself. 
    import platform
    if sys.platform == 'win32':
        import ctypes
        myappid = 'mediadownloader.pro.v1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
    webview.start(debug=False, icon=icon_path if os.path.exists(icon_path) else None)