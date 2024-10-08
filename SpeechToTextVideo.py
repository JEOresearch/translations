import time
import json
import queue
import threading
import vosk
import sounddevice as sd
import cv2
import numpy as np
import os
import statistics
import ffmpeg
import ollama
from PIL import Image, ImageDraw, ImageFont

def put_japanese_text(image, text, position, font_path='E:/Software/JPFonts/NotoSansJP-Regular.ttf', font_size=20, color=(255, 0, 0)):
    # Convert the image to RGB (OpenCV uses BGR by default)
    cv2_im_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Convert the image to a PIL image
    pil_im = Image.fromarray(cv2_im_rgb)
    
    # Create a drawing context
    draw = ImageDraw.Draw(pil_im)
    
    # Load a font
    font = ImageFont.truetype(font_path, font_size)
    
    # Draw the text
    draw.text(position, text, font=font, fill=color)
    
    # Convert the PIL image back to an OpenCV image
    image_with_text = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGB2BGR)
    
    image[:] = image_with_text

def process_final_result(text):
    """Process the final result: remove 'the', capitalize the first letter, and add a period at the end."""
    words = text.split()
    if len(words) == 0:
        return text
    if words[0].lower() == "the":
        words = words[1:]
    if words and words[-1].lower() == "the":
        words = words[:-1]
    
    processed_text = ' '.join(words)
    
    # Capitalize the first letter
    if processed_text:
        processed_text = processed_text[0].upper() + processed_text[1:]
    
    # Add a period at the end if not already present
    if processed_text and processed_text[-1] not in ".!?":
        processed_text += "."
    
    return processed_text

def recognize_speech_from_video(model, audio_queue, results, samplerate=16000, framerate=60):
    """Recognize speech from the video in real-time."""
    rec = vosk.KaldiRecognizer(model, samplerate)
    total_audio_duration = 0.0  # Initialize the total audio duration

    while True:
        data = audio_queue.get()
        if data is None:
            break
        total_audio_duration += len(data) / (samplerate * 2)  # Update the audio duration in seconds
        frame_number = int(total_audio_duration * framerate)  # Compute the frame number

        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            if result['text']:
                transcription = process_final_result(result['text'])  # Process the final result
                print(f"Frame {frame_number}: {transcription}")  # Print the frame number and transcription
                results.append((frame_number, 'full', transcription))
        #elif rec.PartialResult():
        #    partial_result = json.loads(rec.PartialResult())
        #    if partial_result['partial']:
        #        transcription = partial_result['partial']
        #        print(f"Frame {frame_number}: Partial result: {transcription}")  # Print the frame number and partial result
        #        results.append((frame_number, 'partial', transcription))

def display_transcriptions(frame, transcriptions, partial_transcription, x0, y0, dy, prev_length_difference, max_length=40):
    """Combine finalized and partial transcriptions and display them on the frame."""
    jp = False
    
    if jp == True:
        max_length = 25
    
    lines = []
    
    # Combine transcriptions and partial transcription
    combined_transcription = ' '.join(transcriptions) + process_final_result(' '.join(partial_transcription))
    print(combined_transcription)
    words = combined_transcription.split()
    
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_length:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
        else:
            lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)

    # Calculate the difference in the number of lines
    original_length = len(lines)
    lines = lines[-3:]
    length_difference = original_length - len(lines)

    # Check if length difference increased by one
    if length_difference - prev_length_difference == 1:
        print("changed")
        y0 += dy * 2.5

    textScaler = 3.0
    jpTextScaler = 2.0
    #border should be an even number
    border = 2
    fontPath = 'E:/Software/JPFonts/NotoSansJP-Bold.ttf'
    fontPath2 = 'E:/Software/JPFonts/NotoSansJP-Bold.ttf'

    thickness = 5
    
    if jp == False:
        for i, line in enumerate(lines):
            y = y0 + i * dy * textScaler
            # Calculate text width and height
            (text_width, text_height), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.5 * textScaler, 1)
            # Adjust x0 to center the text horizontally
            adjusted_x0 = int(x0 - text_width // 2)
            cv2.putText(frame, line, (adjusted_x0-border, int(y-border)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0+border, int(y+border)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0+border, int(y-border)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0-border, int(y+border)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0-border, int(y)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0+border, int(y)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0, int(y-border)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0, int(y+border)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0, int(y)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (0, 0, 255), thickness-2, cv2.LINE_AA)
    elif jp == True:
        for i, line in enumerate(lines):
            y = y0 + i * dy * textScaler
            # Calculate text width and height
            (text_width, text_height), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.5 * textScaler, 1)
            # Adjust x0 to center the text horizontally
            adjusted_x0 = int(x0  - 680 // 2)
            
            put_japanese_text(frame, line, (adjusted_x0-border, int(y-border)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0+border, int(y+border)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0+border, int(y-border)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0-border, int(y+border)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0-border, int(y)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0+border, int(y)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0, int(y-border)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0, int(y+border)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0, int(y)), fontPath, 20 * jpTextScaler, (255,0,0))
        
    return lines, length_difference

def translate_text(text, jp):
    """
    Translates the given text based on the jp flag using the LLaMA 3.1 model.
    If jp is False, translates English to Japanese.
    If jp is True, translates Japanese to English.
    """
    print(f"input was{text}")
    target_language = "Japanese" if not jp else "English"
    prompt = f"If there is nothing following the last colon in this text, return the word none. Otherwise, only return the translation and nothing else for the following prompt: Assuming the following is only a part of a sentence, translate it as best as possible to {target_language}: \n\n{text}."

    # Make the request to the LLaMA 3.1 model using ollama.chat
    response = ollama.chat(model='llama3.1', messages=[
        {
            'role': 'user',
            'content': prompt,
        },
    ])

    # Extract and return the translated text from the response
    translated_text = response['message']['content']
    print(translated_text)
    if translated_text == "none":
        return ""
    
    return translated_text


def display_translations(frame, transcriptions, partial_transcription, x0, y0, dy, prev_length_difference, max_length=40):
    """
    Combine finalized and partial transcriptions, translate them, and display them on the frame.
    """
    jp = False  # Assuming jp is False for English to Japanese translation
    
    if jp == True:
        max_length = 25
    
    lines = []
    
    # Combine transcriptions and partial transcription
    combined_transcription = ' '.join(transcriptions) + process_final_result(' '.join(partial_transcription))
    
    # Translate the transcription
    translated_text = translate_text(combined_transcription, jp)
    
    
    words = translated_text.split()
    
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_length:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
        else:
            lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)

    # Calculate the difference in the number of lines
    original_length = len(lines)
    lines = lines[-3:]
    length_difference = original_length - len(lines)

    # Check if length difference increased by one
    if length_difference - prev_length_difference == 1:
        print("changed")
        y0 += dy * 2.5

    textScaler = 3.0
    jpTextScaler = 2.0
    #border should be an even number
    border = 2
    fontPath = 'E:/Software/JPFonts/NotoSansJP-Bold.ttf'
    fontPath2 = 'E:/Software/JPFonts/NotoSansJP-Bold.ttf'

    thickness = 5
    
    if jp == False:
        for i, line in enumerate(lines):
            y = y0 + i * dy * textScaler
            # Calculate text width and height
            (text_width, text_height), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.5 * textScaler, 1)
            # Adjust x0 to center the text horizontally
            adjusted_x0 = int(x0 - text_width // 2)
            cv2.putText(frame, line, (adjusted_x0-border, int(y-border)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0+border, int(y+border)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0+border, int(y-border)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0-border, int(y+border)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0-border, int(y)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0+border, int(y)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0, int(y-border)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0, int(y+border)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (255, 255, 255), thickness, cv2.LINE_AA)
            cv2.putText(frame, line, (adjusted_x0, int(y)), cv2.FONT_HERSHEY_SIMPLEX, .5 * textScaler, (0, 0, 255), thickness-2, cv2.LINE_AA)
    elif jp == True:
        for i, line in enumerate(lines):
            y = y0 + i * dy * textScaler
            # Calculate text width and height
            (text_width, text_height), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.5 * textScaler, 1)
            # Adjust x0 to center the text horizontally
            adjusted_x0 = int(x0  - 680 // 2)
            
            put_japanese_text(frame, line, (adjusted_x0-border, int(y-border)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0+border, int(y+border)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0+border, int(y-border)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0-border, int(y+border)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0-border, int(y)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0+border, int(y)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0, int(y-border)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0, int(y+border)), fontPath2, 20 * jpTextScaler, (255,255,255))
            put_japanese_text(frame, line, (adjusted_x0, int(y)), fontPath, 20 * jpTextScaler, (255,0,0))
        
    return lines, length_difference

def compute_median(positions):
    """Compute the median of the last five positions."""
    if len(positions) >= 15:
        median_value = statistics.median(positions[-15:])
    else:
        median_value = statistics.median(positions)
    
    return median_value

def compute_smoothed_position(medians):
    """Compute the average of the last four median values."""
    if len(medians) >= 10:
        return sum(medians[-10:]) / 10
    return sum(medians) / len(medians)

def main():

    # Load Vosk model
    model_path = "C:/Storage/vosk-model-en-us-0.22-lgraph" #ENGL model
    #model_path = "C:/Storage/vosk-model-small-ja-0.22" #JPNS model
    if not os.path.exists(model_path):
        print(f"Please download the model from https://alphacephei.com/vosk/models and unpack it as '{model_path}'")
        return
    model = vosk.Model(model_path)

    audio_queue = queue.Queue()

    # List to hold the results
    results = []

    # Open video file
    video_path = "C:/Storage/Source Videos/TranslationVideos/input_video.mp4" # Replace with your video file path

    # Extract audio from video and put it in the audio queue
    def extract_audio():
        process = (
            ffmpeg
            .input(video_path)
            .output('pipe:', format='wav', ac=1, ar='16k')
            .run_async(pipe_stdout=True)
        )
        while True:
            in_bytes = process.stdout.read(4000)
            if not in_bytes:
                break
            audio_queue.put(in_bytes)
        audio_queue.put(None)
        process.wait()

    # Start audio extraction and recognition
    threading.Thread(target=extract_audio, daemon=True).start()
    recognize_speech_from_video(model, audio_queue, results)

    print("Audio processing complete. Starting video processing.")

    cap = cv2.VideoCapture(video_path)

    # Holds the three lines of transcriptions
    transcriptions = ["", "", ""]
    # Holds current partial transcription
    partial_transcription = [""]
    lock = threading.Lock()
    running = True

    # Load the Haar Cascade for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Store the last five positions of valid face centers
    face_centers_x = []
    face_centers_y = []
    face_sizes_y = []
    median_x_values = []
    median_y_values = []
    timer = 0

    # Variable to store the previous length difference
    prev_length_difference = 0

    frame_idx = 0


    test_scale_factor = 1  # Adjust the scale factor as needed

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))*test_scale_factor 
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))*test_scale_factor 

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('C:/Storage/Source Videos/TranslationVideos/output_with_subtitles.mp4', fourcc, fps, (width, height))

    try:
        while running:
            # Capture frame-by-frame
            ret, frame = cap.read()
            if not ret:
                break

            if timer > 0:
                timer -= 2

            frame = cv2.resize(frame, None, fx=test_scale_factor, fy=test_scale_factor)

            # Convert the frame to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Downscale the image for faster face detection
            scale_factor = 0.25  # Adjust the scale factor as needed
            small_gray = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor)
            
            # Detect faces in the downscaled frame
            faces = face_cascade.detectMultiScale(small_gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            # Draw a rectangle around each face and track face centers
            for (x, y, w, h) in faces:
                if w > 100:
                    cv2.rectangle(frame, (x*4, y*4), (x*4+w*4, y*4+h*4), (255, 255, 255), 4)
                    # Compute the center of the face
                    center_x = x * 4 + 4 * w // 2
                    center_y = y * 4 + 4 * h // 2
                    # Store the center positions
                    face_centers_x.append(center_x)
                    face_centers_y.append(center_y)
                    face_sizes_y.append(4 * h // 2)
                    # Limit to the last 5 positions
                    if len(face_centers_x) > 5:
                        face_centers_x.pop(0)
                    if len(face_centers_y) > 5:
                        face_centers_y.pop(0)
                    
            x0 = 10
            y0 = 10
            chinY = 130

            # Compute the median of the last five positions
            if face_centers_x and face_centers_y:
                median_x = compute_median(face_centers_x)
                median_y = compute_median(face_centers_y)
                chinY = compute_median(face_sizes_y)
                median_x_values.append(median_x)
                median_y_values.append(median_y)

                x0 = compute_smoothed_position(median_x_values)
                y0 = compute_smoothed_position(median_y_values)

                # Optionally, you can draw a circle at the median position
                #cv2.circle(frame, (int(x0), int(y0)), 2, (0, 255, 0), -1)
            '''
            # Check if there are new transcriptions for the current frame
            while results and results[0][0] <= frame_idx:
                _, result_type, transcription = results.pop(0)
                with lock:
                    if result_type == 'full':
                        transcriptions.append(transcription)
                        if len(transcriptions) > 3:
                            transcriptions.pop(0)
                        partial_transcription.clear()  # Clear the partial buffer when a final result is added
                    elif result_type == 'partial':
                        partial_transcription.clear()
                        partial_transcription.append(transcription)  # Update the partial transcription
            '''
            
            while results and results[0][0] <= frame_idx:
                _, result_type, transcription = results.pop(0)
                with lock:
                    if result_type == 'full':
                        transcriptions.append(transcription)
                        if len(transcriptions) > 3:
                            transcriptions.pop(0)
                        partial_transcription.clear()  # Only full results are processed, so clear partials

           

            # Add the transcriptions to the frame
            dy = 20
            with lock:
                lines, length_difference = display_translations(frame, transcriptions, partial_transcription, x0, y0 + chinY + 30 + timer, dy, prev_length_difference)

            # Check if length difference increased by one
            if length_difference - prev_length_difference == 1:
                print("changed2")
                timer += dy * 2.5
            
            # Update previous length difference
            prev_length_difference = length_difference

            # Write the frame to the output video
            out.write(frame)
            
            frame2 = frame.copy()
            frame2 = cv2.resize(frame2, None, fx=.25, fy=.25)


            # Display the resulting frame
            cv2.imshow('frame', frame2)

            # Check for window close event
            if cv2.getWindowProperty('frame', cv2.WND_PROP_VISIBLE) < 1:
                running = False
                break

            # Break the loop on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                running = False
                break

            frame_idx += 1
            
            height, width = frame.shape[:2]

    except KeyboardInterrupt:
        print("\nDone.")
        
    # After the video processing loop


    # Save the processed video to a file
    output_video_path = 'C:/Storage/Source Videos/TranslationVideos/output_with_subtitles.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    # Reopen the video file to process each frame again
    cap = cv2.VideoCapture(video_path)
    frame_idx = 0

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    running = False

    

    # Combine the processed video and original audio
    input_video = ffmpeg.input(output_video_path)
    input_audio = ffmpeg.input(video_path).audio
    ffmpeg.output(input_video, input_audio, 'C:/Storage/Source Videos/TranslationVideos/final_output_with_audio.mp4', vcodec='copy', acodec='aac').run()

if __name__ == "__main__":
    main()
