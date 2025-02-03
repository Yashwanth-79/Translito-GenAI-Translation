# Translito ! Translation Web App with Generative AI

Try out here : https://translito-genai-translation.streamlit.app/

## Overview

The Translation Web App is designed to bridge language barriers in healthcare settings by utilizing generative AI technologies. This web app offers features such as real-time voice recording, transcription, translation, medical term enhancement, and text-to-speech capabilities. The app integrates state-of-the-art AI models, including **Groq**, **gTTS**, and **DeepGram**, to ensure accurate and secure healthcare translations.

## Features

- **Voice Recording**: Record real-time voice input with seamless integration.
- **Audio Transcription**: Transcribe recorded audio to text using AI-powered transcription models.
- **Medical Term Enhancement**: Enhance and correct medical terminology within the transcribed text.
- **Text Translation**: Translate the transcribed text into the selected target language using **Google Translator**.
- **Text-to-Speech (TTS)**: Convert both the original and translated texts back to speech for better accessibility.
- **Encryption & Security**: Sensitive data such as audio files and translations are encrypted to ensure privacy and security.

## Tech Stack

- **Frontend**: 
  - [Streamlit](https://streamlit.io/) for the user interface
  - Custom audio recorder component for real-time recording
  - Deep integration with audio and text components

- **Backend**: 
  - **Groq** for powerful AI model execution
  - **DeepGram SDK** for audio transcription
  - **GoogleTranslator** for text translation
  - **gTTS (Google Text-to-Speech)** for TTS conversion
  - **Cryptography (Fernet)** for data encryption

- **Security**: 
  - End-to-end encryption of sensitive data (audio, text) via **Fernet**
  - Secure temporary file storage with controlled permissions

## Installation

### Prerequisites

1. **Python 3.8+**: Make sure you have Python 3.8 or higher installed.
2. **Virtual Environment**: We recommend using a virtual environment for managing dependencies.
   - To create a virtual environment:
     ```bash
     python -m venv venv
     ```
   - To activate the virtual environment:
     - **Windows**:
       ```bash
       venv\Scripts\activate
       ```
     - **macOS/Linux**:
       ```bash
       source venv/bin/activate
       ```

### Installing Dependencies

Clone the repository and install the required packages:

```bash
git clone https://github.com/your-repository/healthcare-translation-app.git
cd healthcare-translation-app
pip install -r requirements.txt
```

Here is the entire content in Markdown (MD) format for your README:

markdown
Copy code
# Translation Web App with Generative AI

## Overview

The Translation Web App is designed to bridge language barriers in settings by utilizing generative AI technologies. This web app offers features such as real-time voice recording, transcription, translation, medical term enhancement, and text-to-speech capabilities. The app integrates state-of-the-art AI models, including **Groq**, **OpenAI**, and **DeepGram**, to ensure accurate and secure healthcare translations.

## Features

- **Voice Recording**: Record real-time voice input with seamless integration.
- **Audio Transcription**: Transcribe recorded audio to text using AI-powered transcription models.
- **Medical Term Enhancement**: Enhance and correct medical terminology within the transcribed text.
- **Text Translation**: Translate the transcribed text into the selected target language using **Google Translator**.
- **Text-to-Speech (TTS)**: Convert both the original and translated texts back to speech for better accessibility.
- **Encryption & Security**: Sensitive data such as audio files and translations are encrypted to ensure privacy and security.

## Tech Stack

- **Frontend**: 
  - [Streamlit](https://streamlit.io/) for the user interface
  - Custom audio recorder component for real-time recording
  - Deep integration with audio and text components

- **Backend**: 
  - **Groq** for powerful AI model execution
  - **DeepGram SDK** for audio transcription
  - **GoogleTranslator** for text translation
  - **gTTS (Google Text-to-Speech)** for TTS conversion
  - **Cryptography (Fernet)** for data encryption

- **Security**: 
  - End-to-end encryption of sensitive data (audio, text) via **Fernet**
  - Secure temporary file storage with controlled permissions

## Installation

### Prerequisites

1. **Python 3.8+**: Make sure you have Python 3.8 or higher installed.
2. **Virtual Environment**: We recommend using a virtual environment for managing dependencies.
   - To create a virtual environment:
     ```bash
     python -m venv venv
     ```
   - To activate the virtual environment:
     - **Windows**:
       ```bash
       venv\Scripts\activate
       ```
     - **macOS/Linux**:
       ```bash
       source venv/bin/activate
       ```

### Installing Dependencies

Clone the repository and install the required packages:

```bash
git clone https://github.com/your-repository/healthcare-translation-app.git
cd healthcare-translation-app
pip install -r requirements.txt
Configuration
Environment Variables: Make sure to set up the .env file with necessary keys.
ENCRYPTION_KEY: If not provided, one will be generated automatically.
api_key: API key for Groq model access.
Example .env file:

dotenv
Copy code
ENCRYPTION_KEY=your-encryption-key
api_key=your-groq-api-key
Usage
Running the App
To start the web app, simply run:

streamlit run app.py
This will open the web application in your default browser.
```
## How the App Works:

Recording:
Users can click the "Start Recording" button to record their voice. The app captures and processes the audio.

Audio Processing:
After recording, the audio is transcribed to text using Groq and DeepGram SDK.

Medical Term Enhancement:

The transcribed text is passed through the AI model for enhancement and correction of medical terms.

Translation:
The enhanced text is then translated into the selected target language using Google Translator.

Text-to-Speech:
Users can play back both the original and translated text using the integrated gTTS feature.

Secure Storage:
All sensitive data is encrypted and stored securely.

Audio File Formats:
The app supports audio input in WAV format, which is automatically processed for transcription.

Supported Languages:
The app currently supports translation between a wide range of languages, including:

English, Spanish, French, German, Italian, Portuguese, Chinese (Simplified & Traditional), Japanese, Korean, Hindi, Arabic, Russian, and more.
Security Features

Data Encryption:
All sensitive data, including recorded audio and transcriptions, is encrypted using Fernet encryption to ensure privacy.

Secure File Storage:
Audio files are stored in temporary secure locations with restricted access.

Authentication & Authorization:
Basic authentication mechanisms ensure only authorized users can access and process sensitive data.
