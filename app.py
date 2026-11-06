import streamlit as st
import numpy as np

from music_engine.audio_io import load_audio, wav_bytes
from music_engine.analysis import analyze_vocal
from music_engine.arrangement import build_backing
from music_engine.mixing import make_mix

st.set_page_config(page_title="AI Music Studio", page_icon="🎵", layout="wide")

st.title("🎵 AI Music & Singing Studio")
st.caption("Record or upload a dry vocal, analyze it, and create an original backing-track draft.")

with st.sidebar:
    st.header("Studio settings")
    genre = st.selectbox(
        "Arrangement style",
        ["Bollywood", "Acoustic", "Sad / Emotional", "Punjabi", "Cinematic", "Pop", "Electronic"]
    )
    match_level = st.select_slider("Music Match", ["Balanced", "High", "Maximum"], value="High")
    energy = st.slider("Arrangement energy", 0.2, 1.0, 0.65, 0.05)
    vocal_volume = st.slider("Vocal volume", 0.5, 1.5, 1.0, 0.05)
    music_volume = st.slider("Music volume", 0.1, 1.2, 0.75, 0.05)

tab_sing, tab_prompt, tab_about = st.tabs(
    ["🎙️ Sing & Add Music", "✨ Text-to-Song (coming soon)", "ℹ️ About"]
)

with tab_sing:
    st.subheader("Step 1 — Record or upload your singing")
    recording = st.audio_input("Record your voice without music")
    upload = st.file_uploader(
        "Or upload an audio file",
        type=["wav", "mp3", "m4a", "aac", "flac"]
    )
    source = recording if recording is not None else upload

    if source is not None:
        try:
            audio, sr = load_audio(source.getvalue(), getattr(source, "name", "recording.wav"))
            st.audio(source.getvalue())
            st.caption(f"Loaded audio: {len(audio) / sr:.1f} seconds")

            if st.button("🔍 Analyze Vocal", type="primary"):
                with st.spinner("Analyzing tempo, key and melody..."):
                    analysis = analyze_vocal(audio, sr)
                    st.session_state["source_vocal"] = audio
                    st.session_state["analysis"] = analysis
                    st.session_state.pop("final_mix", None)
                    st.session_state.pop("instrumental", None)
                st.success("Analysis complete.")

            if "analysis" in st.session_state:
                info = st.session_state["analysis"]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Estimated BPM", f"{info['bpm']:.0f}")
                c2.metric("Estimated key", f"{info['key']} {info['mode']}")
                c3.metric("Key confidence", f"{info['key_confidence'] * 100:.0f}%")
                c4.metric("Pitch confidence", f"{info['pitch_confidence'] * 100:.0f}%")

                st.caption(
                    "These are estimates. Key and tempo detection can be uncertain "
                    "for short, noisy, or unaccompanied recordings."
                )
                if match_level == "Maximum":
                    st.info(
                        "Maximum Music Match is selected. This prototype follows the "
                        "estimated tempo and key; detailed note-by-note vocal warping "
                        "is not implemented yet."
                    )

                if st.button("🎹 Generate Music Around My Voice", type="primary"):
                    with st.spinner("Creating chords, bass, drums and arrangement..."):
                        vocal = st.session_state["source_vocal"]
                        instrumental = build_backing(
                            info, genre, len(vocal) / sr, sr=sr, energy=energy
                        )
                        final_mix = make_mix(
                            vocal, instrumental,
                            vocal_gain=vocal_volume,
                            music_gain=music_volume,
                            sr=sr
                        )
                        st.session_state["instrumental"] = instrumental
                        st.session_state["final_mix"] = final_mix
                    st.success("Your song draft is ready!")

                if "final_mix" in st.session_state:
                    st.subheader("Step 2 — Preview and export")
                    st.audio(st.session_state["final_mix"], sample_rate=sr)
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.download_button(
                            "⬇️ Download final mix (WAV)",
                            wav_bytes(st.session_state["final_mix"], sr),
                            file_name="ai_music_studio_mix.wav",
                            mime="audio/wav"
                        )
                    with col_b:
                        st.download_button(
                            "⬇️ Download instrumental (WAV)",
                            wav_bytes(st.session_state["instrumental"], sr),
                            file_name="ai_music_studio_instrumental.wav",
                            mime="audio/wav"
                        )
        except Exception as exc:
            st.error(f"Could not read this audio file: {exc}")
            st.info(
                "Try a WAV file first. MP3/M4A/AAC decoding may require FFmpeg "
                "on your device."
            )

with tab_prompt:
    st.subheader("Describe the song you want")
    st.text_area(
        "Song prompt",
        placeholder="A romantic Hindi song, warm vocal, cinematic strings and gentle piano..."
    )
    st.warning(
        "Full prompt-to-song generation is not connected in this starter project. "
        "It requires a music-generation model/provider and server-side credentials."
    )

with tab_about:
    st.markdown("""
    ### Included in this starter project
    - Microphone recording and audio upload
    - Estimated BPM and musical key
    - Basic vocal pitch analysis
    - Procedural chord, bass and drum backing
    - Simple vocal-led mixing
    - WAV export

    ### Important limitations
    This is a local Python prototype, not a complete commercial AI music platform.
    It does not yet provide neural text-to-song, AI singing, detailed adaptive
    note-by-note accompaniment, stem separation, or professional mastering.
    """)
