from flask import Flask, request, send_file, jsonify
import yt_dlp
import os

app = Flask(__name__)

def download_audio(url):
    # Directorio de descargas
    download_dir = 'downloads'
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Opciones de descarga
    ydl_opts = {
        'format': 'bestaudio/best',  # Selecciona el mejor formato de audio disponible
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
        'restrictfilenames': True,  # Evita caracteres problemáticos en el nombre del archivo
    }

    try:
        # Debug: URL recibida
        app.logger.debug(f"[DEBUG] URL recibida: {url}")

        # Intento de descarga
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Debug: Información del video
            app.logger.debug(f"[DEBUG] Información del video: {info}")

            # Obtener nombre del archivo descargado
            file_title = info.get('title', None)
            file_ext = ydl_opts['postprocessors'][0]['preferredcodec']
            file_name = f"{file_title}.{file_ext}"
            file_path = os.path.join(download_dir, file_name)

            # Debug: Ruta del archivo
            app.logger.debug(f"[DEBUG] Ruta del archivo descargado: {file_path}")

            # Verificar si el archivo existe
            if not os.path.exists(file_path):
                app.logger.error(f"[ERROR] Archivo no encontrado: {file_path}")
                return None

            return file_path

    except yt_dlp.utils.DownloadError as e:
        app.logger.error("[ERROR] Error en la descarga: " + str(e))
    except Exception as e:
        app.logger.error("[ERROR] Error durante la descarga o procesamiento del audio")
        app.logger.error(str(e))
    
    return None


@app.route('/descargar', methods=['POST'])
def descargar():
    url = request.form.get('url')

    # Debug: URL del formulario
    app.logger.debug(f"[DEBUG] URL del formulario: {url}")

    if not url:
        return jsonify({'error': 'No se proporcionó una URL'}), 400

    file_path = download_audio(url)

    if file_path:
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'No se pudo descargar el audio'}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
