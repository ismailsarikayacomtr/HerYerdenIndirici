from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import yt_dlp
import os
import time
import shutil
import random

app = Flask(__name__)
CORS(app)

# Geçici indirme klasörü
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

    # --- ANTI-BOT AYARLARI ---
    # YouTube'un veri merkezi IP'lerini engellemesini aşmak için
    # 'android' istemcisini taklit ediyoruz.
    
    ydl_opts = {
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'force_ipv4': True,
        
        # KRİTİK DEĞİŞİKLİK: User-Agent yerine Client Spoofing
        'extractor_args': {
            'youtube': {
                # Android uygulaması gibi davran (En az engel yiyen yöntem)
                'player_client': ['android', 'web'],
                'player_skip': ['webport', 'tv']
            }
        },
        # Bazen küçük bir bekleme süresi bot algısını kırar
        'sleep_interval_requests': 1,
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
                'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
            })
        else:
            ydl_opts.update({'format': 'best[ext=mp4]/best'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            base, ext = os.path.splitext(filename)
            final_file = filename
            
            # Uzantı kontrolü
            possible_mp3 = base + ".mp3"
            possible_mp4 = base + ".mp4"
            
            if os.path.exists(possible_mp3):
                final_file = possible_mp3
            elif os.path.exists(possible_mp4):
                final_file = possible_mp4
            
        return send_file(final_file, as_attachment=True)

    except Exception as e:
        error_msg = str(e)
        print(f"Hata Detayı: {error_msg}")
        
        # Kullanıcıya net mesaj verelim
        if "Sign in" in error_msg:
            return jsonify({"error": "YouTube Koruması: Bulut sunucusu engellendi. Bu linki a-Shell (iPhone Yerel) versiyonu ile indirmen gerekebilir."}), 500
        elif "bot" in error_msg.lower():
             return jsonify({"error": "Bot Algılandı: Lütfen biraz bekleyip tekrar deneyin."}), 500
             
        return jsonify({"error": f"Hata: {error_msg}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
