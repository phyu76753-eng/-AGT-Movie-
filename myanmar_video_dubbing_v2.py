import streamlit as st
import asyncio
import edge_tts
from moviepy.editor import VideoFileClip, AudioFileClip
import google.generativeai as genai
import os
import datetime

st.set_page_config(page_title="AI Myanmar Video Dubbing Studio", layout="wide")

st.title("🎙️ AI မြန်မာ Video Dubbing & Subtitle Studio")
st.write("မည်သည့် ဘာသာစကားမဆို ပါဝင်သော ဗီဒီယိုကို မြန်မာဘာသာသို့ အလိုအလျောက် ပြန်ဆိုပေးခြင်း၊ အသံချိန်ညှိခြင်းနှင့် Subtitle/Audio ထုတ်ယူခြင်း စနစ်")

# 1. API Key Setup
api_key = st.text_input("🔑 Gemini API Key ထည့်ပါ -", type="password", help="Google AI Studio မှ အခမဲ့ ရယူနိုင်ပါသည်။")

# 2. Video File Uploader & Preview
uploaded_video = st.file_uploader("📹 ဗီဒီယိုဖိုင် တင်ပါ (MP4, MOV, AVI)", type=["mp4", "mov", "avi"])

if uploaded_video:
    # Save input video locally
    with open("input_video.mp4", "wb") as f:
        f.write(uploaded_video.read())
    
    st.subheader("👀 တင်သွင်းထားသော Video ပြသမှု")
    st.video("input_video.mp4")

if uploaded_video and api_key:
    genai.configure(api_key=api_key)
    
    st.markdown("---")
    st.subheader("⚙️ အသံနှင့် ဘာသာပြန် ချိန်ညှိချက်များ")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # အမျိုးသမီး/အမျိုးသား အသံ ရွေးချယ်မှု
        voice_option = st.selectbox("🎙️ မြန်မာ AI အသံ ရွေးချယ်ပါ", [
            "my-MM-NilarNeural (အမျိုးသမီး)",
            "my-MM-ThihaNeural (အမျိုးသား)"
        ])
        selected_voice = "my-MM-NilarNeural" if "Nilar" in voice_option else "my-MM-ThihaNeural"
        
        # အသံ အတိုး/အကျယ်
        volume_scale = st.slider("🔊 အသံ အတိုး/အကျယ် (Volume)", 0.1, 2.0, 1.0, 0.1)

    with col2:
        # အသံ အမြန်/အနှေး
        speed = st.slider("⚡ အသံ အမြန်/အနှေး (Speed %)", -50, 50, 0, 5)
        speed_str = f"{'+' if speed >= 0 else ''}{speed}%"
        
        # အသံ အနိမ့်/အမြင့်
        pitch = st.slider("🎶 အသံ အနိမ့်/အမြင့် (Pitch Hz)", -20, 20, 0, 2)
        pitch_str = f"{'+' if pitch >= 0 else ''}{pitch}Hz"

    # Async Edge-TTS Voice Generation
    async def generate_voice(text, voice, rate, pitch_val, output_file):
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch_val)
        await communicate.save(output_file)

    # SRT Subtitle Helper Function
    def create_srt(text, duration):
        start_time = "00:00:00,000"
        
        # Convert total duration to SRT timestamp format
        td = datetime.timedelta(seconds=duration)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        millis = int(td.microseconds / 1000)
        end_time = f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
        
        srt_content = f"1\n{start_time} --> {end_time}\n{text}\n"
        return srt_content

    if st.button("🚀 AI မြန်မာအသံ ပြန်ဆိုစတင်မည်"):
        status_box = st.empty()
        
        try:
            # Step 1: Extract Audio
            status_box.info("1️⃣ ဗီဒီယိုထဲမှ Audio ကို ခွဲထုတ်နေပါသည်...")
            video_clip = VideoFileClip("input_video.mp4")
            extracted_audio_path = "extracted_audio.mp3"
            video_clip.audio.write_audiofile(extracted_audio_path, logger=None)
            
            # Step 2: Gemini AI Speech Translation
            status_box.info("2️⃣ Gemini AI မှ ဘာသာစကားကို နားထောင်၍ မြန်မာစာသား ပြန်ဆိုနေပါသည်...")
            audio_file = genai.upload_file(extracted_audio_path)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = "Listen to this audio. Transcribe and translate the spoken content into natural Myanmar text for dubbing. Return ONLY the Myanmar translation text."
            response = model.generate_content([audio_file, prompt])
            myanmar_script = response.text.strip()
            
            # Display Translated Text
            st.subheader("📝 AI မှ ဘာသာပြန်ပေးထားသော မြန်မာ စာသား -")
            edited_script = st.text_area("လိုအပ်ပါက ပြင်ဆင်နိုင်ပါသည် -", myanmar_script, height=120)
            
            # Step 3: Generate Myanmar Audio
            status_box.info("3️⃣ မြန်မာ AI အသံ ထုတ်လုပ်နေပါသည်...")
            tts_output_path = "myanmar_dubbed.mp3"
            asyncio.run(generate_voice(edited_script, selected_voice, speed_str, pitch_str, tts_output_path))
            
            # Step 4: Adjust Audio Volume & Video Duration Sync
            status_box.info("4️⃣ အသံနှင့် ဗီဒီယို ကိုက်ညီအောင် ညှိယူ ပေါင်းစပ်နေပါသည်...")
            dubbed_audio = AudioFileClip(tts_output_path).volumex(volume_scale)
            
            # Sync duration with video
            final_audio = dubbed_audio.set_duration(video_clip.duration)
            final_video = video_clip.set_audio(final_audio)
            
            output_video_path = "final_output_video.mp4"
            final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac", fps=video_clip.fps or 24)
            
            # Step 5: Generate SRT Content
            srt_data = create_srt(edited_script, video_clip.duration)
            
            # Cleanup clips
            video_clip.close()
            dubbed_audio.close()
            
            status_box.success("✅ AI Dubbing & Sync ပြုလုပ်ခြင်း အောင်မြင်ပါသည်။")
            
            # Preview Final Video
            st.subheader("🎬 ပြုလုပ်ပြီးသော Video စမ်းသပ်ကြည့်ရှုရန်")
            st.video(output_video_path)
            
            st.markdown("---")
            st.subheader("📥 ဒေါင်းလုဒ် ရယူရန် ဖိုင်များ")
            
            col_d1, col_d2, col_d3 = st.columns(3)
            
            # 1. Video Download
            with col_d1:
                with open(output_video_path, "rb") as f:
                    st.download_button(
                        label="🎥 Video ဖိုင် (.mp4) ဒေါင်းရန်",
                        data=f,
                        file_name="myanmar_dubbed_video.mp4",
                        mime="video/mp4"
                    )
            
            # 2. Audio Only Download
            with col_d2:
                with open(tts_output_path, "rb") as f:
                    st.download_button(
                        label="🎵 မြန်မာ အသံဖိုင် (.mp3) ဒေါင်းရန်",
                        data=f,
                        file_name="myanmar_audio.mp3",
                        mime="audio/mp3"
                    )
                    
            # 3. SRT Subtitle Download
            with col_d3:
                st.download_button(
                    label="📄 Subtitle ဖိုင် (.srt) ဒေါင်းရန်",
                    data=srt_data,
                    file_name="myanmar_subtitle.srt",
                    mime="text/plain"
                )
                
        except Exception as e:
            status_box.error(f"❌ Error ဖြစ်ပွားခဲ့သည်: {str(e)}")
