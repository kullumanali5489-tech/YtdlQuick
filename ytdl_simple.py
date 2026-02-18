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
                        if quality not in seen_qualities or f.get('filesize', 0) > seen_qualities[quality].get('filesize', 0):
                            seen_qualities[quality] = {
                                'quality': quality,
                                'height': f['height'],
                                'ext': f.get('ext', 'mp4'),
                                'filesize': f.get('filesize', 0),
                                'direct_url': f['url'],
                                'format_note': f.get('format_note', ''),
                                'fps': f.get('fps', 0)
                            }
                
                # Audio formats
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('url'):
                        if 'audio' not in seen_qualities or f.get('abr', 0) > seen_qualities.get('audio', {}).get('abr', 0):
                            seen_qualities['audio'] = {
                                'quality': 'audio',
                                'ext': f.get('ext', 'm4a'),
                                'filesize': f.get('filesize', 0),
                                'direct_url': f['url'],
                                'abr': f.get('abr', 0)
                            }
                
                formats = list(seen_qualities.values())
                formats.sort(key=lambda x: x.get('height', 0), reverse=True)
            
            return {
                'success': True,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'formats': formats
            }
    except Exception as e:
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
    <html>
    <body style="font-family: Arial; padding: 40px;">
        <h1>🎬 YouTube Downloader</h1>
        
        <h3>Step 1: Get Available Qualities</h3>
        <code>/dl?url=VIDEO_URL</code>
        <p style="color: #666;">Without 'q' parameter = Shows all available qualities with direct YT URLs</p>
        
        <h3>Step 2: Download with Quality</h3>
        <code>/dl?url=VIDEO_URL&q=QUALITY</code>
        <p style="color: #666;">With 'q' parameter = Downloads file</p>
        
        <br>
        <p><b>Quality options:</b> best, 1080p, 720p, 480p, 360p, 240p, audio</p>
        
        <br>
        <h3>Examples:</h3>
        <p>Get info: <code>/dl?url=https://youtube.com/watch?v=xyz</code></p>
        <p>Download 720p: <code>/dl?url=https://youtube.com/watch?v=xyz&q=720p</code></p>
        <p>Download audio: <code>/dl?url=https://youtube.com/watch?v=xyz&q=audio</code></p>
    </body>
    </html>
    '''

@app.route('/dl', methods=['GET'])
def download_direct():
    """Direct download - URL in, file out! Or show qualities if q not provided"""
    url = request.args.get('url')
    quality = request.args.get('q')
    
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400
    
    # If quality not provided, show available qualities
    if not quality:
        logger.info(f"📋 Getting info: {url}")
        info = get_video_info(url)
        
        if info['success']:
            return jsonify({
                'title': info['title'],
                'uploader': info['uploader'],
                'duration': f"{info['duration'] // 60}:{info['duration'] % 60:02d}",
                'views': info['view_count'],
                'thumbnail': info['thumbnail'],
                'available_qualities': [f['quality'] for f in info['formats']],
                'formats': info['formats'],
                'usage': f"/dl?url={url}&q=QUALITY",
                'example': f"/dl?url={url}&q=720p"
            })
        else:
            return jsonify(info), 400
    
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
            return jsonify({'error': 'File downloaded but not found', 'path': str(filepath)}), 500
    else:
        return jsonify(result), 400

@app.route('/list', methods=['GET'])
def list_files():
    """List downloaded files"""
    files = []
    for file in DOWNLOAD_DIR.iterdir():
        if file.is_file():
            files.append({
                'name': file.name,
                'size': f"{file.stat().st_size / (1024*1024):.2f} MB"
            })
    
    return jsonify({'files': files, 'count': len(files)})

@app.route('/clean', methods=['GET'])
def cleanup():
    """Delete all files"""
    count = 0
    for file in DOWNLOAD_DIR.iterdir():
        if file.is_file():
            file.unlink()
            count += 1
    logger.info(f"🗑️  Cleaned {count} files")
    return jsonify({'deleted': count})

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
