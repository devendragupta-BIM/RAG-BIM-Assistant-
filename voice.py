import streamlit as st
from groq import Groq
from streamlit_mic_recorder import mic_recorder
import os
import io
from dotenv import load_dotenv

load_dotenv()

def transcribe_audio(audio_bytes):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "recording.wav"
    transcription = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=audio_file,
        language="en"
    )
    return transcription.text

def answer_voice_question(question, discipline, vectorstore=None):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    context = ""
    if vectorstore:
        try:
            docs = vectorstore.similarity_search(question, k=6)
            context = "\n\n".join([doc.page_content for doc in docs])
        except:
            context = ""

    prompt = f"""You are NexBIM, an expert AI assistant for BIM engineers
specializing in {discipline}.

Answer this spoken question clearly and helpfully.
Give a practical answer with real examples.
{"Use this context from BIM documents: " + context if context else ""}

Question: {question}

Answer:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600
    )
    return response.choices[0].message.content

def render_voice_input(discipline, vectorstore=None):
    st.markdown("""
    <style>
    .voice-input-container {
        position: relative;
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(0,255,178,0.2);
        border-radius: 16px;
        padding: 16px 20px;
        margin: 12px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .voice-input-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        color: #2A4A6A;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .voice-transcript-box {
        background: rgba(0,212,255,0.04);
        border: 1px solid rgba(0,212,255,0.15);
        border-left: 3px solid #00D4FF;
        border-radius: 0 12px 12px 0;
        padding: 14px 18px;
        margin: 10px 0;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.95rem;
        color: #E0F0FF;
        line-height: 1.5;
    }
    .voice-answer-box {
        background: rgba(0,255,178,0.03);
        border: 1px solid rgba(0,255,178,0.12);
        border-left: 3px solid #00FFB2;
        border-radius: 0 12px 12px 0;
        padding: 18px 22px;
        margin: 8px 0;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.92rem;
        color: #A0B4C8;
        line-height: 1.8;
    }
    .voice-mini-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem;
        color: #1E3A5F;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .voice-active-pulse {
        display: inline-block;
        width: 8px; height: 8px;
        background: #FF6B6B;
        border-radius: 50%;
        margin-right: 6px;
        animation: blink 1s infinite;
    }
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }
    .voice-history-compact {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    .vhc-q {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.82rem;
        color: #00D4FF;
        margin-bottom: 4px;
        font-weight: 600;
    }
    .vhc-a {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.8rem;
        color: #4A6A8A;
        line-height: 1.5;
    }
    </style>
    """, unsafe_allow_html=True)

    if "voice_history" not in st.session_state:
        st.session_state.voice_history = []

    if "last_transcript" not in st.session_state:
        st.session_state.last_transcript = None

    if "last_answer" not in st.session_state:
        st.session_state.last_answer = None

    st.markdown("""
    <div class='voice-mini-label'>🎙️ Voice Input — Click mic to speak</div>
    """, unsafe_allow_html=True)

    col_mic, col_clear = st.columns([3, 1])

    with col_mic:
        audio = mic_recorder(
            start_prompt="🎙️  Tap to Speak",
            stop_prompt="⏹️  Done Speaking",
            just_once=True,
            use_container_width=True,
            key="inline_voice_recorder"
        )

    with col_clear:
        if st.button("🗑️ Clear", key="inline_voice_clear",
                use_container_width=True):
            st.session_state.voice_history = []
            st.session_state.last_transcript = None
            st.session_state.last_answer = None
            st.rerun()

    if audio and audio.get("bytes"):
        with st.spinner("🎙️ Transcribing..."):
            try:
                question = transcribe_audio(audio["bytes"])
                st.session_state.last_transcript = question
            except Exception as e:
                st.error(f"Transcription failed: {str(e)}")
                question = None

        if question:
            with st.spinner("🧠 Thinking..."):
                answer = answer_voice_question(
                    question, discipline, vectorstore)
                st.session_state.last_answer = answer

            st.session_state.voice_history.append({
                "question": question,
                "answer": answer
            })

    if st.session_state.last_transcript:
        st.markdown(f"""
        <div class='voice-mini-label'>You Said</div>
        <div class='voice-transcript-box'>
        🎙️ &nbsp; {st.session_state.last_transcript}
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.last_answer:
        st.markdown(f"""
        <div class='voice-mini-label'>NexBIM Answer</div>
        <div class='voice-answer-box'>
        {st.session_state.last_answer.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

    if len(st.session_state.voice_history) > 1:
        with st.expander("📜 Voice History"):
            for item in reversed(
                    st.session_state.voice_history[:-1]):
                st.markdown(f"""
                <div class='voice-history-compact'>
                    <div class='vhc-q'>
                    🎙️ {item['question']}</div>
                    <div class='vhc-a'>
                    {item['answer'][:180]}
                    {'...' if len(item['answer']) > 180 else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

def show_voice():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');
    .voice-page-hero {
        background: linear-gradient(135deg, #050D1A 0%, #0A1628 100%);
        border: 1px solid rgba(0,255,178,0.2);
        border-radius: 20px;
        padding: 32px 36px;
        margin-bottom: 24px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .voice-page-hero::before {
        content: '';
        position: absolute;
        top: -40%; left: 50%;
        transform: translateX(-50%);
        width: 400px; height: 400px;
        background: radial-gradient(circle,
            rgba(0,255,178,0.06) 0%, transparent 70%);
        pointer-events: none;
    }
    .voice-page-title {
        font-family: 'Syne', sans-serif;
        font-size: 2rem; font-weight: 800;
        color: #FFFFFF; margin: 0 0 6px 0;
        letter-spacing: -0.5px;
    }
    .voice-page-title span { color: #00FFB2; }
    .voice-page-sub {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.9rem; color: #4A6A8A;
        max-width: 500px; margin: 0 auto;
    }
    .voice-features {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px; margin: 20px 0;
    }
    .voice-feature-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .voice-feature-icon {
        font-size: 1.8rem; margin-bottom: 8px;
    }
    .voice-feature-text {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.8rem; color: #6B8FAF;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='voice-page-hero'>
        <div style='font-family:JetBrains Mono,monospace;
        font-size:0.68rem; color:#00FFB2;
        letter-spacing:3px; margin-bottom:12px;'>
        ◈ NEXBIM VOICE INTERFACE</div>
        <div class='voice-page-title'>
            Speak to <span>NexBIM</span>
        </div>
        <p class='voice-page-sub'>
            Ask any BIM question using your voice.
            Works exactly like a modern AI assistant.
            Just tap the mic and speak.
        </p>
        <div class='voice-features'>
            <div class='voice-feature-card'>
                <div class='voice-feature-icon'>🎙️</div>
                <div class='voice-feature-text'>
                Tap mic and speak naturally</div>
            </div>
            <div class='voice-feature-card'>
                <div class='voice-feature-icon'>⚡</div>
                <div class='voice-feature-text'>
                Groq Whisper transcription in seconds</div>
            </div>
            <div class='voice-feature-card'>
                <div class='voice-feature-icon'>🧠</div>
                <div class='voice-feature-text'>
                Llama 3.3 answers your BIM question</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    discipline = st.selectbox(
        "Select Discipline",
        ["General BIM", "Architecture", "Structure", "MEP"],
        label_visibility="collapsed",
        key="voice_page_discipline"
    )

    render_voice_input(discipline)

    st.markdown("""
    <div style='text-align:center; margin-top:20px;
    font-family:JetBrains Mono,monospace;
    font-size:0.6rem; color:#0E1E30; letter-spacing:1px;'>
        NEXBIM VOICE · GROQ WHISPER · LLAMA 3.3 ·
        BUILT BY DEVENDRA GUPTA
    </div>
    """, unsafe_allow_html=True)