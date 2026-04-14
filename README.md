# 🎙️ Audio Transcriber

Transcreve arquivos de áudio para `.txt` usando o modelo **Whisper** da OpenAI — 100% local, sem API key.

---

## 📁 Estrutura do Projeto

```
audio_transcriber/
├── transcriber.py     # Lógica principal
├── exemplo_uso.py     # Exemplos de uso via código
├── requirements.txt   # Dependências
└── README.md
```

---

## ⚙️ Instalação

### 1. Pré-requisito: FFmpeg

O Whisper usa o FFmpeg para ler os áudios. Instale conforme seu sistema:

```bash
# Ubuntu / Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows — baixe em https://ffmpeg.org/download.html e adicione ao PATH
```

### 2. Dependências Python

```bash
pip install -r requirements.txt
```

> **Dica:** use uma virtualenv ou conda para isolar o ambiente.

---

## 🚀 Como Usar

### Via linha de comando

```bash
# Transcrever um único arquivo (detecção automática de idioma)
python transcriber.py meu_audio.mp3

# Forçar idioma português e escolher pasta de saída
python transcriber.py meu_audio.mp3 --language pt --output saida/

# Transcrever toda uma pasta de áudios
python transcriber.py audios/ --language pt --output saida/

# Usar um modelo maior (mais preciso, mais lento)
python transcriber.py meu_audio.wav --model medium
```

### Via código Python

```python
from transcriber import load_model, transcribe_file, transcribe_folder

model = load_model("base")

# Arquivo único
transcribe_file(model, "audio.mp3", language="pt", output_dir="saida/")

# Pasta inteira
transcribe_folder(model, "audios/", language="pt", output_dir="saida/")
```

---

## 🤖 Modelos Disponíveis

| Modelo   | Tamanho  | Velocidade | Precisão  | VRAM     |
|----------|----------|------------|-----------|----------|
| `tiny`   | 75 MB    | Muito rápido | Baixa   | ~1 GB    |
| `base`   | 145 MB   | Rápido     | Boa       | ~1 GB    |
| `small`  | 461 MB   | Moderado   | Muito boa | ~2 GB    |
| `medium` | 1.5 GB   | Lento      | Alta      | ~5 GB    |
| `large`  | 2.9 GB   | Muito lento| Máxima    | ~10 GB   |

> Para áudios em português, `base` já entrega ótimos resultados. Use `small` ou `medium` para áudios com sotaque forte ou ruído.

---

## 🎵 Formatos Suportados

`.mp3` · `.mp4` · `.wav` · `.m4a` · `.ogg` · `.flac` · `.webm`

---

## 📄 Formato do Arquivo de Saída

Cada `.txt` gerado contém um cabeçalho com metadados:

```
Arquivo de origem: entrevista.mp3
Idioma detectado: pt
Transcrito em: 13/04/2025 14:32:10
------------------------------------------------------------

Texto transcrito aqui...
```

---

## 💡 Dicas

- **GPU disponível?** O Whisper usa CUDA automaticamente — muito mais rápido.
- **Áudio longo?** Prefira `small` ou `medium` para melhor resultado.
- **Sem GPU?** O modelo `tiny` ou `base` roda bem só com CPU.
