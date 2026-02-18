from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
import socket
from pathlib import Path
import logging

app = Flask(__name__)
CORS(app)

# Clean logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Download directory
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

class QuietLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): logger.error(f"❌ {msg}")

def find_free_port(start_port=5000, max_attempts=10):
    """Find available port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            continue
    return start_port

def kill_port_process(port):
    """Kill process on port"""
    try:
        os.system(f"lsof -ti:{port} | xargs kill -9 2>/dev/null")
        return True
    except:
        return False

def get_video_info(url):
    """Get video info and available qualities with direct URLs"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'logger': QuietLogger(),
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract available formats with direct URLs
            formats = []
            seen_qualities = {}
            
            if 'formats' in info:
                for f in info['formats']:
                    # Video formats
                    if f.get('height') and f.get('vcodec') != 'none' and f.get('url'):
                        quality = f'{f["height"]}p'
                        current_size = f.get('filesize') or 0
                        existing_size = seen_qualities.get(quality, {}).get('filesize') or 0
                        
                        if quality not in seen_qualities or current_size > existing_size:
                            seen_qualities[quality] = {
                                'quality': quality,
                                'height': f['height'],
                                'ext': f.get('ext', 'mp4'),
                                'filesize': current_size,
                                'filesize_mb': f"{current_size / (1024*1024):.1f} MB" if current_size > 0 else "Unknown",
                                'direct_url': f['url'],
                                'format_note': f.get('format_note', ''),
                                'fps': f.get('fps', 0)
                            }
                
                # Audio formats
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('url'):
                        current_abr = f.get('abr') or 0
                        existing_abr = seen_qualities.get('audio', {}).get('abr') or 0
                        
                        if 'audio' not in seen_qualities or current_abr > existing_abr:
                            filesize = f.get('filesize') or 0
                            seen_qualities['audio'] = {
                                'quality': 'audio',
                                'ext': f.get('ext', 'm4a'),
                                'filesize': filesize,
                                'filesize_mb': f"{filesize / (1024*1024):.1f} MB" if filesize > 0 else "Unknown",
                                'direct_url': f['url'],
                                'abr': current_abr
                            }
                
                formats = list(seen_qualities.values())
                formats.sort(key=lambda x: x.get('height', 0), reverse=True)
            
            duration_mins = info.get('duration', 0) // 60
            duration_secs = info.get('duration', 0) % 60
            
            return {
                'success': True,
                'title': info.get('title', 'Unknown'),
                'duration': f"{duration_mins}:{duration_secs:02d}",
                'duration_seconds': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'formats': formats
            }
    except Exception as e:
        logger.error(f"Error getting info: {str(e)}")
        return {'success': False, 'error': str(e)}

def download_video(url, quality='720p'):
    """Download and return file path"""
    
    if quality == 'best':
        format_selector = 'best[ext=mp4]/best'
    elif quality == 'audio':
        format_selector = 'bestaudio[ext=m4a]/bestaudio'
    else:
        height = quality.replace('p', '')
        format_selector = f'best[height<={height}][ext=mp4]/best[height<={height}]'
    
    output_template = str(DOWNLOAD_DIR / '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': format_selector,
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'logger': QuietLogger(),
    }
    
    if quality == 'audio':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    
    try:
        logger.info(f"⬇️  Downloading: {quality}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            if quality == 'audio':
                filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
            else:
                filename = ydl.prepare_filename(info)
            
            logger.info(f"✅ Downloaded: {os.path.basename(filename)}")
            
            return {
                'success': True,
                'filepath': filename,
                'filename': os.path.basename(filename),
                'title': info.get('title', 'Unknown')
            }
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        return {'success': False, 'error': str(e)}

@app.route('/', methods=['GET'])
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YouTube Downloader API 🎬</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
                color: #333;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                text-align: center;
                color: #667eea;
                margin-bottom: 10px;
                font-size: 2.5em;
            }
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 40px;
                font-size: 1.1em;
            }
            .section {
                background: #f8f9fa;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 25px;
                border-left: 5px solid #667eea;
            }
            .section h2 {
                color: #667eea;
                margin-bottom: 15px;
                font-size: 1.5em;
            }
            .endpoint {
                background: white;
                padding: 15px;
                border-radius: 10px;
                margin: 10px 0;
                border: 2px solid #e0e0e0;
            }
            .endpoint code {
                background: #f0f0f0;
                padding: 8px 12px;
                border-radius: 6px;
                font-family: 'Courier New', monospace;
                color: #d63384;
                display: inline-block;
                margin: 5px 0;
                word-break: break-all;
            }
            .quality-badge {
                display: inline-block;
                padding: 5px 12px;
                background: #667eea;
                color: white;
                border-radius: 20px;
                font-size: 0.85em;
                margin: 3px;
            }
            .note {
                background: #fff3cd;
                border: 1px solid #ffeeba;
                color: #856404;
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .feature {
                padding: 10px 0;
                border-bottom: 1px solid #e0e0e0;
            }
            .feature:last-child {
                border-bottom: none;
            }
            .signature {
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #e0e0e0;
                color: #666;
                font-size: 1.1em;
            }
            .signature a {
                color: #667eea;
                text-decoration: none;
                font-weight: bold;
            }
            .signature a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 YouTube Downloader API</h1>
            <p class="subtitle">Fast, Simple & Powerful YouTube Video Downloader</p>
            
            <div class="section">
                <h2>📋 Step 1: Get Available Qualities</h2>
                <div class="endpoint">
                    <code>/dl?url=VIDEO_URL</code>
                    <p style="color: #666; margin-top: 10px;">
                        ✨ Without 'q' parameter = Shows all available qualities with direct YouTube URLs
                    </p>
                </div>
                <div class="endpoint">
                    <strong>Example:</strong><br>
                    <code>/dl?url=https://youtu.be/VIDEO_ID</code><br>
                    <code>/dl?url=https://youtube.com/watch?v=VIDEO_ID</code>
                </div>
            </div>
            
            <div class="section">
                <h2>⬇️ Step 2: Download with Quality</h2>
                <div class="endpoint">
                    <code>/dl?url=VIDEO_URL&q=QUALITY</code>
                    <p style="color: #666; margin-top: 10px;">
                        🎯 With 'q' parameter = Downloads file instantly
                    </p>
                </div>
                <div class="endpoint">
                    <strong>Example:</strong><br>
                    <code>/dl?url=https://youtu.be/VIDEO_ID&q=720p</code>
                </div>
            </div>
            
            <div class="section">
                <h2>🎨 Available Qualities</h2>
                <div style="padding: 10px 0;">
                    <span class="quality-badge">best</span>
                    <span class="quality-badge">1080p</span>
                    <span class="quality-badge">720p</span>
                    <span class="quality-badge">480p</span>
                    <span class="quality-badge">360p</span>
                    <span class="quality-badge">240p</span>
                    <span class="quality-badge">audio</span>
                </div>
            </div>
            
            <div class="section">
                <h2>✨ Features</h2>
                <div class="feature">📹 Support for all YouTube URL formats (watch?v= and youtu.be)</div>
                <div class="feature">🎵 Audio-only download (MP3 format)</div>
                <div class="feature">🔗 Direct YouTube server URLs in response</div>
                <div class="feature">⚡ Fast and reliable downloads</div>
                <div class="feature">🌐 CORS enabled - use from any frontend</div>
                <div class="feature">📱 Mobile & Desktop friendly</div>
            </div>
            
            <div class="note">
                <strong>💡 Pro Tip:</strong> Use the direct YouTube URLs from Step 1 response to download files 
                without going through the API - perfect for external download managers!
            </div>
            
            <div class="signature">
                Developed with 💀 by <a href="https://github.com/EvilIndian" target="_blank">@EvilIndian</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/dl', methods=['GET'])
def download_direct():
    """Direct download - URL in, file out! Or show qualities if q not provided"""
    url = request.args.get('url')
    quality = request.args.get('q')
    
    if not url:
        return jsonify({
            '❌ error': 'Missing url parameter',
            '💡 usage': '/dl?url=VIDEO_URL',
            '👨‍💻 developer': '@EvilIndian 💀'
        }), 400
    
    # If quality not provided, show available qualities
    if not quality:
        logger.info(f"📋 Getting info: {url}")
        info = get_video_info(url)
        
        if info['success']:
            # Format view count
            views = info['view_count']
            if views >= 1_000_000:
                views_formatted = f"{views / 1_000_000:.1f}M"
            elif views >= 1_000:
                views_formatted = f"{views / 1_000:.1f}K"
            else:
                views_formatted = str(views)
            
            return jsonify({
                '✅ success': True,
                '🎬 title': info['title'],
                '👤 uploader': info['uploader'],
                '⏱️ duration': info['duration'],
                '👁️ views': views_formatted,
                '🖼️ thumbnail': info['thumbnail'],
                '🎨 available_qualities': [f['quality'] for f in info['formats']],
                '📦 formats': info['formats'],
                '💡 usage': f"/dl?url={url}&q=QUALITY",
                '✨ example': f"/dl?url={url}&q=720p",
                '👨‍💻 developer': '@EvilIndian 💀'
            })
        else:
            return jsonify({
                '❌ success': False,
                '🚫 error': info['error'],
                '💡 tip': 'Make sure the YouTube URL is valid and accessible',
                '👨‍💻 developer': '@EvilIndian 💀'
            }), 400
    
    logger.info(f"📥 Request: {quality} - {url}")
    
    result = download_video(url, quality)
    
    if result['success']:
        filepath = Path(result['filepath'])
        
        if filepath.exists():
            logger.info(f"📤 Sending file to browser...")
            return send_file(
                filepath,
                as_attachment=True,
                download_name=result['filename'],
                mimetype='application/octet-stream'
            )
        else:
            logger.error(f"File not found: {filepath}")
            return jsonify({
                '❌ success': False,
                '🚫 error': 'File downloaded but not found on server',
                '📁 path': str(filepath),
                '👨‍💻 developer': '@EvilIndian 💀'
            }), 500
    else:
        return jsonify({
            '❌ success': False,
            '🚫 error': result['error'],
            '💡 tip': 'Try a different quality or check if the video is available',
            '👨‍💻 developer': '@EvilIndian 💀'
        }), 400

@app.route('/list', methods=['GET'])
def list_files():
    """List downloaded files"""
    files = []
    for file in DOWNLOAD_DIR.iterdir():
        if file.is_file():
            files.append({
                '📄 name': file.name,
                '💾 size': f"{file.stat().st_size / (1024*1024):.2f} MB"
            })
    
    return jsonify({
        '✅ success': True,
        '📊 count': len(files),
        '📁 files': files,
        '👨‍💻 developer': '@EvilIndian 💀'
    })

@app.route('/clean', methods=['GET'])
def cleanup():
    """Delete all files"""
    count = 0
    for file in DOWNLOAD_DIR.iterdir():
        if file.is_file():
            file.unlink()
            count += 1
    logger.info(f"🗑️  Cleaned {count} files")
    return jsonify({
        '✅ success': True,
        '🗑️ deleted': count,
        '💬 message': f'Successfully deleted {count} file(s)',
        '👨‍💻 developer': '@EvilIndian 💀'
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎬 YouTube Downloader - Ultra Simple Edition")
    print("="*60)
    
    # Get port from environment variable (Railway uses this)
    port = int(os.environ.get('PORT', 5000))
    
    # Only try to kill process if running locally (port 5000)
    if port == 5000:
        logger.info("🔍 Checking port 5000...")
        if kill_port_process(5000):
            logger.info("✅ Cleared port 5000")
        else:
            port = find_free_port(5000)
            logger.info(f"✅ Using port {port}")
    else:
        logger.info(f"✅ Using Railway port {port}")
    
    print(f"\n📁 Downloads: {DOWNLOAD_DIR.absolute()}")
    print(f"🌐 API running on port: {port}")
    print(f"\n💡 Usage:")
    print(f"   Check qualities: /dl?url=VIDEO_URL")
    print(f"   Download: /dl?url=VIDEO_URL&q=720p")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
