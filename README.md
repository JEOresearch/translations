# Real-Time Video Language Translation Tool
This repository contains code that processes video files to recognize speech, display transcriptions, and eventually translate and overlay subtitles on the video in real time. It utilizes various Python libraries for audio processing, video manipulation, and natural language translation.

** Note that this software is incomplete and is still in the prototype stage. **

If this software is useful to you, please consider subscribing to my Youtube Channel to help support this and other open-source projects: https://www.youtube.com/@jeoresearch

Features
- Extracts audio from video files.
- Recognizes speech using the Vosk model.
- Processes and displays transcriptions on the video frame.
- Supports translating text between Japanese and English.
- Adds subtitles to videos and saves the output with optional translations.
- Requirements
- Before running the code, ensure you have the following Python packages installed:

vosk (for speech recognition)
sounddevice (for real-time audio processing)
opencv-python (for video processing)
numpy (for matrix operations)
Pillow (for handling images and fonts)
statistics (for statistical operations)
ffmpeg-python (for processing audio and video)
ollama (for translation using the LLaMA model)
To install the necessary packages, run:

```bash:
pip install vosk sounddevice opencv-python numpy Pillow statistics ffmpeg-python ollama
```

Additionally, you will need ffmpeg installed on your system. You can download it from [here](https://ffmpeg.org/download.html) and add it to your system's PATH.

Directories to Update
Vosk Model Path: The model_path in the code points to C:/Storage/vosk-model-en-us-0.22-lgraph for English or vosk-model-small-ja-0.22 for Japanese. Update this path according to where you have downloaded and extracted the Vosk model. You can find the models at Vosk models.

Font Path: If using Japanese text or other fonts, modify the font_path in the put_japanese_text function to the location of the fonts on your system. The current path points to E:/Software/JPFonts/NotoSansJP-Regular.ttf. Ensure you update this to match your local setup.

Video and Audio File Paths: Update video_path in main() to point to the input video file you want to process. The output video will be saved to the same directory as specified by output_video_path.

Usage
Prepare the Vosk Model: Download the Vosk model for the language you want to use and unpack it. Update the model_path to point to the correct model folder.

Run the Script: Run the script with:

```bash
python script_name.py
```

The script will extract audio from the input video, recognize speech, process transcriptions, and display them on the video.

Translation (Optional): By default, the jp flag is set to False for English-to-Japanese translation. To change the translation direction (Japanese-to-English), set jp = True in the display_translations and translate_text functions.

Output: The processed video will be saved to the path defined by output_with_subtitles.mp4, and the final video with combined audio and video will be saved as final_output_with_audio.mp4.

Important Notes
The video will display three lines of subtitles at a time, centered on the screen.
The code supports both partial and finalized speech recognition results, but currently only finalized results are displayed.
Ensure that you have a proper setup for Japanese fonts if using the Japanese translation feature.
License
This project is licensed under the MIT License.

Feel free to contact me with any issues or questions regarding the usage of this tool!
