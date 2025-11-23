from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import yt_dlp
import os
import time
import shutil

app = Flask(__name__)
CORS(app)

# BULUT İÇİN GEÇİCİ KLASÖR
DOWNLOAD_FOLDER = '/tmp/downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def get_ffmpeg_path():
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

    print(f"☁️ Bulut İndirme Başlıyor: {url}")
    
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

    # --- GÜNCELLENMİŞ BULUT AYARLARI ---
    ydl_opts = {
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'force_ipv4': True, # Bağlantı kararlılığı için önemli
        'legacyserverconnect': True, # Instagram SSL hatasını azaltır
        # User-Agent'ı kaldırdık, yt-dlp otomatik en iyisini seçsin.
    }

    if has_ffmpeg:
        ydl_opts['ffmpeg_location'] = ffmpeg_loc

    if mode == 'audio':
        if has_ffmpeg:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
            })
        else:
            ydl_opts.update({'format': 'bestaudio/best'})
    else:
        # Video Modu
        if has_ffmpeg:
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                # Render.com'da işlemci zayıf olabilir, zorla convert etmek yerine sadece birleştir diyoruz.
                'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
            })
        else:
            ydl_opts.update({'format': 'best[ext=mp4]/best'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            base, ext = os.path.splitext(filename)
            # Bulutta dosya adı bazen değişebilir, kontrol ediyoruz
            final_file = filename
            
            # Eğer convert edildiyse uzantı değişmiştir
            possible_mp3 = base + ".mp3"
            possible_mp4 = base + ".mp4"
            
            if os.path.exists(possible_mp3):
                final_file = possible_mp3
            elif os.path.exists(possible_mp4):
                final_file = possible_mp4
            
        return send_file(final_file, as_attachment=True)

    except Exception as e:
        print(f"Hata Detayı: {e}")
        # Kullanıcıya daha net bir mesaj verelim
        error_msg = str(e)
        if "Sign in" in error_msg or "Login" in error_msg:
            return jsonify({"error": "Instagram Giriş Duvarı: Bulut IP'si engellendi. Lütfen a-Shell (Yerel) versiyonunu kullanın."}), 500
        return jsonify({"error": f"Sunucu Hatası: {error_msg}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
