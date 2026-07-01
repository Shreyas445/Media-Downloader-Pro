let currentData = null;
let currentOutputFolder = "";
let currentPlatform = "youtube";

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const version = await pywebview.api.get_app_version();
        document.getElementById('versionBadge').innerText = `v${version}`;
    } catch (e) {
        // Fallback
    }
});

// Platform Tab Switching
function selectPlatform(platform) {
    currentPlatform = platform;
    
    document.querySelectorAll('.platform-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.platform-tab[data-platform="${platform}"]`).classList.add('active');
    
    // Update placeholder and UI context
    const input = document.getElementById('urlInput');
    const chapterToggle = document.getElementById('chapterToggle');
    const trimToggle = document.getElementById('trimToggle');
    
    if (platform === 'youtube') {
        input.placeholder = 'Paste YouTube link here...';
        chapterToggle.style.display = 'flex';
        trimToggle.style.display = 'flex';
        document.body.setAttribute('data-platform', 'youtube');
    } else if (platform === 'instagram') {
        input.placeholder = 'Paste Instagram reel or post link...';
        chapterToggle.style.display = 'none';
        trimToggle.style.display = 'none';
        
        // Hide trimmer if active
        document.getElementById('enableTrim').checked = false;
        document.getElementById('trimmerUI').style.display = 'none';
        
        document.body.setAttribute('data-platform', 'instagram');
    }
    
    // Reset results
    document.getElementById('resultsArea').style.display = 'none';
    document.getElementById('instagramResults').style.display = 'none';
    document.getElementById('downloadStatus').style.display = 'none';
    document.getElementById('mediaPreview').style.display = 'none';
}

// Folder picker
async function chooseFolder() {
    try {
        const folderPath = await pywebview.api.select_folder();
        if (folderPath && folderPath.trim() !== '') {
            currentOutputFolder = folderPath;
            document.getElementById('folderPathText').innerText = folderPath;
        }
    } catch (e) {
        console.error("Folder selection failed:", e);
    }
}

// Auto-detect platform from URL
function autoDetectPlatform(url) {
    const lower = url.toLowerCase();
    if (lower.includes('youtube.com') || lower.includes('youtu.be')) {
        selectPlatform('youtube');
    } else if (lower.includes('instagram.com') || lower.includes('instagr.am')) {
        selectPlatform('instagram');
    }
}

// Main fetch function
async function fetchInfo() {
    const url = document.getElementById('urlInput').value.trim();
    if (!url) return;

    // Auto-detect platform from URL
    autoDetectPlatform(url);

    const btn = document.getElementById('fetchBtn');
    const spinner = document.getElementById('fetchSpinner');
    const btnText = btn.querySelector('.btn-text');

    btnText.style.display = 'none';
    spinner.style.display = 'block';
    btn.disabled = true;

    document.getElementById('resultsArea').style.display = 'none';
    document.getElementById('instagramResults').style.display = 'none';
    document.getElementById('downloadStatus').style.display = 'none';
    document.getElementById('mediaPreview').style.display = 'none';

    try {
        const response = await pywebview.api.fetch_info(url);
        
        if (response.error) {
            showError(response.error);
        } else {
            currentData = response;
            showMediaPreview(response);
            
            if (response.platform === 'instagram') {
                renderInstagramResults(response);
                document.getElementById('instagramResults').style.display = 'block';
            } else {
                renderFormats();
                document.getElementById('resultsArea').style.display = 'block';
                switchTab('video');
                
                // Reset trimmer UI
                document.getElementById('enableTrim').checked = false;
                document.getElementById('trimmerUI').style.display = 'none';
                document.getElementById('trimStart').value = '';
                document.getElementById('trimEnd').value = '';
                if (ytPlayer && ytPlayer.loadVideoById) {
                    ytPlayer.stopVideo();
                }
            }
        }
    } catch (e) {
        showError('Failed to connect to backend: ' + e);
    } finally {
        btnText.style.display = 'block';
        spinner.style.display = 'none';
        btn.disabled = false;
    }
}

// Show error with styled alert
function showError(message) {
    const statusBox = document.getElementById('downloadStatus');
    statusBox.style.display = 'block';
    updateProgress(0, '⚠️ ' + message);
}

// Show media preview (thumbnail + title)
function showMediaPreview(data) {
    const preview = document.getElementById('mediaPreview');
    const thumbnail = document.getElementById('mediaThumbnail');
    const title = document.getElementById('mediaTitle');
    const channel = document.getElementById('mediaChannel');
    
    if (data.thumbnail) {
        thumbnail.src = data.thumbnail;
        thumbnail.style.display = 'block';
    } else {
        thumbnail.style.display = 'none';
    }
    
    title.innerText = data.title || 'Media';
    channel.innerText = data.channel || data.uploader || '';
    
    preview.style.display = 'block';
}

// Format switching for YouTube
function switchTab(type) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    
    if (type === 'video') {
        document.querySelectorAll('.tab')[0].classList.add('active');
        document.getElementById('videoFormats').style.display = 'flex';
        document.getElementById('audioFormats').style.display = 'none';
    } else {
        document.querySelectorAll('.tab')[1].classList.add('active');
        document.getElementById('videoFormats').style.display = 'none';
        document.getElementById('audioFormats').style.display = 'flex';
    }
}

function formatBytes(bytes) {
    if (bytes === 0 || !bytes) return '~ Unknown';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return '~' + parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    if (!seconds) return '';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
}

// Render YouTube formats
function renderFormats() {
    const videoContainer = document.getElementById('videoFormats');
    const audioContainer = document.getElementById('audioFormats');
    
    videoContainer.innerHTML = '';
    audioContainer.innerHTML = '';

    if (!currentData.video || currentData.video.length === 0) {
        videoContainer.innerHTML = '<div class="empty-state">No video formats available</div>';
    } else {
        currentData.video.forEach(fmt => {
            videoContainer.innerHTML += createFormatCard(
                fmt.resolution,
                `${fmt.fps}fps`,
                formatBytes(fmt.filesize),
                fmt.format_id,
                'video',
                getResolutionIcon(fmt.resolution)
            );
        });
    }

    if (!currentData.audio || currentData.audio.length === 0) {
        audioContainer.innerHTML = '<div class="empty-state">No audio formats available</div>';
    } else {
        currentData.audio.forEach(fmt => {
            audioContainer.innerHTML += createFormatCard(
                fmt.bitrate,
                'MP3',
                formatBytes(fmt.filesize),
                fmt.target_bitrate,
                'audio',
                '🎵'
            );
        });
    }
}

function getResolutionIcon(res) {
    if (res.includes('2160')) return '4K';
    if (res.includes('1440')) return 'QHD';
    if (res.includes('1080')) return 'FHD';
    if (res.includes('720')) return 'HD';
    return 'SD';
}

function createFormatCard(title, subtitle, size, formatId, type, badge) {
    return `
        <div class="format-item" onclick="startDownload('${formatId}', '${type}')">
            <div class="format-badge">${badge}</div>
            <div class="format-info">
                <span class="format-title">${title}</span>
                <span class="format-subtitle">${subtitle} · ${size}</span>
            </div>
            <button class="download-btn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="18" height="18">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
            </button>
        </div>
    `;
}

// Render Instagram results
function renderInstagramResults(data) {
    const container = document.getElementById('instaMediaList');
    container.innerHTML = '';

    if (!data.media || data.media.length === 0) {
        container.innerHTML = '<div class="empty-state">No downloadable media found</div>';
        return;
    }

    data.media.forEach((item, index) => {
        const typeIcon = item.type === 'video' ? '🎬' : '🖼️';
        const typeLabel = item.type === 'video' ? 'Video' : 'Image';
        
        container.innerHTML += `
            <div class="format-item insta-item" onclick="startInstaDownload(${index})">
                <div class="format-badge insta-badge">${typeIcon}</div>
                <div class="format-info">
                    <span class="format-title">${typeLabel} ${data.media.length > 1 ? (index + 1) + ' of ' + data.media.length : ''}</span>
                    <span class="format-subtitle">${item.resolution} · ${formatBytes(item.filesize)}</span>
                </div>
                <button class="download-btn insta-download-btn">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="18" height="18">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                </button>
            </div>
        `;
    });

    // Add "Download All" button if multiple items
    if (data.media.length > 1) {
        container.innerHTML += `
            <div class="format-item download-all-item" onclick="startInstaDownloadAll()">
                <div class="format-badge">📦</div>
                <div class="format-info">
                    <span class="format-title">Download All (${data.media.length} items)</span>
                    <span class="format-subtitle">Save everything at once</span>
                </div>
                <button class="download-btn download-all-btn">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="18" height="18">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                </button>
            </div>
        `;
    }
}

// Start YouTube download
async function startDownload(formatId, type) {
    const url = document.getElementById('urlInput').value.trim();
    const splitChapters = document.getElementById('splitChapters').checked;
    
    let startTime = null;
    let endTime = null;
    
    if (document.getElementById('enableTrim').checked) {
        startTime = document.getElementById('trimStart').value;
        endTime = document.getElementById('trimEnd').value;
        
        if (startTime === "") startTime = null;
        if (endTime === "") endTime = null;
    }
    
    document.getElementById('resultsArea').style.display = 'none';
    document.getElementById('instagramResults').style.display = 'none';
    if (ytPlayer && ytPlayer.pauseVideo) ytPlayer.pauseVideo();
    
    const statusBox = document.getElementById('downloadStatus');
    statusBox.style.display = 'block';
    
    updateProgress(0, 'Starting download...');

    try {
        const result = await pywebview.api.start_download(url, formatId, type === 'audio', splitChapters, currentOutputFolder, startTime, endTime);
        if (result.error) {
            updateProgress(0, '⚠️ Error: ' + result.error);
        }
    } catch (e) {
        updateProgress(0, '⚠️ Failed: ' + e);
    }
}

// Start Instagram download for a single item
async function startInstaDownload(index) {
    const url = document.getElementById('urlInput').value.trim();
    let formatId = 'best';
    
    if (currentData && currentData.media && currentData.media[index]) {
        formatId = currentData.media[index].format_id;
    }
    
    document.getElementById('instagramResults').style.display = 'none';
    
    const statusBox = document.getElementById('downloadStatus');
    statusBox.style.display = 'block';
    
    updateProgress(0, 'Starting Instagram download...');

    try {
        const result = await pywebview.api.start_download(url, formatId, false, false, currentOutputFolder);
        if (result.error) {
            updateProgress(0, '⚠️ Error: ' + result.error);
        }
    } catch (e) {
        updateProgress(0, '⚠️ Failed: ' + e);
    }
}

// Download all Instagram media
async function startInstaDownloadAll() {
    await startInstaDownload(0); // yt-dlp handles playlists/carousels automatically
}

// Progress updater — called from Python backend
window.updateProgress = function(percent, text) {
    const bar = document.getElementById('progressBar');
    const statusText = document.getElementById('statusText');
    
    if (percent >= 0) bar.style.width = percent + '%';
    if (text) statusText.innerText = text;

    // Add success glow animation when done
    if (percent >= 100 && text && text.includes('Complete')) {
        bar.classList.add('complete');
        document.getElementById('downloadStatus').classList.add('success');
    } else {
        bar.classList.remove('complete');
        document.getElementById('downloadStatus').classList.remove('success');
    }
};

// ==========================================
// YouTube Iframe Trimmer Logic
// ==========================================

let ytPlayer = null;
let isYtApiReady = false;

function onYouTubeIframeAPIReady() {
    isYtApiReady = true;
}

function extractYouTubeId(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
}

function toggleTrimmerUI() {
    const enabled = document.getElementById('enableTrim').checked;
    const trimmerUI = document.getElementById('trimmerUI');
    
    if (enabled) {
        trimmerUI.style.display = 'block';
        
        const url = document.getElementById('urlInput').value.trim();
        const videoId = extractYouTubeId(url);
        
        if (videoId && isYtApiReady) {
            if (!ytPlayer) {
                ytPlayer = new YT.Player('ytPlayerContainer', {
                    height: '100%',
                    width: '100%',
                    videoId: videoId,
                    playerVars: {
                        'playsinline': 1,
                        'rel': 0
                    },
                    events: {
                        'onStateChange': onPlayerStateChange
                    }
                });
            } else if (ytPlayer.loadVideoById) {
                ytPlayer.loadVideoById(videoId);
                isDurationSet = false;
            }
        }
    } else {
        trimmerUI.style.display = 'none';
        if (ytPlayer && ytPlayer.pauseVideo) {
            ytPlayer.pauseVideo();
        }
    }
}

let isDurationSet = false;

let playheadInterval = null;
let isDraggingPlayhead = false;

function onPlayerStateChange(event) {
    if (event.data == 1) { // 1 = PLAYING
        if (!isDurationSet) {
            const duration = Math.floor(ytPlayer.getDuration());
            const startSlider = document.getElementById('timelineStart');
            const endSlider = document.getElementById('timelineEnd');
            const playhead = document.getElementById('timelinePlayhead');
            
            startSlider.max = duration;
            endSlider.max = duration;
            playhead.max = duration;
            
            // Only set end slider to max if we haven't touched it yet
            if (document.getElementById('trimEnd').value === "") {
                endSlider.value = duration;
                document.getElementById('trimEnd').value = duration;
            }
            
            isDurationSet = true;
            updateTimelineTrack();
        }

        // Start playhead tracking loop
        if (playheadInterval) clearInterval(playheadInterval);
        playheadInterval = setInterval(() => {
            if (!ytPlayer || !ytPlayer.getCurrentTime || isDraggingPlayhead) return;
            
            const currentTime = ytPlayer.getCurrentTime();
            const endVal = parseFloat(document.getElementById('timelineEnd').value);
            
            // Auto pause if it hits the end boundary
            if (currentTime >= endVal) {
                ytPlayer.pauseVideo();
                document.getElementById('timelinePlayhead').value = endVal;
                return;
            }
            
            document.getElementById('timelinePlayhead').value = currentTime;
        }, 100);
        
    } else {
        // Paused, Ended, Buffering, etc.
        if (playheadInterval) clearInterval(playheadInterval);
    }
}

function onPlayheadGrab() {
    isDraggingPlayhead = true;
    if (ytPlayer && ytPlayer.pauseVideo) ytPlayer.pauseVideo();
}

function onPlayheadDrag() {
    const playhead = document.getElementById('timelinePlayhead');
    if (ytPlayer && ytPlayer.seekTo) {
        ytPlayer.seekTo(parseFloat(playhead.value), true);
    }
}

function onPlayheadRelease() {
    isDraggingPlayhead = false;
    if (ytPlayer && ytPlayer.playVideo) ytPlayer.playVideo();
}

function updateTimelineTrack() {
    const startSlider = document.getElementById('timelineStart');
    const endSlider = document.getElementById('timelineEnd');
    const track = document.getElementById('timelineTrack');
    
    const max = parseFloat(startSlider.max) || 100;
    const startVal = parseFloat(startSlider.value) || 0;
    const endVal = parseFloat(endSlider.value) || max;
    
    const startPercent = (startVal / max) * 100;
    const endPercent = (endVal / max) * 100;
    
    track.style.left = startPercent + '%';
    track.style.width = (endPercent - startPercent) + '%';
}

function onTimelineDrag(type) {
    const startSlider = document.getElementById('timelineStart');
    const endSlider = document.getElementById('timelineEnd');
    
    let startVal = parseFloat(startSlider.value);
    let endVal = parseFloat(endSlider.value);
    
    if (startVal >= endVal) {
        if (type === 'start') {
            startSlider.value = endVal - 1;
            startVal = endVal - 1;
        } else {
            endSlider.value = startVal + 1;
            endVal = startVal + 1;
        }
    }
    
    document.getElementById('trimStart').value = startVal;
    document.getElementById('trimEnd').value = endVal;
    
    updateTimelineTrack();
    
    if (ytPlayer && ytPlayer.seekTo) {
        ytPlayer.seekTo(type === 'start' ? startVal : endVal, true);
    }
}

function onManualTimeInput() {
    const startInput = document.getElementById('trimStart').value;
    const endInput = document.getElementById('trimEnd').value;
    
    const startSlider = document.getElementById('timelineStart');
    const endSlider = document.getElementById('timelineEnd');
    
    if (startInput !== "") startSlider.value = startInput;
    if (endInput !== "") endSlider.value = endInput;
    
    updateTimelineTrack();
}

function setTrimTime(type) {
    if (!ytPlayer || !ytPlayer.getCurrentTime) return;
    
    const currentTime = Math.floor(ytPlayer.getCurrentTime());
    
    if (type === 'start') {
        document.getElementById('trimStart').value = currentTime;
        document.getElementById('timelineStart').value = currentTime;
    } else {
        document.getElementById('trimEnd').value = currentTime;
        document.getElementById('timelineEnd').value = currentTime;
    }
    
    updateTimelineTrack();
}

// Allow Enter key to trigger analysis
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && document.activeElement.id === 'urlInput') {
        fetchInfo();
    }
});
