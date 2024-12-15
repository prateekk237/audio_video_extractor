import streamlit as st
import whisper
import tempfile
import os
import ffmpeg
import subprocess

# Adjust the upload file limit
#st.set_option("server.maxUploadSize", 300)

# Title
st.title("🎥 Video Transcription and 🎵 Audio Extraction")

# Input options: File upload or YouTube link
upload_option = st.radio("Select Input Type", ["Upload File", "YouTube Link"])
temp_file_path = None

# Handling file upload
if upload_option == "Upload File":
    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mkv", "avi", "mov", "flv"])
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

# Handling YouTube link
elif upload_option == "YouTube Link":
    youtube_link = st.text_input("Paste YouTube link here")
    if youtube_link and st.button("Download YouTube Video"):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                temp_file_path = temp_file.name
                # Download video using yt-dlp
                command = [
                    "yt-dlp",
                    "-f", "mp4",
                    youtube_link,
                    "-o", temp_file_path
                ]
                subprocess.run(command, check=True)
            st.success("YouTube video downloaded successfully!")
        except subprocess.CalledProcessError as e:
            st.error(f"Failed to download video: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

# Audio and transcription options
if temp_file_path:
    audio_button = st.button("🎵 Extract Audio")
    video_button = st.button("🎥 Transcribe Video")
    both_button = st.button("🎵🎥 Extract Both")

    # Audio extraction
    if audio_button or both_button:
        try:
            audio_output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            ffmpeg.input(temp_file_path).output(audio_output_path, format='mp3', audio_bitrate='192k').run(overwrite_output=True)
            st.success("Audio extraction successful!")
            st.audio(audio_output_path)
            with open(audio_output_path, "rb") as audio_file:
                st.download_button(
                    "Download Audio", 
                    data=audio_file, 
                    file_name="extracted_audio.mp3", 
                    mime="audio/mp3"
                )
        except ffmpeg.Error:
            st.error("No audio found in the input video. Please check the file or link.")

    # Transcription
    if video_button or both_button:
        model_choice = st.selectbox("Select Whisper Model", ["tiny", "base", "small", "medium", "large"])
        if model_choice:
            st.write(f"Selected model: {model_choice}")
            st.write("Loading Whisper model...")
            model = whisper.load_model(model_choice)
            st.write("Transcribing the video...")
            transcription = model.transcribe(temp_file_path)
            st.success("Transcription complete!")
            st.text_area("Transcript", transcription["text"], height=300)
            st.download_button(
                "Download Transcript", 
                data=transcription["text"], 
                file_name="transcript.txt", 
                mime="text/plain"
            )

# Cleanup temporary files after app restart
if st.button("Cleanup Temporary Files"):
    if temp_file_path and os.path.exists(temp_file_path):
        os.remove(temp_file_path)
        st.success("Temporary files cleaned up!")
