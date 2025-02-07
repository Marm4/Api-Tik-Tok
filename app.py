from flask import Flask, request, send_file, jsonify, after_this_request
import yt_dlp
import os
import logging

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)  # Habilita logging detallado

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/descargar', methods=['POST'])
def download_audio():
    app.logger.debug("\n\n=== Nueva solicitud recibida ===")
    app.logger.debug(f"Headers: {dict(request.headers)}")
    app.logger.debug(f"Body raw: {request.get_data(as_text=True)}")
    
    data = request.get_json()
    url = data.get("url") if data else None
    
    app.logger.debug(f"URL recibida: {url}")
    
    if not url:
        app.logger.error("❌ Falta la URL en la solicitud")
        return jsonify({"error": "Falta la URL"}), 400

    try:
        app.logger.debug("⌛ Iniciando descarga con yt-dlp...")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': '192',
            }],
            'verbose': True,  # Logs internos de yt-dlp
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            app.logger.debug("⌛ Extrayendo información del video...")
            info = ydl.extract_info(url, download=True)
            app.logger.debug(f"✅ Información obtenida: {info.get('title')}")
            
            # Nombre real del archivo generado
            original_filename = ydl.prepare_filename(info)
            final_filename = original_filename.replace(".webm", ".m4a").replace(".mp4", ".m4a")
            file_path = os.path.join(DOWNLOAD_FOLDER, final_filename)
            
            app.logger.debug(f"📄 Nombre de archivo esperado: {final_filename}")
            app.logger.debug(f"📁 Ruta completa: {os.path.abspath(file_path)}")

        # Verificar si el archivo existe realmente
        if not os.path.exists(file_path):
            app.logger.error(f"❌ Archivo no encontrado: {file_path}")
            return jsonify({"error": "Error al generar el archivo"}), 500
            
        app.logger.debug(f"✅ Archivo creado - Tamaño: {os.path.getsize(file_path)} bytes")

        @after_this_request
        def remove_file(response):
            try:
                app.logger.debug("🔄 Intentando eliminar archivo temporal...")
                os.remove(file_path)
                app.logger.debug(f"🗑️ Archivo eliminado: {file_path}")
            except Exception as e:
                app.logger.error(f"❌ Error al eliminar archivo: {str(e)}", exc_info=True)
            return response

        app.logger.debug("📤 Enviando archivo como respuesta...")
        return send_file(
            file_path,
            as_attachment=True,
            mimetype="audio/mp4",
            download_name=final_filename
        )

    except yt_dlp.utils.DownloadError as e:
        app.logger.error(f"❌ Error en yt-dlp: {str(e)}", exc_info=True)
        return jsonify({"error": "Error al descargar el video"}), 500
        
    except Exception as e:
        app.logger.error(f"❌ Error inesperado: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
