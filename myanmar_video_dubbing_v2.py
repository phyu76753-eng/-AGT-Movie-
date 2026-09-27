import streamlit as st
import os
import tempfile
import numpy as np
from PIL import Image, ImageEnhance
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, vfx
import asyncio

# Page Configuration for Mobile & Desktop
st.set_page_config(
    page_title="Myanmar AI Video Dubbing & Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎬 Myanmar AI Video Dubbing & Color Studio")
st.caption("မြန်မာဘာသာ သို့မဟုတ် အခြား ဘာသာစကားများမှ ဗီဒီယို အသံပြောင်းပေးခြင်း၊ အသံထပ်ခြင်း (Dubbing) နှင့် အရောင်၊ တောက်ပမှု ပြင်ဆင်ခြင်းများကို All-in-One ပြုလုပ်နိုင်သော AI နည်းပညာသုံး ဗီဒီယို စတူဒီယို ဖြစ်ပါသည်။")

# Sidebar for API Keys and Settings
with st.sidebar:
    st.header("⚙️ API Keys & Settings")
    api_provider = st.selectbox(
        "TTS Engine ရွေးချယ်ပါ",
        ["gTTS (Google Translate)", "edge-tts (Microsoft Edge)"]
    )
    
    if "edge-tts" in api_provider:
        edge_voice = st.selectbox(
            "Edge TTS Voice",
            ["my-MM-ThihaNeural (Male)", "my-MM-NilarNeural (Female)", "en-US-AvaMultilingualNeural (Female)", "en-US-AndrewMultilingualNeural (Male)"]
        )
    else:
        gtts_lang = st.selectbox(
            "gTTS Language",
            ["my (Myanmar)", "en (English)", "ja (Japanese)", "ko (Korean)", "zh-CN (Chinese)"]
        )

    st.markdown("---")
    st.header("🎨 Video Color & Quality")
    brightness = st.slider("Brightness (တောက်ပမှု)", 0.5, 2.0, 1.0, 0.1)
    contrast = st.slider("Contrast (အလင်းအမှောင် ကွာခြားမှု)", 0.5, 2.0, 1.0, 0.1)
    color = st.slider("Color Saturation (အရောင် ရင့်/ဖျော့)", 0.0, 2.0, 1.0, 0.1)

# Main UI Tabs
tab1, tab2 = st.tabs(["🎙️ Video Dubbing & Processing", "ℹ️ How to Use"])

with tab1:
    st.subheader("၁။ ဗီဒီယို ဖိုင် တင်ပါ (Upload Video)")
    uploaded_video = st.file_uploader("MP4, MOV သို့မဟုတ် AVI ဖိုင် တင်ပါ", type=["mp4", "mov", "avi"])

    st.subheader("၂။ စာသား သို့မဟုတ် အသံ ရေးသား/ထည့်သွင်းပါ")
    dubbing_text = st.text_area("ဗီဒီယိုထဲတွင် ထည့်သွင်းလိုသော မြန်မာ/အင်္ဂလိပ် စာသားကို ရေးပါ", height=120, placeholder="ဒီမှာ စာသား ရိုက်ထည့်ပါ...")

    keep_original_audio = st.checkbox("မူလ အသံနောက်ခံ (Background Audio) ကို တိုးတိုးလေး ချန်ထားမည်", value=True)
    if keep_original_audio:
        bg_volume = st.slider("မူလ အသံ ကျယ်/တိုး (Background Volume)", 0.0, 1.0, 0.2, 0.05)

    if st.button("🚀 ဗီဒီယို စတင် ပြုပြင်မည် (Start Processing)", type="primary"):
        if uploaded_video is not None and dubbing_text.strip() != "":
            with st.spinner("ဗီဒီယိုနှင့် အသံကို AI ဖြင့် ပြုပြင်နေပါသည်... ခဏစောင့်ပါ..."):
                try:
                    # Save uploaded video to temp file
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    tfile.write(uploaded_video.read())
                    tfile.close()

                    # 1. Generate TTS Audio
                    tts_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                    
                    if "edge-tts" in api_provider:
                        voice_code = edge_voice.split(" ")[0]
                        async def generate_edge_tts():
                            import edge_tts
                            communicate = edge_tts.Communicate(dubbing_text, voice_code)
                            await communicate.save(tts_audio_path)
                        asyncio.run(generate_edge_tts())
                    else:
                        from gtts import gTTS
                        lang_code = gtts_lang.split(" ")[0]
                        tts = gTTS(text=dubbing_text, lang=lang_code)
                        tts.save(tts_audio_path)

                    # 2. Process Video with MoviePy
                    video_clip = VideoFileClip(tfile.name)
                    
                    # Apply Color Enhancements frame by frame or filter
                    def enhance_frame(frame):
                        img = Image.fromarray(frame)
                        if brightness != 1.0:
                            img = ImageEnhance.Brightness(img).enhance(brightness)
                        if contrast != 1.0:
                            img = ImageEnhance.Contrast(img).enhance(contrast)
                        if color != 1.0:
                            img = ImageEnhance.Color(img).enhance(color)
                        return np.array(img)

                    processed_video = video_clip.fl_image(enhance_frame)

                    # 3. Audio Mixing
                    new_audio = AudioFileClip(tts_audio_path)
                    
                    if keep_original_audio and video_clip.audio is not None:
                        orig_audio = video_clip.audio.volumex(bg_volume)
                        final_audio = CompositeAudioClip([orig_audio, new_audio.set_start(0)])
                    else:
                        final_audio = new_audio

                    # Set final audio to video
                    final_video = processed_video.set_audio(final_audio)

                    # Export Final Video
                    output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")

                    st.success("🎉 ဗီဒီယို ပြုပြင်ခြင်း အောင်မြင်စွာ ပြီးစီးပါပြီ!")
                    st.video(output_path)

                    with open(output_path, "rb") as file:
                        st.download_button(
                            label="📥 ပြုပြင်ထားသော ဗီဒီယို ဒေါင်းလုဒ်ဆွဲပါ",
                            data=file,
                            file_name="dubbed_video.mp4",
                            mime="video/mp4"
                        )

                except Exception as e:
                    st.error(f"အမှားအယွင်း ဖြစ်ပေါ်ခဲ့ပါသည်။ Error: {e}")
        else:
            st.warning("ကျေးဇူးပြု၍ ဗီဒီယို ဖိုင်နှင့် စာသား နှစ်ခုလုံး ထည့်သွင်းပေးပါခင်ဗျာ။")

with tab2:
    st.subheader("📖 အသုံးပြုနည်း လမ်းညွှန်")
    st.markdown("""
    ၁။ ဘယ်ဘက် ဘား (Sidebar) မှ မိမိ အသုံးပြုလိုသော TTS Engine နှင့် အသံအမျိုးအစားကို ရွေးချယ်ပါ။
    ၂။ အရောင် သို့မဟုတ် တောက်ပမှု ပြောင်းလဲလိုပါက Brightness, Contrast, Color Slider များကို သင့်တော်သလို ချိန်ညှိပါ။
    ၃။ ဗီဒီယို ဖိုင်ကို Upload ပြုလုပ်ပြီး ထည့်သွင်းလိုသော စာသားကို ရေးသားပါ။
    ၄။ 'ဗီဒီယို စတင် ပြုပြင်မည်' ခလုတ်ကို နှိပ်ပြီး ခဏစောင့်ဆိုင်းပါ။
    ၅။ ပြုပြင်ပြီးပါက ဗီဒီယိုကို ကြည့်ရှုနိုင်ပြီး ဒေါင်းလုဒ် ဆွဲယူနိုင်ပါပြီ။
    """)
