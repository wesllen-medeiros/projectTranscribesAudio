import whisper
import argparse
import os
from pathlib import Path
from datetime import datetime


SUPPORTED_FORMATS = {".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac", ".webm"}


def load_model(model_size: str = "base") -> whisper.Whisper:
    """Carrega o modelo Whisper. Tamanhos: tiny, base, small, medium, large."""
    print(f"[INFO] Carregando modelo '{model_size}'...")
    return whisper.load_model(model_size)


def transcribe_file(
    model: whisper.Whisper,
    audio_path: str,
    language: str = None,
    output_dir: str = None,
) -> str:
    """
    Transcreve um arquivo de áudio e salva o resultado em .txt.

    Args:
        model: Modelo Whisper carregado.
        audio_path: Caminho do arquivo de áudio.
        language: Idioma do áudio (ex: 'pt', 'en'). None = detecção automática.
        output_dir: Diretório de saída. None = mesmo diretório do áudio.

    Returns:
        Caminho do arquivo .txt gerado.
    """
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {audio_path}")

    if audio_path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Formato '{audio_path.suffix}' não suportado. "
            f"Use: {', '.join(SUPPORTED_FORMATS)}"
        )

    print(f"[INFO] Transcrevendo: {audio_path.name}")

    # Transcrição
    options = {"verbose": False}
    if language:
        options["language"] = language

    result = model.transcribe(str(audio_path), **options)
    text = result["text"].strip()
    detected_lang = result.get("language", "desconhecido")

    print(f"[INFO] Idioma detectado: {detected_lang}")

    # Define diretório de saída
    out_dir = Path(output_dir) if output_dir else audio_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # Nome do arquivo de saída
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_filename = f"{audio_path.stem}_{timestamp}.txt"
    txt_path = out_dir / txt_filename

    # Salva o texto
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Arquivo de origem: {audio_path.name}\n")
        f.write(f"Idioma detectado: {detected_lang}\n")
        f.write(f"Transcrito em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write("-" * 60 + "\n\n")
        f.write(text)

    print(f"[OK] Salvo em: {txt_path}")
    return str(txt_path)


def transcribe_folder(
    model: whisper.Whisper,
    folder_path: str,
    language: str = None,
    output_dir: str = None,
) -> list[str]:
    """
    Transcreve todos os arquivos de áudio de uma pasta.

    Returns:
        Lista de caminhos dos arquivos .txt gerados.
    """
    folder = Path(folder_path)
    audio_files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS
    ]

    if not audio_files:
        print(f"[AVISO] Nenhum áudio encontrado em: {folder}")
        return []

    print(f"[INFO] {len(audio_files)} arquivo(s) encontrado(s).")
    results = []

    for audio in audio_files:
        try:
            txt = transcribe_file(model, str(audio), language, output_dir)
            results.append(txt)
        except Exception as e:
            print(f"[ERRO] {audio.name}: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Transcreve áudio para TXT usando Whisper."
    )
    parser.add_argument(
        "input",
        help="Arquivo de áudio ou pasta com áudios.",
    )
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Tamanho do modelo Whisper (padrão: base).",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Idioma do áudio (ex: pt, en). Padrão: detecção automática.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Pasta de saída para os arquivos .txt.",
    )

    args = parser.parse_args()
    model = load_model(args.model)

    input_path = Path(args.input)

    if input_path.is_dir():
        transcribe_folder(model, str(input_path), args.language, args.output)
    elif input_path.is_file():
        transcribe_file(model, str(input_path), args.language, args.output)
    else:
        print(f"[ERRO] Caminho inválido: {input_path}")


if __name__ == "__main__":
    main()
