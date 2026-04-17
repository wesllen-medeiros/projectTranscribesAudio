import os
import uuid
import threading
import queue
import json
import time
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, send_file, stream_with_context
import whisper

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("saida")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

SUPPORTED_FORMATS = {".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac", ".webm"}

# Cache de modelos (evita recarregar o mesmo modelo)
_models: dict = {}
_model_lock = threading.Lock()

# Registro de jobs em andamento
_jobs: dict = {}


def get_or_load_model(model_size: str) -> whisper.Whisper:
    with _model_lock:
        if model_size not in _models:
            _models[model_size] = whisper.load_model(model_size)
        return _models[model_size]


def transcription_worker(job_id: str, audio_path: Path, model_size: str, language: str | None):
    job = _jobs[job_id]
    q: queue.Queue = job["queue"]

    def emit(event: dict):
        q.put(event)

    try:
        emit({"type": "status", "message": f'Carregando modelo "{model_size}"...'})
        model = get_or_load_model(model_size)
        emit({"type": "status", "message": "Modelo pronto. Transcrevendo áudio..."})

        options: dict = {"verbose": False}
        if language:
            options["language"] = language

        result = model.transcribe(str(audio_path), **options)

        text: str = result["text"].strip()
        detected_lang: str = result.get("language", "desconhecido")
        segments: list = result.get("segments", [])

        emit({"type": "language", "language": detected_lang})

        # Envia cada segmento individualmente para exibição progressiva
        for seg in segments:
            emit({
                "type": "segment",
                "text": seg["text"].strip(),
                "start": round(seg["start"], 1),
                "end": round(seg["end"], 1),
            })

        # Salva arquivo de saída
        audio_stem = audio_path.stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_filename = f"{audio_stem}_{timestamp}.txt"
        txt_path = OUTPUT_DIR / txt_filename

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"Arquivo de origem: {audio_path.name}\n")
            f.write(f"Idioma detectado: {detected_lang}\n")
            f.write(f"Transcrito em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("-" * 60 + "\n\n")
            f.write(text)

        job["output_file"] = str(txt_path)
        job["status"] = "done"
        emit({"type": "done", "filename": txt_filename})

    except Exception as exc:
        job["status"] = "error"
        emit({"type": "error", "message": str(exc)})

    finally:
        # Remove o arquivo de upload após processar
        try:
            audio_path.unlink(missing_ok=True)
        except Exception:
            pass


@app.route("/")
def index(): 
    return render_template("index.html")


@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Nome de arquivo inválido"}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        return jsonify({"error": f"Formato {ext} não suportado. Use: {', '.join(SUPPORTED_FORMATS)}"}), 400

    model_size = request.form.get("model", "base")
    if model_size not in ("tiny", "base", "small", "medium", "large"):
        model_size = "base"

    language = request.form.get("language") or None

    job_id = str(uuid.uuid4())
    audio_path = UPLOAD_DIR / f"{job_id}{ext}"
    file.save(str(audio_path))

    _jobs[job_id] = {
        "queue": queue.Queue(),
        "status": "running",
        "output_file": None,
    }

    thread = threading.Thread(
        target=transcription_worker,
        args=(job_id, audio_path, model_size, language),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/stream/<job_id>")
def stream(job_id: str):
    if job_id not in _jobs:
        return jsonify({"error": "Job não encontrado"}), 404

    @stream_with_context
    def generate():
        job = _jobs[job_id]
        q: queue.Queue = job["queue"]
        while True:
            try:
                event = q.get(timeout=60)
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                # Pausa breve entre segmentos para aparecerem progressivamente na tela
                if event["type"] == "segment":
                    time.sleep(0.12)
                if event["type"] in ("done", "error"):
                    break
            except queue.Empty:
                yield 'data: {"type":"ping"}\n\n'

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.route("/download/<job_id>")
def download(job_id: str):
    if job_id not in _jobs:
        return jsonify({"error": "Job não encontrado"}), 404

    job = _jobs[job_id]
    output_file = job.get("output_file")

    if not output_file or not Path(output_file).exists():
        return jsonify({"error": "Arquivo ainda não disponível"}), 404

    return send_file(output_file, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, threaded=True, port=5000)
