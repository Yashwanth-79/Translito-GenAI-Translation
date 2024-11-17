import streamlit as st
import os
from groq import Groq
import tempfile
from gtts import gTTS
import audio_recorder_streamlit as ast  # Use streamlit_audio_recorder
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
    st.set_page_config(page_title="NaoMedical", layout="wide")
    
    st.markdown("""<style> .stAudio { width: 100%; } </style>""", unsafe_allow_html=True)
    st.markdown(" ## Healthcare Translation Web App with Generative AI")
    st.text("By [Nao Medical](https://naomedical.com)")

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
    'Hmong': 'hmn', 'Icelandic': 'is', 'Igbo': 'ig',
    'Irish': 'ga', 'Javanese': 'jw', 'Kannada': 'kn',
    'Kazakh': 'kk', 'Khmer': 'km', 'Kinyarwanda': 'rw',
    'Kurdish': 'ku', 'Kyrgyz': 'ky', 'Lao': 'lo',
    'Latin': 'la', 'Luxembourgish': 'lb', 'Macedonian': 'mk',
    'Malagasy': 'mg', 'Malayalam': 'ml', 'Maltese': 'mt',
    'Maori': 'mi', 'Mongolian': 'mn', 'Myanmar (Burmese)': 'my',
    'Nepali': 'ne', 'Nyanja (Chichewa)': 'ny', 'Odia (Oriya)': 'or',
    'Pashto': 'ps', 'Persian': 'fa', 'Samoan': 'sm',
    'Scots Gaelic': 'gd', 'Sesotho': 'st', 'Shona': 'sn',
    'Sindhi': 'sd', 'Sinhala (Sinhalese)': 'si', 'Somali': 'so',
    'Sundanese': 'su', 'Swahili': 'sw', 'Tagalog (Filipino)': 'tl',
    'Tajik': 'tg', 'Tatar': 'tt', 'Turkmen': 'tk',
    'Uyghur': 'ug', 'Uzbek': 'uz', 'Welsh': 'cy',
    'Xhosa': 'xh', 'Yiddish': 'yi', 'Yoruba': 'yo', 'Zulu': 'zu'
    }
    
    col1, col2 = st.columns(2)
    with col1:
        source_lang = st.selectbox("Source Language", list(languages.keys()), index=0)
    with col2:
        target_lang = st.selectbox("Target Language", list(languages.keys()), index=1)
    
    st.subheader("Voice Recording")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎙️ Start Recording", 
                    type="primary" if st.session_state.recording_state != 'recording' else "secondary",
                    disabled=st.session_state.recording_state == 'recording'):
            st.session_state.recording_state = 'recording'
            st.session_state.audio_bytes = None
            st.rerun()
    
    with col2:
        if st.button("⏹️ Stop", 
                    type="primary" if st.session_state.recording_state == 'recording' else "secondary",
                    disabled=st.session_state.recording_state != 'recording'):
            st.session_state.recording_state = 'stopped'
            st.rerun()
    
    with col3:
        if st.button("🔄 Reset",
                    disabled=st.session_state.recording_state == 'recording'):
            st.session_state.recording_state = 'stopped'
            st.session_state.audio_bytes = None
            st.rerun()

    if st.session_state.recording_state == 'recording':
        st.markdown("""<div class="recording-status" style="background-color: #ff4b4b; color: white;"> Recording in progress... 🎙️ </div>""", unsafe_allow_html=True)
        
        audio_bytes = ast.audio_recorder(pause_threshold=60.0, sample_rate=44100)  # Using streamlit_audio_recorder
        
        if audio_bytes:
            st.session_state.audio_bytes = audio_bytes
    
    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/wav")
        
        with st.spinner("Processing audio..."):
            audio_file = secure_save_audio(st.session_state.audio_bytes)
            
            if audio_file:
                transcription = secure_transcribe_audio(audio_file)
                
                if transcription:
                    enhanced_text = secure_enhance_medical_terms(transcription)
                    
                    translation = secure_translate_text(enhanced_text, languages[target_lang])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"<h3>Original Text</h3><p>{security.decrypt_text(enhanced_text)}</p>", unsafe_allow_html=True)
                        
                        if st.button("🔊 Play Original"):
                            audio_file = secure_text_to_speech(enhanced_text, languages[source_lang])
                            if audio_file:
                                st.audio(audio_file)
                                os.remove(audio_file)
                    
                    with col2:
                        st.markdown(f"<h3>Translation</h3><p>{security.decrypt_text(translation)}</p>", unsafe_allow_html=True)
                        
                        if st.button("🔊 Play Translation"):
                            audio_file = secure_text_to_speech(translation, languages[target_lang])
                            if audio_file:
                                st.audio(audio_file)
                                os.remove(audio_file)

if __name__ == "__main__":
    main()
