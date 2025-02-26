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
from langdetect import detect, LangDetectException

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

# Language code mapping (ISO 639-1 to language name)
def get_language_code_mapping():
    return {
        'en': 'English', 'es': 'Spanish', 'fr': 'French',
        'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
        'zh-cn': 'Chinese (Simplified)', 'zh-tw': 'Chinese (Traditional)',
        'ja': 'Japanese', 'ko': 'Korean', 'hi': 'Hindi',
        'ar': 'Arabic', 'ru': 'Russian', 'bn': 'Bengali',
        'id': 'Indonesian', 'tr': 'Turkish', 'vi': 'Vietnamese',
        'nl': 'Dutch', 'el': 'Greek', 'he': 'Hebrew',
        'sv': 'Swedish', 'no': 'Norwegian', 'da': 'Danish',
        'pl': 'Polish', 'cs': 'Czech', 'hu': 'Hungarian',
        'fi': 'Finnish', 'th': 'Thai', 'fil': 'Filipino',
        'ms': 'Malay', 'ur': 'Urdu', 'ta': 'Tamil',
        'te': 'Telugu', 'mr': 'Marathi', 'pa': 'Punjabi',
        'gu': 'Gujarati', 'uk': 'Ukrainian', 'ro': 'Romanian',
        'bg': 'Bulgarian', 'sr': 'Serbian', 'hr': 'Croatian',
        'sk': 'Slovak', 'sl': 'Slovenian', 'lt': 'Lithuanian',
        'lv': 'Latvian', 'et': 'Estonian', 'is': 'Icelandic',
        'af': 'Afrikaans', 'sq': 'Albanian', 'am': 'Amharic',
        'hy': 'Armenian', 'az': 'Azerbaijani', 'eu': 'Basque',
        'be': 'Belarusian', 'bs': 'Bosnian', 'ca': 'Catalan',
        'ceb': 'Cebuano', 'co': 'Corsican', 'eo': 'Esperanto',
        'fy': 'Frisian', 'gl': 'Galician', 'ka': 'Georgian',
        'ht': 'Haitian Creole', 'ha': 'Hausa', 'haw': 'Hawaiian',
        'hmn': 'Hmong', 'is': 'Icelandic', 'ig': 'Igbo',
        'ga': 'Irish', 'jw': 'Javanese', 'kn': 'Kannada',
        'kk': 'Kazakh', 'km': 'Khmer', 'rw': 'Kinyarwanda',
        'ku': 'Kurdish', 'ky': 'Kyrgyz', 'lo': 'Lao',
        'la': 'Latin', 'lb': 'Luxembourgish', 'mk': 'Macedonian',
        'mg': 'Malagasy', 'ml': 'Malayalam', 'mt': 'Maltese',
        'mi': 'Maori', 'mn': 'Mongolian', 'my': 'Myanmar (Burmese)',
        'ne': 'Nepali', 'ny': 'Nyanja (Chichewa)', 'or': 'Odia (Oriya)',
        'ps': 'Pashto', 'fa': 'Persian', 'sm': 'Samoan',
        'gd': 'Scots Gaelic', 'st': 'Sesotho', 'sn': 'Shona',
        'sd': 'Sindhi', 'si': 'Sinhala (Sinhalese)', 'so': 'Somali',
        'su': 'Sundanese', 'sw': 'Swahili', 'tl': 'Tagalog (Filipino)',
        'tg': 'Tajik', 'tt': 'Tatar', 'tk': 'Turkmen',
        'ug': 'Uyghur', 'uz': 'Uzbek', 'cy': 'Welsh',
        'xh': 'Xhosa', 'yi': 'Yiddish', 'yo': 'Yoruba', 'zu': 'Zulu'
    }

# Get language name from code
def get_language_name(code):
    code_mapping = get_language_code_mapping()
    # Make code lowercase to handle different cases
    code = code.lower()
    
    # Handle special cases and mapping differences
    if code == 'zh':
        return 'Chinese (Simplified)'
    
    if code in code_mapping:
        return code_mapping[code]
    
    # If not found, return the code itself
    return code

# Initialize session state
if 'recording_state' not in st.session_state:
    st.session_state.recording_state = 'stopped'
if 'audio_bytes' not in st.session_state:
    st.session_state.audio_bytes = None
if 'detected_language' not in st.session_state:
    st.session_state.detected_language = None
if 'auto_detect' not in st.session_state:
    st.session_state.auto_detect = True

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
            # Return both the text and detected language
            return {
                "text": security.encrypt_text(transcription.text),
                "language": transcription.language  # Whisper provides detected language
            }
    except Exception as e:
        logging.error(f"Transcription error: {str(e)}")
        return None
    finally:
        # Cleanup temporary file
        try:
            os.remove(audio_file)
        except:
            pass

def detect_language(text):
    """Detect language from text as fallback"""
    try:
        return detect(text)
    except LangDetectException:
        return None

def secure_translate_text(encrypted_text, source_lang_code, target_lang_code):
    """Translate text with encryption and explicit source language"""
    try:
        # Decrypt for translation
        decrypted_text = security.decrypt_text(encrypted_text)
        if not decrypted_text:
            return None

        # Use explicit source language instead of 'auto'
        translator = GoogleTranslator(source=source_lang_code, target=target_lang_code)
        translation = translator.translate(decrypted_text)

        # Re-encrypt before returning
        return security.encrypt_text(translation)
    except Exception as e:
        logging.error(f"Translation error: {str(e)}")
        # Fallback to auto detection if explicit source fails
        try:
            translator = GoogleTranslator(source='auto', target=target_lang_code)
            translation = translator.translate(decrypted_text)
            return security.encrypt_text(translation)
        except:
            return None

def secure_enhance_medical_terms(encrypted_text, detected_lang=None):
    """Enhance medical terms with encryption"""
    try:
        # Decrypt for processing
        decrypted_text = security.decrypt_text(encrypted_text)
        if not decrypted_text:
            return None

        prompt = "You are a translation and transcription expert. "
        if detected_lang:
            prompt += f"The text is in {detected_lang}. "
        prompt += "Correct and enhance any terminology in the following text while preserving the original meaning. Just translate what input you receive."

        completion = client.chat.completions.create(
            model="llama3-groq-70b-8192-tool-use-preview",
            messages=[{
                "role": "system",
                "content": prompt
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

        # Handle special cases for TTS compatibility
        if lang_code == 'zh-CN':
            lang_code = 'zh-cn'
        elif lang_code == 'zh-TW':
            lang_code = 'zh-tw'
            
        # Check if language is supported by gTTS, fallback to English if not
        try:
            tts = gTTS(text=decrypted_text, lang=lang_code)
        except:
            st.warning(f"TTS not available for selected language. Using English instead.")
            tts = gTTS(text=decrypted_text, lang='en')
            
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3', mode='wb') as f:
            os.chmod(f.name, 0o600)
            tts.save(f.name)
            return f.name
    except Exception as e:
        logging.error(f"Text-to-speech error: {str(e)}")
        return None

def get_languages():
    """Get dictionary of supported languages"""
    return {
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

def main():
    st.set_page_config(page_title="Translito", layout="wide")

    # Add custom CSS styles
    st.markdown(
        """
        <style>
            /* Main title style */
            .main-title {
                font-size: 2.5em;
                font-weight: bold;
                text-align: center;
                color: #2C3E50;
            }
            /* Subtitle style */
            .sub-title {
                font-size: 1.2em;
                text-align: center;
                color: #34495E;
            }
            /* Recording status style */
            .recording-status {
                background-color: #e74c3c;
                color: white;
                padding: 10px;
                text-align: center;
                border-radius: 5px;
                margin-bottom: 10px;
            }
            /* Sidebar instructions */
            .sidebar-instructions {
                font-size: 1em;
                line-height: 1.5;
            }
            /* Audio section styling */
            .audio-section {
                margin-top: 20px;
            }
            /* Button styles override */
            .stButton>button {
                font-weight: bold;
            }
            /* Detected language banner */
            .detected-language {
                background-color: #3498db;
                color: white;
                padding: 10px;
                text-align: center;
                border-radius: 5px;
                margin-bottom: 10px;
            }
        </style>
        """, unsafe_allow_html=True
    )

    # Sidebar with instructions and guidance
    st.sidebar.markdown("## How to Use This App")
    st.sidebar.markdown(
        """
        1. **Select Languages:** Choose the source language (your spoken language) and the target language (desired translation).
        2. **Enable Auto-Detection:** Toggle auto-detection if you want the app to identify your language automatically.
        3. **Record Your Voice:** Click on **Start Recording** and speak clearly. When done, click **Stop**.
        4. **Review & Play:** Once processed, view the transcription and translation. Use the play buttons to listen to both the original and the translated audio.
        5. **Reset if Needed:** If you want to start over, click the **Reset** button.
        """
    )
    st.sidebar.info("This application securely processes audio, transcribes the content, and translates it while enhancing terminologies. Enjoy a seamless and secure experience!")

    # Main page header
    st.markdown('<div class="main-title"><i>Translito !</i></div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Real-Time Generative AI powered Translation Web App</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>By Yashwanth M S</p>", unsafe_allow_html=True)

    languages = get_languages()
    
    # Language selection area
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        source_lang = st.selectbox("Source Language", list(languages.keys()), index=0, 
                                   disabled=st.session_state.auto_detect)
    with col2:
        target_lang = st.selectbox("Target Language", list(languages.keys()), index=1)
    with col3:
        st.session_state.auto_detect = st.checkbox("Auto-detect language", value=True)
        if st.session_state.auto_detect:
            st.caption("Speaking any language will be auto-detected")

    st.subheader("Voice Recording")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🎙️ Start Recording", 
                    type="primary" if st.session_state.recording_state != 'recording' else "secondary",
                    disabled=st.session_state.recording_state == 'recording'):
            st.session_state.recording_state = 'recording'
            st.session_state.audio_bytes = None
            st.session_state.detected_language = None
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
            st.session_state.detected_language = None
            st.rerun()

    if st.session_state.recording_state == 'recording':
        st.markdown("""<div class="recording-status" style="background-color: #ff4b4b; color: white;"> Recording in progress... 🎙️ </div>""", unsafe_allow_html=True)

        audio_bytes = ast.audio_recorder(pause_threshold=60.0, sample_rate=44100)

        if audio_bytes:
            st.session_state.audio_bytes = audio_bytes

    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/wav")

        with st.spinner("Processing audio..."):
            audio_file = secure_save_audio(st.session_state.audio_bytes)

            if audio_file:
                transcription_result = secure_transcribe_audio(audio_file)

                if transcription_result:
                    transcription = transcription_result["text"]
                    detected_lang_code = transcription_result.get("language")
                    
                    # If language not detected by Whisper, use langdetect as fallback
                    if not detected_lang_code and transcription:
                        decrypted_text = security.decrypt_text(transcription)
                        detected_lang_code = detect_language(decrypted_text)
                    
                    # Display detected language if auto-detect is enabled
                    if detected_lang_code and st.session_state.auto_detect:
                        detected_lang_name = get_language_name(detected_lang_code)
                        st.session_state.detected_language = detected_lang_name
                        st.markdown(f"""<div class="detected-language">Detected Language: {detected_lang_name}</div>""", unsafe_allow_html=True)
                        # Use the detected language for source
                        source_lang_code = languages.get(detected_lang_name) or detected_lang_code
                    else:
                        # Use the manually selected source language
                        source_lang_code = languages[source_lang]
                    
                    # Use the detected language information for enhancement
                    enhanced_text = secure_enhance_medical_terms(transcription, detected_lang_code)
                    
                    # Get target language code
                    target_lang_code = languages[target_lang]
                    
                    # Translate with explicit source language
                    translation = secure_translate_text(enhanced_text, source_lang_code, target_lang_code)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"<h3>Original Text</h3><p>{security.decrypt_text(enhanced_text)}</p>", unsafe_allow_html=True)

                        if st.button("🔊 Play Original"):
                            # Use detected language code for TTS if auto-detect is enabled
                            tts_source_lang = source_lang_code
                            audio_file = secure_text_to_speech(enhanced_text, tts_source_lang)
                            if audio_file:
                                st.audio(audio_file)
                                os.remove(audio_file)

                    with col2:
                        st.markdown(f"<h3>Translation</h3><p>{security.decrypt_text(translation)}</p>", unsafe_allow_html=True)

                        if st.button("🔊 Play Translation"):
                            audio_file = secure_text_to_speech(translation, target_lang_code)
                            if audio_file:
                                st.audio(audio_file)
                                os.remove(audio_file)

if __name__ == "__main__":
    main()
