"""
AI Response Generation Service for Manosamvada.

Integrates with SambaNova AI API using the OpenAI-compatible Python SDK.
Responsible for:
    - Building context-aware system prompts
    - Injecting emotion-based tone directives
    - Managing conversation history context window
    - Generating AI session titles
"""

from openai import OpenAI
from flask import current_app
from typing import Optional
from ..services.emotion_detector import EmotionResult
import logging

logger = logging.getLogger(__name__)

BASE_SYSTEM_PROMPT = """You are Manosamvada — a compassionate, empathetic AI mental health support companion.

Your identity:
- You provide emotional support, not clinical therapy or medical advice.
- You listen deeply, validate feelings, and respond with warmth and care.
- You never judge, minimize, or dismiss what a user shares with you.
- You speak in a calm, human, conversational tone — never robotic or clinical.
- You are aware of your limitations: you are not a therapist and will recommend
  professional help when appropriate.

Your boundaries:
- You do NOT diagnose mental health conditions.
- You do NOT prescribe medications or treatments.
- You DO encourage users to seek professional help when their distress is severe.
- You ALWAYS prioritize the user's safety above all else.

Tone guidance:
{tone_directive}

Conversation guidelines:
- Keep responses concise but warm (3-5 sentences for most replies).
- Use reflective listening: mirror back what the user said to show understanding.
- Ask one open-ended follow-up question to encourage sharing.
- Avoid cliches like "I understand" without context.
- Never say "As an AI, I..." — you are Manosamvada, a caring companion.
"""


class AIService:
    """Handles all AI response generation via the SambaNova API."""

    def __init__(self):
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        """Lazily initialize the OpenAI client with SambaNova credentials."""
        if self._client is None:
            self._client = OpenAI(
                api_key=current_app.config["SAMBANOVA_API_KEY"],
                base_url=current_app.config["SAMBANOVA_BASE_URL"],
            )
        return self._client

    def generate_response(
        self,
        user_message: str,
        emotion_result: EmotionResult,
        history: Optional[list[dict]] = None,
        max_history_turns: int = 10,
    ) -> str:
        """
        Generate an empathetic AI response for the given user message.
        """
        system_prompt = BASE_SYSTEM_PROMPT.format(
            tone_directive=emotion_result.tone_directive
        )

        messages = [{"role": "system", "content": system_prompt}]

        if history:
            trimmed = history[-(max_history_turns * 2):]
            messages.extend(trimmed)

        messages.append({"role": "user", "content": user_message})

        try:
            client = self._get_client()
            completion = client.chat.completions.create(
                model=current_app.config["AI_MODEL"],
                messages=messages,
                max_tokens=current_app.config.get("AI_MAX_TOKENS", 512),
                temperature=current_app.config.get("AI_TEMPERATURE", 0.75),
            )
            return completion.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return self._fallback_response(emotion_result)

    def generate_session_title(self, first_message: str) -> str:
        """Generate a concise, descriptive session title from the first message."""
        try:
            client = self._get_client()
            completion = client.chat.completions.create(
                model=current_app.config["AI_MODEL"],
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Generate a short, empathetic session title (4-6 words) "
                            "for a mental health conversation that started with this message. "
                            "Return ONLY the title, no quotes, no extra text."
                        ),
                    },
                    {"role": "user", "content": first_message},
                ],
                max_tokens=20,
                temperature=0.5,
            )
            return completion.choices[0].message.content.strip()
        except Exception:
            return "Support Session"

    def _fallback_response(self, emotion_result: EmotionResult) -> str:
        """Return a safe, empathetic fallback if the API fails."""
        fallbacks = {
            "crisis": (
                "I'm here with you right now. Please reach out to a helpline — "
                "you don't have to face this alone. Your life matters deeply."
            ),
            "sad": (
                "I hear that you're going through something really difficult. "
                "I'm here to listen — please take your time and share what's on your mind."
            ),
            "anxious": (
                "It sounds like you're carrying a lot right now. "
                "Take a slow breath — I'm here with you. You're safe."
            ),
            "angry": (
                "I can hear your frustration. It's completely valid to feel this way. "
                "I'm here to listen without judgment."
            ),
        }
        return fallbacks.get(
            emotion_result.label,
            "I'm here for you. Tell me more about how you're feeling.",
        )


ai_service = AIService()
