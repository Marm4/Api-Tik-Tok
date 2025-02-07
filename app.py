from flask import Flask, request, send_file, jsonify, after_this_request
import yt_dlp
import os

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)  # Crea la carpeta si no existe

@app.route('/descargar', methods=['POST'])
def download_audio():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "Falta la URL"}), 400

    try:
        # Opciones para descargar solo el audio
        ydl_opts = {
            'format': 'bestaudio/best',
            'ffmpeg_location': '/usr/bin/ffmpeg',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = f"{info['title']}.mp3"
            file_path = os.path.join(DOWNLOAD_FOLDER, filename)

        @after_this_request
        def remove_file(response):
            try:
                os.remove(file_path)
            except Exception as e:
                app.logger.error("Error al eliminar el archivo", exc_info=e)
            return response

        return send_file(file_path, as_attachment=True, mimetype="audio/mp4")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

