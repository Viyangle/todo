import os

try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - dependency is optional at runtime
    ChatOpenAI = None
    HumanMessage = None
    SystemMessage = None


class TarotInterpreter:
    def __init__(self) -> None:
        self._max_chars = 100
        self._model = self._create_model()

    def _create_model(self):
        if ChatOpenAI is None:
            return None

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return None

        base_url = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        model_name = os.getenv("OPENAI_MODEL_NAME", "qwen-max")
        temperature = float(os.getenv("TAROT_MODEL_TEMPERATURE", "0.6"))

        return ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            model=model_name,
            temperature=temperature,
            max_tokens=120,
            timeout=20,
        )

    def build_summary(self, question: str, cards: list[dict[str, str]]) -> str:
        if not cards:
            return "No cards."

        if self._model is None or HumanMessage is None or SystemMessage is None:
            return self._fallback_summary(cards)

        system_prompt = (
            "You are a tarot interpreter. "
            "Read the three cards as one coherent message. "
            "Reply in 1-2 short sentences, with no bullets, title, or disclaimer. "
            "Keep it concise and action-oriented."
        )
        user_prompt = (
            f"Question: {question or 'Not provided'}\n"
            f"Spread: {self._format_cards(cards)}\n"
            "Provide a short integrated interpretation with a practical next step."
        )

        try:
            response = self._model.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            )
        except Exception:
            return self._fallback_summary(cards)

        text = self._extract_text(response)
        if not text:
            return self._fallback_summary(cards)
        return self._trim_text(text)

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

    def _fallback_summary(self, cards: list[dict[str, str]]) -> str:
        present = cards[1].get("meaning", "") if len(cards) > 1 else ""
        future = cards[2].get("meaning", "") if len(cards) > 2 else ""
        base = f"Current focus: {present} Next trend: {future}"
        return self._trim_text(base)
