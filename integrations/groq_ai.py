
import logging

from django.conf import settings
from groq import Groq

logger = logging.getLogger(__name__)


# ==========================================
# SKY AWARE PH - AI SAFETY ASSISTANT
# ==========================================

SYSTEM_INSTRUCTION = """
You are SkyAware PH's AI Safety Assistant.

Help people in the Philippines prepare for:
- Earthquakes
- Typhoons
- Floods
- Landslides
- Tsunamis
- Emergency kits
- Evacuation
- Air pollution
- Extreme weather

Rules:
1. Provide practical and understandable safety advice.
2. Answer in English, Filipino, or Cebuano,
   depending on the user's language.
3. Never invent real-time disaster warnings.
4. Never claim to predict earthquakes.
5. Refer users to PAGASA, PHIVOLCS, and local
   disaster authorities for official information.
6. If someone is in immediate danger, recommend
   contacting local emergency services.
7. Explain that AI guidance does not replace
   official government emergency instructions.
8. Keep answers clear, concise, and organized.
"""


# ==========================================
# CUSTOM EXCEPTIONS
# ==========================================

class GroqConfigurationError(Exception):
    pass


class GroqServiceError(Exception):
    pass


# ==========================================
# GROQ API INTEGRATION
# ==========================================

def ask_groq(question):

    api_key = getattr(
        settings,
        "GROQ_API_KEY",
        ""
    ).strip()

    if not api_key:
        raise GroqConfigurationError(
            "Groq API key is missing."
        )

    try:
        client = Groq(
            api_key=api_key,
            timeout=30.0,
            max_retries=1
        )

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_INSTRUCTION
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            temperature=0.3,
            max_completion_tokens=700
        )

        answer = (
            response.choices[0].message.content or ""
        ).strip()

        if not answer:
            raise GroqServiceError(
                "Groq returned an empty response."
            )

        return answer

    except GroqServiceError:
        raise

    except Exception as error:
        logger.exception(
            "Groq API request failed"
        )

        raise GroqServiceError(
            "The AI service is temporarily unavailable. "
            "Please try again later."
        ) from error
