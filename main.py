from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import yt_dlp
import os
import time
import shutil

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = '/tmp/downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def get_ffmpeg_path():
    return shutil.which("ffmpeg")

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
    
    # Temizlik
    for f in os.listdir(DOWNLOAD_FOLDER):
        try:
            os.remove(os.path.join(DOWNLOAD_FOLDER, f))
        except:
            pass

    timestamp = int(time.time())
    outtmpl = os.path.join(DOWNLOAD_FOLDER, f"Cloud_Clip_{timestamp}.%(ext)s")
    
    ffmpeg_loc = get_ffmpeg_path()
    has_ffmpeg = ffmpeg_loc is not None

    ydl_opts = {
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'force_ipv4': True,
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    }

    if has_ffmpeg:
        ydl_opts['ffmpeg_location'] = ffmpeg_loc

    if mode == 'audio':
        # FFmpeg varsa dönüştür, yoksa en iyi sesi indir
        if has_ffmpeg:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
            })
        else:
            ydl_opts.update({'format': 'bestaudio/best'}) # Ham ses
    else:
        # Video Modu
        if has_ffmpeg:
            # FFmpeg varsa: 4K/1080p indir ve birleştir
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
                'postprocessor_args': ['-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p']
            })
        else:
            # FFmpeg yoksa: Tek parça en iyi formatı indir (Merge yapmaya çalışma yoksa hata verir)
            ydl_opts.update({'format': 'best[ext=mp4]/best'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Dosya adı düzeltme
            base, ext = os.path.splitext(filename)
            # Eğer audio modundaysak ve ffmpeg yoksa uzantı m4a/webm kalabilir, sorun değil iPhone açar.
            final_file = filename
            
            if has_ffmpeg and mode == 'audio':
                 final_file = base + ".mp3"
            elif has_ffmpeg and mode == 'video':
                 final_file = base + ".mp4"
            
        return send_file(final_file, as_attachment=True)

    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"error": f"Sunucu Hatası: {str(e)}"}), 500

if __name__ == '__main__':
    # Yerelde test ederken
    app.run(host='0.0.0.0', port=10000)
