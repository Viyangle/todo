import os
from dataclasses import dataclass


@dataclass
class TarotAIConfig:
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model_name: str = "qwen-max"
    temperature: float = 0.6

try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - dependency is optional at runtime
    ChatOpenAI = None
    HumanMessage = None
    SystemMessage = None


class TarotInterpreter:
    def __init__(self, config: TarotAIConfig | None = None) -> None:
        self._max_chars = 100
        self._config = config or self._load_config_from_env()
        self._model = self._create_model(self._config)

    def _load_config_from_env(self) -> TarotAIConfig:
        temperature_raw = os.getenv("TAROT_MODEL_TEMPERATURE", "0.6")
        try:
            temperature = float(temperature_raw)
        except ValueError:
            temperature = 0.6
        return TarotAIConfig(
            api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            base_url=os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1").strip(),
            model_name=os.getenv("OPENAI_MODEL_NAME", "qwen-max").strip(),
            temperature=temperature,
        )

    def set_config(self, config: TarotAIConfig) -> None:
        self._config = config
        self._model = self._create_model(config)

    def has_ai_config(self) -> bool:
        return bool(self._config.api_key.strip())

    def _create_model(self, config: TarotAIConfig):
        if ChatOpenAI is None:
            return None

        api_key = config.api_key.strip()
        if not api_key:
            return None

        return ChatOpenAI(
            base_url=config.base_url.strip() or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=api_key,
            model=config.model_name.strip() or "qwen-max",
            temperature=config.temperature,
            max_tokens=120,
            timeout=20,
        )

    def build_summary(
        self,
        question: str,
        cards: list[dict[str, str]],
        spread_type: str = "past_present_future",
    ) -> str:
        if not cards:
            return "No cards."

        if self._model is None or HumanMessage is None or SystemMessage is None:
            return self._fallback_summary(cards, question, spread_type)

        system_prompt = (
            "You are a tarot interpreter. "
            f"Read the {self._describe_spread(spread_type, len(cards))} as one coherent message. "
            "Reply in 1-2 short sentences, with no bullets, title, or disclaimer. "
            "Keep it concise and action-oriented."
        )
        user_prompt = (
            f"Question: {question or 'Not provided'}\n"
            f"Spread Type: {spread_type}\n"
            f"Spread: {self._format_cards(cards)}\n"
            "Provide a short integrated interpretation with a practical next step."
        )

        try:
            response = self._invoke(self._model, system_prompt, user_prompt)
        except Exception:
            return self._fallback_summary(cards, question, spread_type)

        text = self._extract_text(response)
        if not text:
            return self._fallback_summary(cards, question, spread_type)
        return self._trim_text(text)

    def test_connection(self, config: TarotAIConfig | None = None) -> str:
        active_config = config or self._config
        if ChatOpenAI is None or HumanMessage is None or SystemMessage is None:
            raise RuntimeError("AI dependencies are unavailable.")
        if not active_config.api_key.strip():
            raise RuntimeError("API Key is empty.")

        model = self._create_model(active_config)
        if model is None:
            raise RuntimeError("Unable to create AI client.")

        response = self._invoke(
            model,
            "You are a concise assistant.",
            "Reply with exactly: connection ok",
        )
        text = self._extract_text(response)
        if not text:
            raise RuntimeError("AI service returned an empty response.")
        return self._trim_text(text)

    def _invoke(self, model, system_prompt: str, user_prompt: str):
        return model.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )

    def _format_cards(self, cards: list[dict[str, str]]) -> str:
        rows = []
        for card in cards:
            rows.append(
                f"{card.get('position', '-')}: {card.get('name', '-')}, "
                f"{card.get('orientation', '-')}, "
                f"keywords={card.get('keywords', '-')}, "
                f"meaning={card.get('meaning', '-')}"
            )
        return " | ".join(rows)

    def _extract_text(self, response) -> str:
        content = getattr(response, "content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            chunks: list[str] = []
            for block in content:
                if isinstance(block, str):
                    chunks.append(block)
                    continue
                if isinstance(block, dict):
                    maybe_text = block.get("text")
                    if isinstance(maybe_text, str):
                        chunks.append(maybe_text)
            return "".join(chunks).strip()
        return str(content).strip()

    def _trim_text(self, text: str) -> str:
        compact = " ".join(text.split())
        if len(compact) <= self._max_chars:
            return compact
        return compact[: self._max_chars - 3].rstrip() + "..."

    def _describe_spread(self, spread_type: str, card_count: int) -> str:
        labels = {
            "single_card": "single-card draw",
            "past_present_future": "past / present / future spread",
            "celtic_cross": "Celtic Cross spread",
        }
        return labels.get(spread_type, f"{card_count}-card spread")

    def _fallback_summary(
        self,
        cards: list[dict[str, str]],
        question: str,
        spread_type: str,
    ) -> str:
        card_bits = []
        for card in cards:
            position = card.get("position", "Card")
            meaning = card.get("meaning", "").strip()
            if meaning:
                card_bits.append(f"{position}: {meaning}")

        if not card_bits:
            return "No interpretation available."

        focus = f"Question: {question}. " if question else ""
        base = (
            f"{focus}{self._describe_spread(spread_type, len(cards)).capitalize()}: "
            + " ".join(card_bits)
        )
        return self._trim_text(base)
