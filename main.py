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
import datetime

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
if 'language_error' not in st.session_state:
    st.session_state.language_error = False
if 'error_message' not in st.session_state:
    st.session_state.error_message = ""
# Initialize conversation history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Language code mapping (reverse mapping from language code to language name)
def get_lang_code_mapping():
    # Create reverse mapping
    reverse_lang_map = {}
    for lang, code in languages.items():
        reverse_lang_map[code] = lang
    return reverse_lang_map

# Language detection to ISO code mapping
lang_detect_to_iso = {
    'en': 'en', 'es': 'es', 'fr': 'fr', 'de': 'de', 'it': 'it', 'pt': 'pt',
    'zh-cn': 'zh-CN', 'zh-tw': 'zh-TW', 'ja': 'ja', 'ko': 'ko', 'hi': 'hi',
    'ar': 'ar', 'ru': 'ru', 'bn': 'bn', 'id': 'id', 'tr': 'tr', 'vi': 'vi',
    'nl': 'nl', 'el': 'el', 'he': 'he', 'sv': 'sv', 'no': 'no', 'da': 'da',
    'pl': 'pl', 'cs': 'cs', 'hu': 'hu', 'fi': 'fi', 'th': 'th', 'fil': 'fil',
    'ms': 'ms', 'ur': 'ur', 'ta': 'ta', 'te': 'te', 'mr': 'mr', 'pa': 'pa',
    'gu': 'gu', 'uk': 'uk', 'ro': 'ro', 'bg': 'bg', 'sr': 'sr', 'hr': 'hr',
    'sk': 'sk', 'sl': 'sl', 'lt': 'lt', 'lv': 'lv', 'et': 'et', 'is': 'is',
    'af': 'af', 'sq': 'sq', 'am': 'am', 'hy': 'hy', 'az': 'az', 'eu': 'eu',
    'be': 'be', 'bs': 'bs', 'ca': 'ca', 'ceb': 'ceb', 'co': 'co', 'eo': 'eo',
    'fy': 'fy', 'gl': 'gl', 'ka': 'ka', 'ht': 'ht', 'ha': 'ha', 'haw': 'haw',
    'hmn': 'hmn', 'is': 'is', 'ig': 'ig', 'ga': 'ga', 'jw': 'jw', 'kn': 'kn',
    'kk': 'kk', 'km': 'km', 'rw': 'rw', 'ku': 'ku', 'ky': 'ky', 'lo': 'lo',
    'la': 'la', 'lb': 'lb', 'mk': 'mk', 'mg': 'mg', 'ml': 'ml', 'mt': 'mt',
    'mi': 'mi', 'mn': 'mn', 'my': 'my', 'ne': 'ne', 'ny': 'ny', 'or': 'or',
    'ps': 'ps', 'fa': 'fa', 'sm': 'sm', 'gd': 'gd', 'st': 'st', 'sn': 'sn',
    'sd': 'sd', 'si': 'si', 'so': 'so', 'su': 'su', 'sw': 'sw', 'tl': 'tl',
    'tg': 'tg', 'tt': 'tt', 'tk': 'tk', 'ug': 'ug', 'uz': 'uz', 'cy': 'cy',
    'xh': 'xh', 'yi': 'yi', 'yo': 'yo', 'zu': 'zu'
}

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

def secure_transcribe_audio(audio_file, expected_lang_code):
    """Transcribe audio with encryption and language validation"""
    try:
        with open(audio_file, "rb") as file:
            # Instruct Whisper to focus on the expected language
            transcription = client.audio.transcriptions.create(
                file=(audio_file, file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
                language=expected_lang_code  # Tell Whisper which language to expect
            )
            
            # Get the transcribed text
            transcribed_text = transcription.text
            
            # Verify the language of the transcribed text
            try:
                detected_lang = detect(transcribed_text)
                
                # Map detected language to ISO code for comparison
                detected_iso = lang_detect_to_iso.get(detected_lang, detected_lang)
                expected_iso = expected_lang_code
                
                # Normalize codes for comparison (some languages have different formats)
                if detected_iso.lower() != expected_iso.lower() and detected_iso.split('-')[0] != expected_iso.split('-')[0]:
                    reverse_lang_map = get_lang_code_mapping()
                    st.session_state.language_error = True
                    st.session_state.error_message = f"Language mismatch detected. You selected {reverse_lang_map.get(expected_iso, expected_iso)} but spoke in {reverse_lang_map.get(detected_iso, detected_iso)}."
                    return None
                
                # Reset error state if no error
                st.session_state.language_error = False
                st.session_state.error_message = ""
                
            except LangDetectException:
                # If language detection fails, proceed with caution but don't block
                logging.warning("Language detection failed, proceeding with transcription")
            
            # Encrypt the transcribed text
            return security.encrypt_text(transcribed_text)
    except Exception as e:
        logging.error(f"Transcription error: {str(e)}")
        st.session_state.language_error = True
        st.session_state.error_message = f"Error during transcription: {str(e)}"
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
                "content": "You are a translation and transcription expert. Correct and enhance any terminology in the following text while preserving the original meaning. just translate what input you receive."
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

# Global language dictionary
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

def save_to_history(source_lang, target_lang, original_text, translated_text):
    """Save the current translation to history"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history_entry = {
        "timestamp": timestamp,
        "source_language": source_lang,
        "target_language": target_lang,
        "original_text": original_text,
        "translated_text": translated_text
    }
    st.session_state.conversation_history.append(history_entry)
    
    # Keep only the last 50 entries to prevent memory issues
    if len(st.session_state.conversation_history) > 50:
        st.session_state.conversation_history = st.session_state.conversation_history[-50:]

def display_conversation_history():
    """Display the conversation history"""
    if not st.session_state.conversation_history:
        st.info("No conversation history yet. Start translating to build your history!")
        return
    
    st.subheader("Conversation History")
    
    # Add download button for history
    if st.download_button(
        label="Download History as CSV",
        data=generate_history_csv(),
        file_name="translito_history.csv",
        mime="text/csv"
    ):
        st.success("History downloaded successfully!")
    
    # Add clear history button
    if st.button("Clear History"):
        st.session_state.conversation_history = []
        st.success("History cleared successfully!")
        st.rerun()
    
    # Display history in an expandable format
    for i, entry in enumerate(reversed(st.session_state.conversation_history)):
        with st.expander(f"#{len(st.session_state.conversation_history)-i}: {entry['timestamp']} - {entry['source_language']} to {entry['target_language']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Original ({entry['source_language']}):**")
                st.markdown(f"<div style='background-color:#f0f0f0; padding:10px; border-radius:5px;'>{entry['original_text']}</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"**Translation ({entry['target_language']}):**")
                st.markdown(f"<div style='background-color:#f0f0f0; padding:10px; border-radius:5px;'>{entry['translated_text']}</div>", unsafe_allow_html=True)

def generate_history_csv():
    """Generate CSV data from conversation history"""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Timestamp', 'Source Language', 'Target Language', 'Original Text', 'Translated Text'])
    
    # Write data
    for entry in st.session_state.conversation_history:
        writer.writerow([
            entry['timestamp'],
            entry['source_language'],
            entry['target_language'],
            entry['original_text'],
            entry['translated_text']
        ])
    
    return output.getvalue()

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
            /* Error message style */
            .error-message {
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
            /* History entry */
            .history-entry {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 10px;
            }
            /* Tabs styling */
            .stTabs [data-baseweb="tab-list"] {
                gap: 24px;
            }
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                white-space: pre-wrap;
                background-color: white;
                border-radius: 4px 4px 0px 0px;
                gap: 1px;
                padding-top: 10px;
                padding-bottom: 10px;
            }
            .stTabs [aria-selected="true"] {
                background-color: #f0f2f6;
                border-bottom: 2px solid #4e89e8;
            }
        </style>
        """, unsafe_allow_html=True
    )

    # Sidebar with instructions and guidance
    st.sidebar.markdown("## How to Use This App")
    st.sidebar.markdown(
        """
        1. **Select Languages:** Choose the source language (your spoken language) and the target language (desired translation).
        2. **Record Your Voice:** Click on **Start Recording** and speak clearly in the selected source language. When done, click **Stop**.
        3. **Review & Play:** Once processed, view the transcription and translation. Use the play buttons to listen to both the original and the translated audio.
        4. **History:** View your conversation history in the History tab. You can download it as a CSV file.
        5. **Reset if Needed:** If you want to start over, click the **Reset** button.
        
        **Important Note:** You must speak in the language you selected as the source language. The app will verify this and alert you if there's a mismatch.
        """
    )
    st.sidebar.info("This application securely processes audio, transcribes the content, and translates it while enhancing terminologies. Enjoy a seamless and secure experience!")

    # Main page header
    st.markdown('<div class="main-title"><i>Translito !</i></div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Real-Time Generative AI powered Translation Web App</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>By Yashwanth M S</p>", unsafe_allow_html=True)

    # Create tabs for Translation and History
    tab1, tab2 = st.tabs(["Translation", "History"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            source_lang = st.selectbox("Source Language ", list(languages.keys()), index=0)
        with col2:
            target_lang = st.selectbox("Target Language", list(languages.keys()), index=1)

        # Display language guidance
        st.info(f"Please make sure to speak in {source_lang} for accurate transcription and translation.")

        st.subheader("Voice Recording")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🎙️ Start Recording", 
                        type="primary" if st.session_state.recording_state != 'recording' else "secondary",
                        disabled=st.session_state.recording_state == 'recording'):
                st.session_state.recording_state = 'recording'
                st.session_state.audio_bytes = None
                st.session_state.language_error = False
                st.session_state.error_message = ""
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
                st.session_state.language_error = False
                st.session_state.error_message = ""
                st.rerun()

        if st.session_state.recording_state == 'recording':
            st.markdown("""<div class="recording-status" style="background-color: #ff4b4b; color: white;"> Recording in progress... 🎙️ </div>""", unsafe_allow_html=True)

            audio_bytes = ast.audio_recorder(pause_threshold=60.0, sample_rate=44100)

            if audio_bytes:
                st.session_state.audio_bytes = audio_bytes

        # Display language error if detected
        if st.session_state.language_error and st.session_state.error_message:
            st.markdown(f"""<div class="error-message">{st.session_state.error_message}</div>""", unsafe_allow_html=True)

        if st.session_state.audio_bytes:
            st.audio(st.session_state.audio_bytes, format="audio/wav")

            with st.spinner("Processing audio..."):
                audio_file = secure_save_audio(st.session_state.audio_bytes)

                if audio_file:
                    # Use the selected source language code for transcription
                    source_lang_code = languages[source_lang]
                    transcription = secure_transcribe_audio(audio_file, source_lang_code)

                    # Only proceed if there's no language mismatch error
                    if transcription and not st.session_state.language_error:
                        enhanced_text = secure_enhance_medical_terms(transcription)
                        translation = secure_translate_text(enhanced_text, languages[target_lang])

                        # Get decrypted texts for display
                        original_decrypted = security.decrypt_text(enhanced_text)
                        translation_decrypted = security.decrypt_text(translation)

                        # Save to history
                        save_to_history(source_lang, target_lang, original_decrypted, translation_decrypted)

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"<h3>Original Text ({source_lang})</h3><p>{original_decrypted}</p>", unsafe_allow_html=True)

                            if st.button("🔊 Play Original"):
                                audio_file = secure_text_to_speech(enhanced_text, languages[source_lang])
                                if audio_file:
                                    st.audio(audio_file)
                                    os.remove(audio_file)

                        with col2:
                            st.markdown(f"<h3>Translation ({target_lang})</h3><p>{translation_decrypted}</p>", unsafe_allow_html=True)

                            if st.button("🔊 Play Translation"):
                                audio_file = secure_text_to_speech(translation, languages[target_lang])
                                if audio_file:
                                    st.audio(audio_file)
                                    os.remove(audio_file)
                    elif not st.session_state.language_error:
                        st.error("Failed to transcribe audio. Please try again.")
    
    with tab2:
        # Display conversation history
        display_conversation_history()

if __name__ == "__main__":
    main()
