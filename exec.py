from transcriber import load_model, transcribe_file


model = load_model("large")  

"""

    Transcrever um único arquivo

"""
txt_path = transcribe_file(
    model=model,
    audio_path=r"C:\Users\wesllen.medeiros\Documents\Gravações de som\Gravando (3).m4a",
    language="pt",          # opcional — remove para detecção automática
    output_dir="saida/",    # opcional — padrão: mesma pasta do áudio
)
print(f"Transcrição salva em: {txt_path}")
