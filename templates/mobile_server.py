from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import yt_dlp
import os
import shutil
import time
import socket

# --- MOBİL MOTOR AYARLARI ---
app = Flask(__name__)
CORS(app) # iPhone'un erişmesine izin ver

# İndirilenler klasörü
DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads", "MobileDownloads")
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def get_local_ip():
    """Mac'in yerel ağdaki IP adresini bulur."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def get_ffmpeg_path():
    return shutil.which("ffmpeg")

@app.route('/')
def home():
    # index.html dosyasını templates klasöründen okur
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    mode = data.get('mode', 'video') # video veya audio
    
    if not url:
        return jsonify({"error": "Link yok!"}), 400

    print(f"📱 iPhone'dan talep geldi: {url} ({mode})")

    # Dosya ismi şablonu
    timestamp = int(time.time())
    outtmpl = os.path.join(DOWNLOAD_FOLDER, f"Mobile_Download_{timestamp}.%(ext)s")

    # Ayarlar (Masaüstü versiyonunun aynısı)
    ydl_opts = {
        'outtmpl': outtmpl,
        'ffmpeg_location': get_ffmpeg_path(),
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        # Instagram Fix
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    }

    if mode == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        })
    else:
        # Video - H.264 Zorlama (iPhone uyumu için şart)
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
            'postprocessor_args': ['-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p']
        })

    try:
        # İndirme İşlemi
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Uzantı düzeltme (mp3 veya mp4)
            if mode == 'audio':
                final_file = os.path.splitext(filename)[0] + ".mp3"
            else:
                final_file = os.path.splitext(filename)[0] + ".mp4"

        # Dosyayı iPhone'a geri gönder
        return send_file(final_file, as_attachment=True)

    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Mac'in yerel ağdaki IP adresini bulur ve yayına başlar
    # Terminalde '0.0.0.0' yazması, tüm ağa açık demektir.
    local_ip = get_local_ip()
    print("\n" + "="*40)
    print(f"🚀 MOBİL SUNUCU AKTİF!")
    print(f"📡 iPhone'undan Safari'yi aç ve şu adrese git:")
    print(f"👉 http://{local_ip}:5000")
    print("="*40 + "\n")
    app.run(host='0.0.0.0', port=5000)