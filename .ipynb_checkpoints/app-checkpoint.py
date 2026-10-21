import os
import asyncio
from flask import Flask, render_template, request, jsonify, send_file
import edge_tts

app = Flask(__name__)

# Carpetas donde guardaremos los textos y los audios generados
TXT_DIR = "archivos_texto"
AUDIO_DIR = "archivos_audio"
VOICE = "es-PE-AlexNeural" # Voz de Perú (puedes cambiarla por es-MX-JorgeNeural, etc.)

for folder in [TXT_DIR, AUDIO_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

async def tts_compile(text_path, audio_path):
    with open(text_path, "r", encoding="utf-8") as f:
        text_content = f.read()
    communicate = edge_tts.Communicate(text_content, VOICE)
    await communicate.save(audio_path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/archivos', methods=['GET'])
def listar_archivos():
    """Devuelve la lista de archivos creados"""
    archivos = [f for f in os.listdir(TXT_DIR) if f.endswith('.txt')]
    return jsonify(archivos)

@app.route('/api/guardar', methods=['POST'])
def guardar_archivo():
    """Crea o edita un archivo de texto"""
    data = request.json
    nombre = data.get('nombre', '').strip()
    contenido = data.get('contenido', '')

    if not nombre:
        return jsonify({"error": "El nombre es obligatorio"}), 400
    
    if not nombre.endswith('.txt'):
        nombre += '.txt'

    ruta = os.path.join(TXT_DIR, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)

    return jsonify({"success": True, "filename": nombre})

@app.route('/api/convertir/<filename>', methods=['POST'])
def convertir_audio(filename):
    """Convierte el archivo TXT seleccionado en MP3"""
    txt_path = os.path.join(TXT_DIR, filename)
    audio_filename = filename.replace('.txt', '.mp3')
    audio_path = os.path.join(AUDIO_DIR, audio_filename)

    if not os.path.exists(txt_path):
        return jsonify({"error": "Archivo no encontrado"}), 404

    # Ejecutar la conversión asíncrona de Edge TTS
    asyncio.run(tts_compile(txt_path, audio_path))
    return jsonify({"success": True, "audio_url": f"/download/{audio_filename}"})

@app.route('/download/<filename>')
def descargar_audio(filename):
    """Descarga o reproduce el audio generado"""
    return send_file(os.path.join(AUDIO_DIR, filename), mimetype="audio/mp3")

if __name__ == '__main__':
    # Esto permite que el servidor web asigne el puerto automáticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
