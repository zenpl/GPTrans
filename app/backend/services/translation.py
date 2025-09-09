import os
import re
import asyncio
from typing import Dict, List, Optional
from abc import ABC, abstractmethod

from app.shared.schemas import GlossaryTerm


class TranslationProvider(ABC):
    """Abstract base class for translation providers."""
    
    @abstractmethod
    async def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        glossary: Optional[List[GlossaryTerm]] = None,
        length_policy: str = "normal"
    ) -> str:
        """Translate text from source to target language."""
        pass


class MockTranslationProvider(TranslationProvider):
    """Mock translation provider for testing and development."""
    
    def __init__(self):
        # Sample translations for common German/Swedish phrases
        self.translations = {
            "de": {
                "Die Entwicklung der modernen Typografie": "现代字体设计的发展",
                "Die Geschichte der Typografie": "字体排印史",
                "Johannes Gutenberg": "约翰内斯·古腾堡",
                "beweglichen Lettern": "活字印刷",
                "Renaissance": "文艺复兴",
                "humanistische Minuskel": "人文主义小写字母",
                "Gutenberg-Bible": "古腾堡圣经",
                "Mainz": "美因茨"
            },
            "sv": {
                "Typografins utveckling": "字体设计的发展",
                "Modern design": "现代设计",
                "Tryckkonst": "印刷艺术"
            }
        }
    
    async def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        glossary: Optional[List[GlossaryTerm]] = None,
        length_policy: str = "normal"
    ) -> str:
        """Mock translation with basic word substitution and length control."""
        await asyncio.sleep(0.2)  # Simulate API call
        
        translated = text
        
        # Apply glossary terms first
        if glossary:
            for term in glossary:
                if term.case_sensitive:
                    translated = translated.replace(term.src, term.tgt)
                else:
                    pattern = re.compile(re.escape(term.src), re.IGNORECASE)
                    translated = pattern.sub(term.tgt, translated)
        
        # Apply built-in translations
        if source_lang in self.translations:
            for src, tgt in self.translations[source_lang].items():
                if src.lower() in translated.lower():
                    pattern = re.compile(re.escape(src), re.IGNORECASE)
                    translated = pattern.sub(tgt, translated)
        
        # Basic German to Chinese translation logic
        if source_lang == "de" and target_lang == "zh-CN":
            translated = self._mock_german_to_chinese(translated)
        elif source_lang == "sv" and target_lang == "zh-CN":
            translated = self._mock_swedish_to_chinese(translated)
        
        # Apply length policy
        if length_policy == "concise":
            translated = self._make_concise(translated, target_ratio=0.9)
        
        return translated
    
    def _mock_german_to_chinese(self, text: str) -> str:
        """Mock German to Chinese translation."""
        # Simple word-by-word substitution for common patterns
        patterns = {
            r'\bder\b': '这个',
            r'\bdie\b': '这个',  
            r'\bdas\b': '这个',
            r'\bund\b': '和',
            r'\bin\b': '在',
            r'\bmit\b': '用',
            r'\bvon\b': '来自',
            r'\bzu\b': '到',
            r'\bist\b': '是',
            r'\bwird\b': '被',
            r'\bwurde\b': '被',
            r'\bsich\b': '',
            r'ung\b': '化',
            r'tion\b': '动',
            r'ität\b': '性',
        }
        
        result = text
        for pattern, replacement in patterns.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        # Clean up multiple spaces
        result = re.sub(r'\s+', '', result)
        
        # If no translation occurred, provide a generic Chinese text
        if result == text or len([c for c in result if ord(c) > 127]) < 3:
            result = f"这是一段从德语翻译过来的文本：{text[:20]}..."
        
        return result
    
    def _mock_swedish_to_chinese(self, text: str) -> str:
        """Mock Swedish to Chinese translation."""
        patterns = {
            r'\ben\b': '一个',
            r'\bett\b': '一个',
            r'\boch\b': '和',
            r'\bi\b': '在',
            r'\bav\b': '的',
            r'\bför\b': '为了',
            r'\bsom\b': '如',
            r'\bär\b': '是',
        }
        
        result = text
        for pattern, replacement in patterns.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        result = re.sub(r'\s+', '', result)
        
        if result == text or len([c for c in result if ord(c) > 127]) < 3:
            result = f"这是一段从瑞典语翻译过来的文本：{text[:20]}..."
        
        return result
    
    def _make_concise(self, text: str, target_ratio: float = 0.9) -> str:
        """Make translation more concise by removing redundant words."""
        if len(text) <= 10:
            return text
        
        target_length = int(len(text) * target_ratio)
        
        # Simple strategy: remove common filler words and redundant phrases
        concise_patterns = [
            r'，这个',
            r'的这个',
            r'，它',
            r'，该',
            r'，其',
            r'所谓的',
            r'也就是说',
            r'换句话说',
        ]
        
        result = text
        for pattern in concise_patterns:
            if len(result) > target_length:
                result = re.sub(pattern, '', result)
        
        # If still too long, truncate sentences
        if len(result) > target_length:
            sentences = result.split('。')
            while len('。'.join(sentences)) > target_length and len(sentences) > 1:
                sentences.pop()
            result = '。'.join(sentences)
            if not result.endswith('。') and sentences:
                result += '。'
        
        return result or text  # Fallback to original if empty


class OpenAITranslationProvider(TranslationProvider):
    """OpenAI GPT-based translation provider."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        
    async def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        glossary: Optional[List[GlossaryTerm]] = None,
        length_policy: str = "normal"
    ) -> str:
        """Translate using OpenAI API."""
        if not self.api_key:
            # Fall back to mock if no API key
            mock_provider = MockTranslationProvider()
            return await mock_provider.translate_text(
                text, source_lang, target_lang, glossary, length_policy
            )
        
        # TODO: Implement actual OpenAI API call
        # For now, fall back to mock
        mock_provider = MockTranslationProvider()
        return await mock_provider.translate_text(
            text, source_lang, target_lang, glossary, length_policy
        )


def get_translation_provider() -> TranslationProvider:
    """Get configured translation provider."""
    provider_type = os.getenv("TRANSLATION_PROVIDER", "mock")
    
    if provider_type == "openai":
        return OpenAITranslationProvider()
    else:
        return MockTranslationProvider()


async def translate_paragraph(
    text: str,
    source_lang: str,
    target_lang: str,
    glossary: Optional[List[GlossaryTerm]] = None,
    length_policy: str = "normal"
) -> str:
    """
    Translate a paragraph while preserving placeholders and markup.
    
    Args:
        text: Source text to translate
        source_lang: Source language code (de, sv)
        target_lang: Target language code (zh-CN)
        glossary: Optional glossary terms
        length_policy: "normal" or "concise"
        
    Returns:
        Translated text with preserved markup
    """
    if not text.strip():
        return text
    
    # Extract and preserve placeholders and markup
    placeholders = {}
    placeholder_pattern = r'(\{[^}]+\}|<[^>]+>[^<]*</[^>]+>|<[^/>]+/>)'
    
    def replace_placeholder(match):
        key = f"__PLACEHOLDER_{len(placeholders)}__"
        placeholders[key] = match.group(1)
        return key
    
    # Replace placeholders with keys
    text_for_translation = re.sub(placeholder_pattern, replace_placeholder, text)
    
    # Translate the text
    provider = get_translation_provider()
    translated = await provider.translate_text(
        text_for_translation, source_lang, target_lang, glossary, length_policy
    )
    
    # Restore placeholders
    for key, value in placeholders.items():
        translated = translated.replace(key, value)
    
    return translated