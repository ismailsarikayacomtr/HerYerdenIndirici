from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import yt_dlp
import os
import time
import shutil

app = Flask(__name__)
CORS(app)

# Bulut sistemlerinde geçici depolama alanı /tmp klasörüdür
DOWNLOAD_FOLDER = '/tmp/downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def get_ffmpeg_path():
    # Bulut sunucularında ffmpeg genelde sistem yolundadır
    return shutil.which("ffmpeg") or "ffmpeg"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    mode = data.get('mode', 'video')
    
    if not url:
        return jsonify({"error": "Link yok!"}), 400

    print(f"☁️ Bulut Talebi: {url}")
    
    # Temizlik: Eski dosyaları sil (Disk dolmasın)
    for f in os.listdir(DOWNLOAD_FOLDER):
        try:
            os.remove(os.path.join(DOWNLOAD_FOLDER, f))
        except:
            pass

    timestamp = int(time.time())
    outtmpl = os.path.join(DOWNLOAD_FOLDER, f"Cloud_Clip_{timestamp}.%(ext)s")

    ydl_opts = {
        'outtmpl': outtmpl,
        'ffmpeg_location': get_ffmpeg_path(),
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'force_ipv4': True,
        # Instagram Fix
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    }

    if mode == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        })
    else:
        # Video: H.264 Zorlama (iPhone uyumu için)
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
            'postprocessor_args': ['-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p']
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base, ext = os.path.splitext(filename)
            final_file = base + (".mp3" if mode == 'audio' else ".mp4")
            
        return send_file(final_file, as_attachment=True)

    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
