from flask import Flask, request, send_file, jsonify, after_this_request
import yt_dlp
import os
import re

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)  # Crea la carpeta si no existe


# Función para limpiar el nombre del archivo
def sanitize_filename(filename):
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)  # Elimina caracteres especiales
    app.logger.debug(f"Nombre del archivo sanitizado: {sanitized}")
    return sanitized


@app.route('/descargar', methods=['POST'])
def download_audio():
    data = request.get_json()
    url = data.get("url")

    if not url:
        app.logger.error("No se proporcionó una URL.")
        return jsonify({"error": "Falta la URL"}), 400

    try:
        # Opciones de yt_dlp para forzar formatos compatibles y extraer solo audio
        ydl_opts = {
            'format': 'bestaudio[ext=opus]/bestaudio[ext=m4a]/bestaudio',
            'ffmpeg_location': '/usr/bin/ffmpeg',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'logger': app.logger,  # Para ver los logs detallados de yt_dlp
            'progress_hooks': [lambda d: app.logger.debug(f"Progreso de descarga: {d}")],
        }

        app.logger.debug(f"Iniciando descarga para URL: {url}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # Obtener el nombre del archivo generado
            title = sanitize_filename(info['title'])
            filename = f"{title}.mp3"
            file_path = os.path.join(DOWNLOAD_FOLDER, filename)

            app.logger.debug(f"Archivo esperado: {file_path}")

            # Verificar si el archivo existe realmente
            if not os.path.exists(file_path):
                app.logger.error(f"Archivo no encontrado: {file_path}")
                return jsonify({"error": "Error: El archivo no fue generado correctamente"}), 500

            # Comprobar tamaño del archivo para verificar validez
            file_size = os.path.getsize(file_path)
            app.logger.debug(f"Tamaño del archivo: {file_size} bytes")

            if file_size < 100:  # Si el archivo es menor a 100 bytes, probablemente está dañado
                app.logger.error("El archivo descargado parece estar corrupto.")
                return jsonify({"error": "El archivo descargado parece estar corrupto"}), 500

        # Programar eliminación del archivo después de la descarga
        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    app.logger.debug(f"Archivo eliminado: {file_path}")
                else:
                    app.logger.warning(f"Intento de eliminar archivo no existente: {file_path}")
            except Exception as e:
                app.logger.error("Error al eliminar el archivo", exc_info=e)
            return response

        # Enviar el archivo al cliente
        return send_file(file_path, as_attachment=True, mimetype="audio/mp3")

    except Exception as e:
        app.logger.error("Error durante la descarga o procesamiento del audio", exc_info=e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
