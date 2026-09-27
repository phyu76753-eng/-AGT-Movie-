import streamlit as st
import asyncio
import edge_tts
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
import os

st.set_page_config(page_title="Myanmar AI Video Dubber", layout="wide")

st.title("🎬 Myanmar AI Video Dubbing & Subtitle Tool")
st.write("ဗီဒီယိုထည့်သွင်း၍ မြန်မာ AI အသံပြောင်းခြင်း၊ စာတန်းထိုးခြင်းနှင့် အသံချိန်ညှိခြင်းများကို ပြုလုပ်ပါ")

# 1. Video File Uploader
uploaded_video = st.file_uploader("ဗီဒီယိုဖိုင် ရွေးချယ်ပါ (MP4, MOV, AVI)", type=["mp4", "mov", "avi"])

if uploaded_video is not None:
    # Save uploaded video locally
    with open("input_video.mp4", "wb") as f:
        f.write(uploaded_video.read())
    
    st.video("input_video.mp4")
    
    st.markdown("---")
    st.subheader("⚙️ စာတန်းထိုးနှင့် အသံချိန်ညှိချက်များ")
    
    # 2. Myanmar Text Input for Dubbing & Subtitle
    myanmar_text = st.text_area("မြန်မာဘာသာပြန် စာသား (သို့) စာတန်းထိုးလိုသည့် စာသား ရိုက်ထည့်ပါ -", 
                                "မင်္ဂလာပါ၊ ဒီဗီဒီယိုမှာ AI အသံနဲ့ မြန်မာစာတန်းထိုး ပြုလုပ်ပေးထားပါတယ်။")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Voice Selection
        voice_option = st.selectbox("AI အသံ ရွေးချယ်ပါ", [
            "my-MM-NilarNeural (အမျိုးသမီး)",
            "my-MM-ThihaNeural (အမျိုးသား)"
        ])
        selected_voice = "my-MM-NilarNeural" if "Nilar" in voice_option else "my-MM-ThihaNeural"
        
        # Audio Volume Control
        volume_scale = st.slider("အသံ အတိုး/အကျယ် (Volume)", 0.0, 2.0, 1.0, 0.1)

    with col2:
        # Audio Speed Control (-50% to +50%)
        speed = st.slider("အသံ အမြန်/အနှေး (Speed %)", -50, 50, 0, 5)
        speed_str = f"{'+' if speed >= 0 else ''}{speed}%"
        
        # Audio Pitch Control
        pitch = st.slider("အသံ အနိမ့်/အမြင့် (Pitch Hz)", -20, 20, 0, 2)
        pitch_str = f"{'+' if pitch >= 0 else ''}{pitch}Hz"

    # Async function to generate Edge TTS Audio
    async def generate_voice(text, voice, rate, pitch_val, output_file):
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch_val)
        await communicate.save(output_file)

    if st.button("🚀 AI Dubbing & Subtitle ပြုလုပ်မည်"):
        with st.spinner("AI အသံ ဖန်တီးနေပြီး ဗီဒီယိုနှင့် စိစစ်ချိန်ညှိနေပါသည်။ ခဏစောင့်ပေးပါ..."):
            try:
                # 3. Generate Myanmar TTS Audio
                tts_output_path = "output_voice.mp3"
                asyncio.run(generate_voice(myanmar_text, selected_voice, speed_str, pitch_str, tts_output_path))
                
                # 4. Process Video with MoviePy
                video_clip = VideoFileClip("input_video.mp4")
                audio_clip = AudioFileClip(tts_output_path)
                
                # Adjust volume
                audio_clip = audio_clip.volumex(volume_scale)
                
                # Fit audio or video duration for sync
                final_audio = audio_clip.set_duration(video_clip.duration)
                video_with_audio = video_clip.set_audio(final_audio)
                
                # Output Path
                final_output_path = "final_dubbed_video.mp4"
                video_with_audio.write_videofile(
                    final_output_path, 
                    codec="libx264", 
                    audio_codec="aac",
                    fps=video_clip.fps or 24
                )
                
                # Close clips to release resources
                video_clip.close()
                audio_clip.close()
                
                st.success("✅ AI Dubbing နှင့် Video Sync ပြုလုပ်ခြင်း အောင်မြင်ပါသည်။")
                st.video(final_output_path)
                
                # Download Button
                with open(final_output_path, "rb") as file:
                    st.download_button(
                        label="📥 ပြုလုပ်ပြီးသော Video ကို Download ရယူပါ",
                        data=file,
                        file_name="myanmar_dubbed_video.mp4",
                        mime="video/mp4"
                    )
                    
            except Exception as e:
                st.error(f"Error ဖြစ်ပွားခဲ့သည်: {str(e)}")
