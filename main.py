import streamlit as st
import whisper
import tempfile
import os
import ffmpeg
import uuid
import yt_dlp  # for downloading YouTube videos

# Title of the app
st.title("🎥 Video Transcription and 🎵 Audio Extraction")

# Input for YouTube URL
youtube_url = st.text_input("Enter YouTube Video URL")

# File upload (disabled if YouTube URL is used)
uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mkv", "avi", "mov", "flv"])

# Temporary video file path
temp_file_path = None

if youtube_url:
    # Download YouTube video
    with st.spinner("Downloading video from YouTube... ⏳"):
        try:
            # Using yt-dlp to download the best quality video
            ydl_opts = {
                'format': 'best',
                'outtmpl': tempfile.mktemp(suffix=".mp4"),  # Save temp video file
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=True)
                temp_file_path = ydl.prepare_filename(info_dict)  # Get the video path
            st.success(f"Video downloaded successfully! 🎥")
        except Exception as e:
            st.error(f"Failed to download the video: {e}")
else:
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

if temp_file_path:
    # Create horizontal buttons with emojis
    col1, col2, col3 = st.columns(3)
    with col1:
        audio_button = st.button("🎵 Extract Audio")
    with col2:
        video_button = st.button("🎥 Transcribe Video")
    with col3:
        both_button = st.button("🎵🎥 Both Actions")

    # Persistent model selection dropdown
    model_choice = st.selectbox(
        "Select Model 🙂",
        ["Select Model 🙂", "tiny", "base", "small", "medium"],
        key="model_choice"
    )


    def extract_audio(temp_file_path):
        try:
            # Check if the video file has an audio stream
            probe = ffmpeg.probe(temp_file_path)
            audio_streams = [stream for stream in probe.get('streams', []) if stream.get('codec_type') == 'audio']
            if not audio_streams:
                st.error("The uploaded file does not contain an audio stream. Please upload a valid video with audio.")
                return

            with st.spinner("Extracting audio... 🎵"):
                # Generate a unique file name for the output
                unique_id = str(uuid.uuid4())
                audio_output_path = os.path.join(tempfile.gettempdir(), f"{unique_id}.mp3")

                # Run FFmpeg command for audio extraction
                ffmpeg.input(temp_file_path).output(audio_output_path, format='mp3', audio_bitrate='192k').run()

                st.success("Audio extracted successfully! 🎶")
                st.audio(audio_output_path)
                st.download_button(
                    label="Download Audio",
                    data=open(audio_output_path, "rb").read(),
                    file_name="extracted_audio.mp3",
                    mime="audio/mp3"
                )

                # Clean up temporary audio file
                os.remove(audio_output_path)
        except ffmpeg._run.Error as e:
            st.error("Audio extraction failed. Please check the file format or try again.")
            st.text(e.stderr)  # Print FFmpeg error for debugging


    def transcribe_video(temp_file_path, model_choice):
        if model_choice == "Select Model 🙂":
            st.error("Please select a valid model to proceed.")
            return

        with st.spinner("Loading Whisper model... ⏳"):
            st.write(f"Selected model: {model_choice}")
            model = whisper.load_model(model_choice)  # device="cpu" Force CPU to avoid FP16 error or for GPU use "cuda"

        with st.spinner("Transcribing the video... 📝"):
            transcription = model.transcribe(temp_file_path)
            st.success("Transcription complete! ✅")

            # Display formatted transcript
            st.subheader("Transcript")
            formatted_text = "\n".join(transcription["text"].split(". "))  # Split sentences by period
            st.text_area("Transcript", formatted_text, height=300)

            # Option to download the transcript
            if st.download_button(
                    label="Download Transcript",
                    data=formatted_text,
                    file_name="transcript.txt",
                    mime="text/plain"
            ):
                st.experimental_rerun()  # Re-run the app to reset model selection


    if audio_button:
        extract_audio(temp_file_path)

    if video_button:
        transcribe_video(temp_file_path, model_choice)

    if both_button:
        # Perform both actions
        extract_audio(temp_file_path)
        transcribe_video(temp_file_path, model_choice)

    # Cleanup temporary file
    os.remove(temp_file_path)
