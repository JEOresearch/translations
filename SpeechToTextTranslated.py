import time
import os
import json
import queue
import vosk
import sounddevice as sd
import ollama

def list_microphones():
    """List all available microphones and their indices."""
    device_list = sd.query_devices()
    for index, device in enumerate(device_list):
        print(f"Microphone {index}: {device['name']}")
    return device_list

def translate_text(text, target_language="de"):
    """Translate text to the target language using the Ollama model."""
    # Make the request to Ollama model
    response = ollama.chat(model='llama3', messages=[
        {
            'role': 'user',
            'content': text,
        },
    ])

    # Extract and return the translated text from the response
    translated_text = response['message']['content']
    return translated_text


def write_to_file_with_retries(file_path, content, retries=5, delay=1, encoding='utf-8'):
    for attempt in range(retries):
        try:
            with open(file_path, "a", encoding=encoding) as file:
                file.write(content + "\n")
                file.flush()
            break
        except PermissionError:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise

def overwrite_last_line(file_path, content, encoding='utf-8'):
    with open(file_path, "r+", encoding=encoding, errors='ignore') as file:
        lines = file.readlines()
        if lines and "(E)" not in lines[-1]:
            file.seek(0, os.SEEK_END)
            pos = file.tell() - len(lines[-1])
            file.seek(pos)
            file.truncate()
            file.write(content + "\n")
        else:
            file.write(content + "\n")
            
def callback(indata, frames, time, status, q):
    """Callback function to process audio in real-time."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def recognize_speech_from_mic(model, device_index, q, samplerate=16000):
    """Recognize speech from the microphone in real-time."""
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, device=device_index, dtype='int16', channels=1, callback=lambda indata, frames, time, status: callback(indata, frames, time, status, q)):
        rec = vosk.KaldiRecognizer(model, samplerate)
        sentence_buffer = ""
        segment_id = 0
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result['text']:
                    segment_id += 1
                    yield result['text'], True, segment_id  # Final result
            elif rec.PartialResult():
                partial_result = json.loads(rec.PartialResult())
                if partial_result['partial']:
                    yield partial_result['partial'], False, segment_id  # Partial result



def main():
    # List available microphones
    list_microphones()

    # Prompt the user to select a microphone
    mic_index = int(input("Select the microphone index: "))

    # Load Vosk model
    model_path = "C:/Storage/vosk-model-en-us-0.22-lgraph" #ENGL model
    model_path2 = "C:/Storage/vosk-model-small-ja-0.22" #JPNS model
    if not os.path.exists(model_path):
        print(f"Please download the English model from https://alphacephei.com/vosk/models and unpack it as '{model_path}'")
        return
    model = vosk.Model(model_path)
    if not os.path.exists(model_path2):
        print(f"Please download the Japanese model from https://alphacephei.com/vosk/models and unpack it as '{model_path2}'")
        return
    model = vosk.Model(model_path2)

    output_file = "transcription.txt"
    q = queue.Queue()

    last_segment_id = -1

    print("gothere")

    try:
        for transcription, is_final, segment_id in recognize_speech_from_mic(model, mic_index, q):
            print(f"English: {transcription}")

            if is_final:
                # Final result: Write to the file with delimiter
                final_transcription = f"(E) {transcription}"
                overwrite_last_line(output_file, final_transcription)
                # Translate the transcription
                # translated_text = translate_text(transcription, target_language="de")
                # print(f"German: {translated_text}")
                # write_to_file_with_retries(output_file, f"German: {translated_text}")
                last_segment_id = segment_id
            else:
                # Partial result: Overwrite the last line
                overwrite_last_line(output_file, transcription)

            if transcription.lower() == "stop" and is_final:
                print("Stopping the program.")
                break

    except KeyboardInterrupt:
        print("\nDone.")

if __name__ == "__main__":
    main()
