import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import datetime

from moviepy.editor import VideoFileClip, AudioFileClip
from google import genai


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Myanmar Video Dubbing Studio",
    page_icon="🎙️",
    layout="wide"
)


# =========================================================
# TITLE
# =========================================================

st.title("🎙️ AI မြန်မာ Video Dubbing & Subtitle Studio")

st.write(
    "ဗီဒီယိုထဲက အသံကို Gemini AI ဖြင့် နားထောင်ပြီး "
    "မြန်မာဘာသာသို့ ပြန်ဆိုပေးကာ မြန်မာ AI အသံဖြင့် "
    "Video ပြန်တည်ဆောက်ပေးမည့် System"
)

st.markdown("---")


# =========================================================
# API KEY
# =========================================================

st.subheader("🔑 Gemini API Key")

api_key = st.text_input(
    "Gemini API Key ထည့်ပါ",
    type="password",
    placeholder="AIza....",
    help="Google AI Studio မှ Gemini API Key ထည့်ပါ။"
)

if api_key:
    api_key = api_key.strip()


# =========================================================
# VIDEO UPLOAD
# =========================================================

st.subheader("📹 Video တင်ပါ")

uploaded_video = st.file_uploader(
    "MP4 / MOV / AVI Video ဖိုင် ရွေးပါ",
    type=["mp4", "mov", "avi"]
)


# =========================================================
# MAIN PROCESS
# =========================================================

if uploaded_video:

    # -----------------------------------------------------
    # Create temporary working folder
    # -----------------------------------------------------

    work_dir = tempfile.mkdtemp(prefix="myanmar_dubbing_")

    input_video_path = os.path.join(
        work_dir,
        "input_video.mp4"
    )

    with open(input_video_path, "wb") as f:
        f.write(uploaded_video.getbuffer())


    # -----------------------------------------------------
    # Video Preview
    # -----------------------------------------------------

    st.subheader("👀 တင်ထားသော Video")

    st.video(input_video_path)


    # -----------------------------------------------------
    # Settings
    # -----------------------------------------------------

    st.markdown("---")

    st.subheader("⚙️ အသံနှင့် ဘာသာပြန် ချိန်ညှိချက်များ")

    col1, col2 = st.columns(2)


    # =====================================================
    # VOICE
    # =====================================================

    with col1:

        voice_option = st.selectbox(
            "🎙️ မြန်မာ AI အသံရွေးပါ",
            [
                "Nilar — အမျိုးသမီးအသံ",
                "Thiha — အမျိုးသားအသံ"
            ]
        )

        if "Nilar" in voice_option:
            selected_voice = "my-MM-NilarNeural"
        else:
            selected_voice = "my-MM-ThihaNeural"


        volume_scale = st.slider(
            "🔊 အသံ Volume",
            min_value=0.1,
            max_value=2.0,
            value=1.0,
            step=0.1
        )


    # =====================================================
    # SPEED / PITCH
    # =====================================================

    with col2:

        speed = st.slider(
            "⚡ အသံအမြန် / အနှေး",
            min_value=-50,
            max_value=50,
            value=0,
            step=5
        )

        speed_str = f"{'+' if speed >= 0 else ''}{speed}%"


        pitch = st.slider(
            "🎶 အသံ Pitch",
            min_value=-20,
            max_value=20,
            value=0,
            step=2
        )

        pitch_str = f"{'+' if pitch >= 0 else ''}{pitch}Hz"


    # =====================================================
    # ASYNC EDGE TTS
    # =====================================================

    async def generate_voice(
        text,
        voice,
        rate,
        pitch_value,
        output_file
    ):

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch_value
        )

        await communicate.save(output_file)


    # =====================================================
    # SRT FUNCTION
    # =====================================================

    def seconds_to_srt_time(seconds):

        milliseconds = int((seconds % 1) * 1000)

        total_seconds = int(seconds)

        hours = total_seconds // 3600

        minutes = (total_seconds % 3600) // 60

        secs = total_seconds % 60

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{secs:02d},"
            f"{milliseconds:03d}"
        )


    def create_srt(text, duration):

        start_time = "00:00:00,000"

        end_time = seconds_to_srt_time(duration)

        return (
            "1\n"
            f"{start_time} --> {end_time}\n"
            f"{text}\n"
        )


    # =====================================================
    # START BUTTON
    # =====================================================

    start_button = st.button(
        "🚀 AI မြန်မာအသံ ပြန်ဆိုစတင်မည်",
        type="primary",
        use_container_width=True
    )


    if start_button:

        # -------------------------------------------------
        # Check API Key
        # -------------------------------------------------

        if not api_key:

            st.error(
                "❌ Gemini API Key မထည့်ရသေးပါ။ "
                "အပေါ်မှာ API Key ထည့်ပါ။"
            )

            st.stop()


        status_box = st.empty()


        try:

            # =================================================
            # STEP 1
            # =================================================

            status_box.info(
                "1️⃣ Video ထဲမှ Audio ကို ခွဲထုတ်နေပါသည်..."
            )

            video_clip = VideoFileClip(
                input_video_path
            )

            if video_clip.audio is None:

                video_clip.close()

                st.error(
                    "❌ ဒီ Video ထဲမှာ Audio မပါပါ။"
                )

                st.stop()


            extracted_audio_path = os.path.join(
                work_dir,
                "extracted_audio.mp3"
            )


            video_clip.audio.write_audiofile(
                extracted_audio_path,
                logger=None
            )


            video_duration = video_clip.duration


            # =================================================
            # STEP 2 - GEMINI
            # =================================================

            status_box.info(
                "2️⃣ Gemini AI က Video Audio ကို နားထောင်ပြီး "
                "မြန်မာဘာသာသို့ ပြန်ဆိုနေပါသည်..."
            )


            # New Google GenAI Client
            client = genai.Client(
                api_key=api_key
            )


            # Upload audio to Gemini
            audio_file = client.files.upload(
                file=extracted_audio_path
            )


            prompt = """
You are a professional Myanmar video dubbing translator.

Listen carefully to the audio.

1. Understand what the speaker is saying.
2. Transcribe the meaning.
3. Translate it into natural spoken Myanmar Burmese.
4. Make the Myanmar translation suitable for voice dubbing.
5. Keep the meaning accurate.
6. Do not explain anything.
7. Do not add introductions.
8. Return ONLY the Myanmar translation text.

If there are multiple speakers, preserve the meaning of the conversation naturally.
"""


            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=[
                    prompt,
                    audio_file
                ]
            )


            myanmar_script = response.text.strip()


            if not myanmar_script:

                raise Exception(
                    "Gemini က မြန်မာစာသား ပြန်မပေးနိုင်ပါ။"
                )


            # =================================================
            # SHOW TRANSLATION
            # =================================================

            st.subheader(
                "📝 Gemini AI မှ ပြန်ဆိုထားသော မြန်မာစာ"
            )


            edited_script = st.text_area(
                "လိုအပ်ပါက စာသားကို ကိုယ်တိုင်ပြင်နိုင်ပါသည်",
                value=myanmar_script,
                height=250
            )


            if not edited_script.strip():

                st.error(
                    "❌ မြန်မာစာသား မရှိပါ။"
                )

                video_clip.close()

                st.stop()


            # =================================================
            # STEP 3 - TTS
            # =================================================

            status_box.info(
                "3️⃣ မြန်မာ AI အသံ ထုတ်လုပ်နေပါသည်..."
            )


            tts_output_path = os.path.join(
                work_dir,
                "myanmar_dubbed.mp3"
            )


            asyncio.run(
                generate_voice(
                    edited_script,
                    selected_voice,
                    speed_str,
                    pitch_str,
                    tts_output_path
                )
            )


            # =================================================
            # STEP 4 - AUDIO + VIDEO
            # =================================================

            status_box.info(
                "4️⃣ မြန်မာအသံနှင့် Video ကို ပေါင်းစပ်နေပါသည်..."
            )


            dubbed_audio = AudioFileClip(
                tts_output_path
            )


            # Volume
            dubbed_audio = dubbed_audio.volumex(
                volume_scale
            )


            # -------------------------------------------------
            # Sync Audio Duration
            # -------------------------------------------------

            if dubbed_audio.duration > video_duration:

                # Audio is longer than video.
                # Trim audio to video duration.

                final_audio = dubbed_audio.subclip(
                    0,
                    video_duration
                )

            else:

                # Audio is shorter.
                # Keep audio duration.
                final_audio = dubbed_audio


            final_video = video_clip.set_audio(
                final_audio
            )


            output_video_path = os.path.join(
                work_dir,
                "myanmar_dubbed_video.mp4"
            )


            final_video.write_videofile(
                output_video_path,
                codec="libx264",
                audio_codec="aac",
                fps=video_clip.fps or 24,
                logger=None
            )


            # =================================================
            # STEP 5 - SRT
            # =================================================

            status_box.info(
                "5️⃣ Myanmar Subtitle (.srt) ဖိုင် ပြုလုပ်နေပါသည်..."
            )


            srt_data = create_srt(
                edited_script,
                video_duration
            )


            srt_path = os.path.join(
                work_dir,
                "myanmar_subtitle.srt"
            )


            with open(
                srt_path,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(srt_data)


            # =================================================
            # CLOSE VIDEO / AUDIO
            # =================================================

            try:
                final_audio.close()
            except:
                pass

            try:
                dubbed_audio.close()
            except:
                pass

            try:
                final_video.close()
            except:
                pass

            try:
                video_clip.close()
            except:
                pass


            # =================================================
            # SUCCESS
            # =================================================

            status_box.success(
                "✅ AI Myanmar Dubbing အောင်မြင်စွာ ပြီးပါပြီ!"
            )


            # =================================================
            # FINAL VIDEO
            # =================================================

            st.markdown("---")

            st.subheader(
                "🎬 ပြုလုပ်ပြီးသော Myanmar Dubbed Video"
            )


            st.video(
                output_video_path
            )


            # =================================================
            # DOWNLOAD
            # =================================================

            st.markdown("---")

            st.subheader(
                "📥 ဖိုင်များ Download လုပ်ရန်"
            )


            col1, col2, col3 = st.columns(3)


            # -------------------------------------------------
            # VIDEO
            # -------------------------------------------------

            with col1:

                with open(
                    output_video_path,
                    "rb"
                ) as f:

                    st.download_button(
                        label="🎥 Video Download",
                        data=f.read(),
                        file_name="myanmar_dubbed_video.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )


            # -------------------------------------------------
            # AUDIO
            # -------------------------------------------------

            with col2:

                with open(
                    tts_output_path,
                    "rb"
                ) as f:

                    st.download_button(
                        label="🎵 Audio Download",
                        data=f.read(),
                        file_name="myanmar_audio.mp3",
                        mime="audio/mpeg",
                        use_container_width=True
                    )


            # -------------------------------------------------
            # SRT
            # -------------------------------------------------

            with col3:

                st.download_button(
                    label="📄 SRT Download",
                    data=srt_data.encode("utf-8"),
                    file_name="myanmar_subtitle.srt",
                    mime="text/plain",
                    use_container_width=True
                )


            # =================================================
            # INFO
            # =================================================

            st.markdown("---")

            st.success(
                "🎉 ပြီးပါပြီ။ Video / Audio / Subtitle "
                "ဖိုင် ၃ မျိုးလုံးကို Download လုပ်နိုင်ပါပြီ။"
            )


        except Exception as e:

            # Close video if error occurs
            try:
                video_clip.close()
            except:
                pass


            st.error(
                "❌ Error ဖြစ်ပွားခဲ့ပါသည်။"
            )


            error_text = str(e)


            # API KEY ERROR
            if (
                "API_KEY_INVALID" in error_text
                or "API key not valid" in error_text
                or "INVALID_ARGUMENT" in error_text
            ):

                st.warning(
                    """
🔑 Gemini API Key ပြဿနာဖြစ်နေပါသည်။

1. Google AI Studio မှ API Key အသစ်ထုတ်ပါ။
2. ဒီ App ထဲမှာ Key အသစ်ထည့်ပါ။
3. API Key ရှေ့နောက်မှာ Space မပါစေပါနဲ့။
4. API Key ကို Public မမျှဝေပါနဲ့။
                    """
                )


            else:

                st.code(
                    error_text,
                    language="text"
                )
