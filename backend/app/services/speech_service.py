"""
Speech Service - Handles Speech-to-Text (Deepgram Nova-3) and Text-to-Speech (OpenAI)
"""

import os
import base64
from typing import Optional
from openai import OpenAI
from deepgram import DeepgramClient
from dotenv import load_dotenv

load_dotenv()


class SpeechService:
    """Service for speech recognition and synthesis"""

    def __init__(self):
        # Deepgram for STT (Nova-3)
        deepgram_key = os.getenv("DEEPGRAM_API_KEY")
        self.deepgram = DeepgramClient(api_key=deepgram_key) if deepgram_key else None

        # OpenAI for TTS
        openai_key = os.getenv("OPENAI_API_KEY")
        self.openai = OpenAI(api_key=openai_key) if openai_key else None
        self.tts_model = "tts-1"
        self.tts_voice = "nova"

        if not self.deepgram:
            print("⚠️ Deepgram API key not set - speech-to-text disabled")
        if not self.openai:
            print("⚠️ OpenAI API key not set - text-to-speech disabled")

    async def transcribe(
        self,
        audio_data: bytes,
        filename: Optional[str] = None
    ) -> str:
        """
        Transcribe audio to text using Deepgram Nova-3

        Args:
            audio_data: Raw audio bytes
            filename: Original filename (used to determine mimetype)

        Returns:
            Transcribed text
        """
        if not self.deepgram:
            raise Exception("Deepgram API key not configured - speech-to-text unavailable")

        try:
            response = self.deepgram.listen.v1.media.transcribe_file(
                request=audio_data,
                model="nova-3",
                smart_format=True,
                language="en",
            )
            transcript = response.results.channels[0].alternatives[0].transcript

            return transcript.strip()

        except Exception as e:
            print(f"Transcription error: {e}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> str:
        """
        Convert text to speech using OpenAI TTS

        Args:
            text: Text to convert to speech
            voice: Voice to use (optional, defaults to nova)

        Returns:
            Base64 encoded MP3 audio
        """
        if not self.openai:
            raise Exception("OpenAI API key not configured - text-to-speech unavailable")

        try:
            response = self.openai.audio.speech.create(
                model=self.tts_model,
                voice=voice or self.tts_voice,
                input=text,
                response_format="mp3"
            )

            audio_base64 = base64.b64encode(response.content).decode('utf-8')
            return audio_base64

        except Exception as e:
            print(f"TTS error: {e}")
            raise Exception(f"Failed to synthesize speech: {str(e)}")

    async def transcribe_stream(self, audio_chunk: bytes) -> Optional[str]:
        return await self.transcribe(audio_chunk)

    def set_voice(self, voice: str):
        valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if voice in valid_voices:
            self.tts_voice = voice
        else:
            raise ValueError(f"Invalid voice. Choose from: {valid_voices}")
