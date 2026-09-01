import os
import warnings
import whisper

# Suppress PyTorch FP16 CPU warning
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

# Load the Whisper model ("base" model provides high accuracy and fast CPU performance)
model = whisper.load_model("base")

def voice_to_text(audio_path: str) -> str:
    """
    Converts an audio file to text using OpenAI Whisper.
    Args:
        audio_path (str): Path to the audio file (WAV, MP3, WEBM, etc.).
    Returns:
        str: Transcribed text string.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Transcribe audio file with explicit CPU FP32 setting
    result = model.transcribe(audio_path, fp16=False)
    return result.get("text", "").strip()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        print(f"Transcribing {test_file}...")
        transcription = voice_to_text(test_file)
        print(f"Result: '{transcription}'")
    else:
        print("Voice Input Module loaded successfully.")
