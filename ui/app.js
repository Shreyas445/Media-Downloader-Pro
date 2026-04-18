let currentData = null;
let currentOutputFolder = "";

// Bind folder picker
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

async function fetchInfo() {
    const url = document.getElementById('urlInput').value.trim();
    if (!url) return;

    const btn = document.getElementById('fetchBtn');
    const spinner = document.getElementById('fetchSpinner');
    const btnText = btn.querySelector('.btn-text');

    btnText.style.display = 'none';
    spinner.style.display = 'block';
    btn.disabled = true;

    document.getElementById('resultsArea').style.display = 'none';
    document.getElementById('downloadStatus').style.display = 'none';

    try {
        const response = await pywebview.api.fetch_info(url);
        
        if (response.error) {
            alert('Error: ' + response.error);
        } else {
            currentData = response;
            renderFormats();
            document.getElementById('resultsArea').style.display = 'block';
            switchTab('video');
        }
    } catch (e) {
        alert('Failed to connect to backend: ' + e);
    } finally {
        btnText.style.display = 'block';
        spinner.style.display = 'none';
        btn.disabled = false;
    }
}

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
    if (bytes === 0 || !bytes) return 'Unknown Size';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function renderFormats() {
    const videoContainer = document.getElementById('videoFormats');
    const audioContainer = document.getElementById('audioFormats');
    
    videoContainer.innerHTML = '';
    audioContainer.innerHTML = '';

    // Render Video Details
    if (currentData.video.length === 0) {
        videoContainer.innerHTML = '<div class="status-text">No video formats found.</div>';
    } else {
        currentData.video.forEach(fmt => {
            videoContainer.innerHTML += createFormatHTML(
                `${fmt.resolution} (${fmt.fps}fps)`,
                formatBytes(fmt.filesize),
                fmt.format_id,
                'video'
            );
        });
    }

    // Render Audio Details
    if (currentData.audio.length === 0) {
        audioContainer.innerHTML = '<div class="status-text">No audio formats found.</div>';
    } else {
        currentData.audio.forEach(fmt => {
            audioContainer.innerHTML += createFormatHTML(
                `${fmt.bitrate} MP3`,
                formatBytes(fmt.filesize),
                fmt.target_bitrate,
                'audio'
            );
        });
    }
}

function createFormatHTML(title, size, formatId, type) {
    return `
        <div class="format-item">
            <div class="format-info">
                <span class="format-title">${title}</span>
                <span class="format-size">${size}</span>
            </div>
            <button class="download-btn" onclick="startDownload('${formatId}', '${type}')">Download</button>
        </div>
    `;
}

async function startDownload(formatId, type) {
    const url = document.getElementById('urlInput').value.trim();
    const splitChapters = document.getElementById('splitChapters').checked;
    
    document.getElementById('resultsArea').style.display = 'none';
    
    const statusBox = document.getElementById('downloadStatus');
    statusBox.style.display = 'block';
    
    updateProgress(0, 'Starting download...');

    try {
        const result = await pywebview.api.start_download(url, formatId, type === 'audio', splitChapters, currentOutputFolder);
        if (result.error) {
            updateProgress(0, 'Error: ' + result.error);
        }
    } catch (e) {
        updateProgress(0, 'Failed: ' + e);
    }
}

// Called by Python backend to update progress
window.updateProgress = function(percent, text) {
    const bar = document.getElementById('progressBar');
    const statusText = document.getElementById('statusText');
    
    if (percent >= 0) bar.style.width = percent + '%';
    if (text) statusText.innerText = text;
};
