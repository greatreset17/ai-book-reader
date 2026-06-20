"""
gemini_client.py - Gemini API クライアント
プライマリ: gemini-3.5-flash / フォールバック: gemini-2.5-flash
"""
import logging
from typing import Optional

from google import genai
from google.genai import types

from .prompts import (
    TRANSLATE_PROMPT,
    MERMAID_PROMPT,
    SUMMARIZE_PROMPT,
    CHAT_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

PRIMARY_MODEL = "gemini-3.5-flash"
FALLBACK_MODEL = "gemini-2.5-flash"


class GeminiClient:
    """Gemini APIクライアント（フォールバック付き）"""

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.current_model = PRIMARY_MODEL

    def _generate(
        self,
        prompt: str,
        *,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Gemini APIでテキストを生成。プライマリモデルで失敗したらフォールバック。
        """
        config = types.GenerateContentConfig(
            temperature=temperature,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        models_to_try = [PRIMARY_MODEL, FALLBACK_MODEL]

        for model_name in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                self.current_model = model_name
                return response.text or ""
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}")
                if model_name == FALLBACK_MODEL:
                    raise RuntimeError(
                        f"Both models failed. Last error: {e}"
                    ) from e
                continue

        raise RuntimeError("All models failed")

    def translate(self, text: str) -> str:
        """テキストを現代日本語に翻訳"""
        prompt = TRANSLATE_PROMPT.format(text=text)
        return self._generate(prompt, temperature=0.3)

    def generate_mermaid(self, text: str) -> str:
        """テキストからMermaid構造図コードを生成"""
        prompt = MERMAID_PROMPT.format(text=text)
        raw = self._generate(prompt, temperature=0.4)
        # Clean up: remove markdown fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```mermaid"):
            cleaned = cleaned[len("```mermaid") :].strip()
        if cleaned.startswith("```"):
            cleaned = cleaned[3:].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
        return cleaned

    def summarize(self, text: str) -> str:
        """現代の視点からの要約・応用を生成"""
        prompt = SUMMARIZE_PROMPT.format(text=text)
        return self._generate(prompt, temperature=0.5)

    def chat(self, user_message: str, context: str, history: list[dict]) -> str:
        """チャット対話（コンテキスト付き）"""
        system = CHAT_SYSTEM_PROMPT.format(context=context)

        # Build conversation as a single prompt with history
        conversation_parts = []
        for msg in history:
            role = "ユーザー" if msg["role"] == "user" else "AI"
            conversation_parts.append(f"{role}: {msg['content']}")
        conversation_parts.append(f"ユーザー: {user_message}")
        conversation_parts.append("AI:")

        full_prompt = "\n\n".join(conversation_parts)

        return self._generate(
            full_prompt,
            system_instruction=system,
            temperature=0.7,
        )
