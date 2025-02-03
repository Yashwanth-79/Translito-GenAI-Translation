import streamlit as st
import os
from groq import Groq
import tempfile
from gtts import gTTS
import audio_recorder_streamlit as ast
from deep_translator import GoogleTranslator
import time
import numpy as np
from dotenv import load_dotenv
import logging
from cryptography.fernet import Fernet
import secrets

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log'
)

# Load environment variables
load_dotenv()

# Basic security setup
class BasicSecurity:
    def __init__(self):
        # Generate or load encryption key
        self.encryption_key = os.getenv("ENCRYPTION_KEY") or Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def encrypt_text(self, text):
        """Encrypt sensitive text data"""
        if isinstance(text, str):
            return self.cipher_suite.encrypt(text.encode()).decode()
        return text
    
    def decrypt_text(self, encrypted_text):
        """Decrypt sensitive text data"""
        if isinstance(encrypted_text, str):
            try:
                return self.cipher_suite.decrypt(encrypted_text.encode()).decode()
            except:
                return None
        return encrypted_text

# Initialize security
security = BasicSecurity()

# Initialize Groq client
client = Groq(api_key=os.getenv("api_key"))

# Initialize session state
if 'recording_state' not in st.session_state:
    st.session_state.recording_state = 'stopped'
if 'audio_bytes' not in st.session_state:
    st.session_state.audio_bytes = None

def secure_save_audio(audio_bytes):
    """Save audio with secure file handling"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', mode='wb') as f:
            # Set secure file permissions (readable only by owner)
            os.chmod(f.name, 0o600)
            f.write(audio_bytes)
            return f.name
    except Exception as e:
        logging.error(f"Error saving audio: {str(e)}")
        return None

def secure_transcribe_audio(audio_file):
    """Transcribe audio with encryption"""
    try:
        with open(audio_file, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(audio_file, file.read()),
                model="whisper-large-v3",
                response_format="verbose_json"
            )
            # Encrypt the transcribed text
            return security.encrypt_text(transcription.text)
    except Exception as e:
        logging.error(f"Transcription error: {str(e)}")
        return None
    finally:
        # Cleanup temporary file
        try:
            os.remove(audio_file)
        except:
            pass

def secure_translate_text(encrypted_text, target_lang):
    """Translate text with encryption"""
    try:
        # Decrypt for translation
        decrypted_text = security.decrypt_text(encrypted_text)
        if not decrypted_text:
            return None
            
        translator = GoogleTranslator(source='auto', target=target_lang)
        translation = translator.translate(decrypted_text)
        
        # Re-encrypt before returning
        return security.encrypt_text(translation)
    except Exception as e:
        logging.error(f"Translation error: {str(e)}")
        return None

def secure_enhance_medical_terms(encrypted_text):
    """Enhance medical terms with encryption"""
    try:
        # Decrypt for processing
        decrypted_text = security.decrypt_text(encrypted_text)
        if not decrypted_text:
            return None

        completion = client.chat.completions.create(
            model="llama3-groq-70b-8192-tool-use-preview",
            messages=[{
                "role": "system",
                "content": "You are a medical transcription expert. Correct and enhance any medical terminology in the following text while preserving the original meaning. Don't be General, just translate what input you receive."
            }, {
                "role": "user",
                "content": decrypted_text
            }],
            temperature=0.3,
            max_tokens=1024
        )
        
        # Re-encrypt enhanced text
        return security.encrypt_text(completion.choices[0].message.content)
    except Exception as e:
        logging.error(f"Medical term enhancement error: {str(e)}")
        return encrypted_text

def secure_text_to_speech(encrypted_text, lang_code):
    """Convert text to speech with secure handling"""
    try:
        # Decrypt for TTS
        decrypted_text = security.decrypt_text(encrypted_text)
        if not decrypted_text:
            return None

        tts = gTTS(text=decrypted_text, lang=lang_code)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3', mode='wb') as f:
            os.chmod(f.name, 0o600)
            tts.save(f.name)
            return f.name
    except Exception as e:
        logging.error(f"Text-to-speech error: {str(e)}")
        return None

def main():
    st.set_page_config(
        page_title="NaoMedical Translation Assistant",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for enhanced UI
    st.markdown("""
        <style>
        /* Overall app styling */
        .main {
            padding: 1rem;
        }
        
        .stApp {
            background-color: #f8f9fa;
        }
        
        /* Header styling */
        .custom-header {
            background: linear-gradient(135deg, #00467F 0%, #A5CC82 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Section styling */
        .section-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            margin-bottom: 1.5rem;
        }
        
        /* Button styling */
        .stButton > button {
            border-radius: 20px;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        
        /* Recording status */
        .recording-status {
            background: linear-gradient(45deg, #ff4b4b, #ff6b6b);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            margin: 1rem 0;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        /* Audio player styling */
        .stAudio {
            width: 100%;
            margin: 1rem 0;
        }
        
        /* Language selector styling */
        .stSelectbox {
            margin-bottom: 1rem;
        }
        
        /* Text display areas */
        .text-output {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            margin: 0.5rem 0;
        }
        
        /* Helper text */
        .helper-text {
            color: #6c757d;
            font-size: 0.9rem;
            font-style: italic;
            margin-bottom: 1rem;
        }
        
        /* Progress spinner */
        .stSpinner {
            text-align: center;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
        <div class="custom-header">
            <h1>Healthcare Translation Assistant</h1>
            <p>Powered by Advanced AI for Accurate Medical Translations</p>
        </div>
    """, unsafe_allow_html=True)

    # Quick Guide
    with st.expander("📖 How to Use This Tool", expanded=True):
        st.markdown("""
            ### Quick Start Guide
            1. **Choose Languages**: Select your source and target languages
            2. **Record Speech**: Use the recording controls to capture speech
            3. **Review & Listen**: Check both the original and translated text
            4. **Playback Options**: Listen to both versions in their respective languages
            
            **Tips for Best Results:**
            - Speak clearly and at a normal pace
            - Minimize background noise
            - Use proper medical terminology when possible
            - Wait for the translation to complete before recording again
        """)

    # Language Selection Section
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🌐 Language Settings")
    
    languages = {
        'English': 'en', 'Spanish': 'es', 'French': 'fr',
        'German': 'de', 'Italian': 'it', 'Portuguese': 'pt',
        'Chinese (Simplified)': 'zh-CN', 'Chinese (Traditional)': 'zh-TW',
        'Japanese': 'ja', 'Korean': 'ko', 'Hindi': 'hi',
        'Arabic': 'ar', 'Russian': 'ru', 'Bengali': 'bn',
        'Indonesian': 'id', 'Turkish': 'tr', 'Vietnamese': 'vi',
        'Dutch': 'nl', 'Greek': 'el', 'Hebrew': 'he',
        'Swedish': 'sv', 'Norwegian': 'no', 'Danish': 'da',
        'Polish': 'pl', 'Czech': 'cs', 'Hungarian': 'hu',
        'Finnish': 'fi', 'Thai': 'th', 'Filipino': 'fil',
        'Malay': 'ms', 'Urdu': 'ur', 'Tamil': 'ta',
        'Telugu': 'te', 'Marathi': 'mr', 'Punjabi': 'pa',
        'Gujarati': 'gu', 'Ukrainian': 'uk', 'Romanian': 'ro',
        'Bulgarian': 'bg', 'Serbian': 'sr', 'Croatian': 'hr',
        'Slovak': 'sk', 'Slovenian': 'sl', 'Lithuanian': 'lt',
        'Latvian': 'lv', 'Estonian': 'et', 'Icelandic': 'is',
        'Afrikaans': 'af', 'Albanian': 'sq', 'Amharic': 'am',
        'Armenian': 'hy', 'Azerbaijani': 'az', 'Basque': 'eu',
        'Belarusian': 'be', 'Bosnian': 'bs', 'Catalan': 'ca',
        'Cebuano': 'ceb', 'Corsican': 'co', 'Esperanto': 'eo',
        'Frisian': 'fy', 'Galician': 'gl', 'Georgian': 'ka',
        'Haitian Creole': 'ht', 'Hausa': 'ha', 'Hawaiian': 'haw',
        'Hmong': 'hmn', 'Igbo': 'ig', 'Irish': 'ga',
        'Javanese': 'jw', 'Kannada': 'kn', 'Kazakh': 'kk',
        'Khmer': 'km', 'Kinyarwanda': 'rw', 'Kurdish': 'ku',
        'Kyrgyz': 'ky', 'Lao': 'lo', 'Latin': 'la',
        'Luxembourgish': 'lb', 'Macedonian': 'mk', 'Malagasy': 'mg',
        'Malayalam': 'ml', 'Maltese': 'mt', 'Maori': 'mi',
        'Mongolian': 'mn', 'Myanmar (Burmese)': 'my', 'Nepali': 'ne',
        'Nyanja (Chichewa)': 'ny', 'Odia (Oriya)': 'or', 'Pashto': 'ps',
        'Persian': 'fa', 'Samoan': 'sm', 'Scots Gaelic': 'gd',
        'Sesotho': 'st', 'Shona': 'sn', 'Sindhi': 'sd',
        'Sinhala (Sinhalese)': 'si', 'Somali': 'so', 'Sundanese': 'su',
        'Swahili': 'sw', 'Tagalog (Filipino)': 'tl', 'Tajik': 'tg',
        'Tatar': 'tt', 'Turkmen': 'tk', 'Uyghur': 'ug',
        'Uzbek': 'uz', 'Welsh': 'cy', 'Xhosa': 'xh',
        'Yiddish': 'yi', 'Yoruba': 'yo', 'Zulu': 'zu'
    }
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p class="helper-text">Select the language you\'ll speak in</p>', unsafe_allow_html=True)
        source_lang = st.selectbox("From (Source Language)", list(languages.keys()), index=0)
    with col2:
        st.markdown('<p class="helper-text">Select the language to translate to</p>', unsafe_allow_html=True)
        target_lang = st.selectbox("To (Target Language)", list(languages.keys()), index=1)
    st.markdown('</div>', unsafe_allow_html=True)

    # Recording Section
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🎙️ Voice Recording")
    st.markdown('<p class="helper-text">Record your voice for translation</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎙️ Start Recording",
                    type="primary" if st.session_state.recording_state != 'recording' else "secondary",
                    disabled=st.session_state.recording_state == 'recording',
                    help="Click to start recording your voice"):
            st.session_state.recording_state = 'recording'
            st.session_state.audio_bytes = None
            st.rerun()
    
    with col2:
        if st.button("⏹️ Stop Recording",
                    type="primary" if st.session_state.recording_state == 'recording' else "secondary",
                    disabled=st.session_state.recording_state != 'recording',
                    help="Click to stop recording"):
            st.session_state.recording_state = 'stopped'
            st.rerun()
    
    with col3:
        if st.button("🔄 Reset",
                    disabled=st.session_state.recording_state == 'recording',
                    help="Clear the current recording and start over"):
            st.session_state.recording_state = 'stopped'
            st.session_state.audio_bytes = None
            st.rerun()

    # Recording Status and Audio Capture
    if st.session_state.recording_state == 'recording':
        st.markdown("""
            <div class="recording-status">
                🎙️ Recording in progress... Speak clearly into your microphone
                <br><small>Click 'Stop Recording' when finished</small>
            </div>
        """, unsafe_allow_html=True)
        
        audio_bytes = ast.audio_recorder(pause_threshold=60.0, sample_rate=44100)
        
        if audio_bytes:
            st.session_state.audio_bytes = audio_bytes
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Audio Playback and Translation Results
    if st.session_state.audio_bytes:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📝 Recording Playback")
        st.audio(st.session_state.audio_bytes, format="audio/wav")
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.spinner("🔄 Processing your recording... This may take a moment"):
            audio_file = secure_save_audio(st.session_state.audio_bytes)
            
            if audio_file:
                transcription = secure_transcribe_audio(audio_file)
                
                if transcription:
                    enhanced_text = secure_enhance_medical_terms(transcription)
                    translation = secure_translate_text(enhanced_text, languages[target_lang])
                    
                    st.markdown('<div class="section-card">', unsafe_allow_html=True)
                    st.subheader("🔄 Translation Results")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### Original Text")
                        st.markdown('<div class="text-output">', unsafe_allow_html=True)
                        st.write(security.decrypt_text(enhanced_text))
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        if st.button("🔊 Play Original", key="play_original",
                                   help="Listen to the original text"):
                            with st.spinner("Generating audio..."):
                                audio_file = secure_text_to_speech(enhanced_text, languages[source_lang])
                                if audio_file:
                                    st.audio(audio_file)
                                    os.remove(audio_file)
                    
                    with col2:
                        st.markdown("### Translation")
                        st.markdown('<div class="text-output">', unsafe_allow_html=True)
                        st.write(security.decrypt_text(translation))
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        if st.button("🔊 Play Translation", key="play_translation",
                                   help="Listen to the translated text"):
                            with st.spinner("Generating audio..."):
                                audio_file = secure_text_to_speech(translation, languages[target_lang])
                                if audio_file:
                                    st.audio(audio_file)
                                    os.remove(audio_file)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("""
        <div style="text-align: center; margin-top: 2rem; padding: 1rem; color: #6c757d;">
            <p>Developed by Yashwanth M S | Powered by Advanced AI</p>
            <p style="font-size: 0.8rem;">For medical translation purposes only</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
