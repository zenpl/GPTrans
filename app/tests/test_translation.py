import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.backend.services.translation import (
    MockTranslationProvider, 
    translate_paragraph,
    get_translation_provider
)
from app.shared.schemas import GlossaryTerm


class TestTranslation:
    """Test cases for translation functionality."""
    
    @pytest.fixture
    def mock_provider(self):
        return MockTranslationProvider()
    
    @pytest.fixture
    def sample_glossary(self):
        return [
            GlossaryTerm(
                id=1, glossary_id=1, 
                src="Typografie", tgt="字体排印学", 
                case_sensitive=False, notes=None
            ),
            GlossaryTerm(
                id=2, glossary_id=1,
                src="Renaissance", tgt="文艺复兴",
                case_sensitive=True, notes=None
            )
        ]
    
    @pytest.mark.asyncio
    async def test_mock_translation_basic(self, mock_provider):
        """Test basic mock translation functionality."""
        
        # Test German to Chinese
        german_text = "Die Entwicklung der modernen Typografie"
        result = await mock_provider.translate_text(
            text=german_text,
            source_lang="de",
            target_lang="zh-CN"
        )
        
        assert result != german_text  # Should be different
        assert len(result) > 0
        
        # Test Swedish to Chinese
        swedish_text = "Typografins utveckling"
        result = await mock_provider.translate_text(
            text=swedish_text,
            source_lang="sv", 
            target_lang="zh-CN"
        )
        
        assert result != swedish_text
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_translation_with_glossary(self, mock_provider, sample_glossary):
        """Test translation with glossary terms."""
        
        text = "Die Typografie in der Renaissance war wichtig"
        result = await mock_provider.translate_text(
            text=text,
            source_lang="de",
            target_lang="zh-CN",
            glossary=sample_glossary
        )
        
        # Should contain glossary translations
        assert "字体排印学" in result  # Typografie -> 字体排印学
        assert "文艺复兴" in result    # Renaissance -> 文艺复兴
    
    @pytest.mark.asyncio
    async def test_case_sensitive_glossary(self, mock_provider):
        """Test case-sensitive glossary matching."""
        
        case_sensitive_terms = [
            GlossaryTerm(
                id=1, glossary_id=1,
                src="Renaissance", tgt="文艺复兴期",
                case_sensitive=True, notes=None
            ),
            GlossaryTerm(
                id=2, glossary_id=1,
                src="renaissance", tgt="复兴",
                case_sensitive=True, notes=None
            )
        ]
        
        # Test exact case match
        text1 = "The Renaissance period"
        result1 = await mock_provider.translate_text(
            text=text1,
            source_lang="en",
            target_lang="zh-CN",
            glossary=case_sensitive_terms
        )
        assert "文艺复兴期" in result1
        
        # Test different case
        text2 = "The renaissance period"
        result2 = await mock_provider.translate_text(
            text=text2,
            source_lang="en", 
            target_lang="zh-CN",
            glossary=case_sensitive_terms
        )
        assert "复兴" in result2
    
    @pytest.mark.asyncio
    async def test_concise_translation(self, mock_provider):
        """Test concise translation mode."""
        
        long_text = "Dies ist ein sehr langer Text mit vielen Wörtern und Details" * 3
        
        # Normal translation
        normal_result = await mock_provider.translate_text(
            text=long_text,
            source_lang="de",
            target_lang="zh-CN",
            length_policy="normal"
        )
        
        # Concise translation
        concise_result = await mock_provider.translate_text(
            text=long_text,
            source_lang="de",
            target_lang="zh-CN",
            length_policy="concise"
        )
        
        # Concise should be shorter or equal
        assert len(concise_result) <= len(normal_result)
    
    @pytest.mark.asyncio
    async def test_translate_paragraph_with_markup(self):
        """Test paragraph translation preserving markup."""
        
        text_with_markup = "Die {FN:1} moderne <i>Typografie</i> ist wichtig"
        
        result = await translate_paragraph(
            text=text_with_markup,
            source_lang="de",
            target_lang="zh-CN"
        )
        
        # Should preserve placeholders and markup
        assert "{FN:1}" in result
        assert "<i>" in result and "</i>" in result
        
        # Should translate the text around markup
        assert result != text_with_markup
    
    @pytest.mark.asyncio
    async def test_translate_paragraph_empty_text(self):
        """Test translation of empty or whitespace-only text."""
        
        # Empty string
        result1 = await translate_paragraph("", "de", "zh-CN")
        assert result1 == ""
        
        # Whitespace only
        result2 = await translate_paragraph("   \n\t  ", "de", "zh-CN")
        assert result2.strip() == ""
        
        # Only markup
        result3 = await translate_paragraph("{FN:1}", "de", "zh-CN")
        assert result3 == "{FN:1}"
    
    @pytest.mark.asyncio
    async def test_complex_markup_preservation(self):
        """Test complex markup preservation."""
        
        complex_text = "Der Text hat <b>fettgedruckte {REF:2} Wörter</b> und <i>kursive</i> Teile"
        
        result = await translate_paragraph(
            text=complex_text,
            source_lang="de",
            target_lang="zh-CN"
        )
        
        # Check all markup is preserved
        assert "<b>" in result and "</b>" in result
        assert "<i>" in result and "</i>" in result
        assert "{REF:2}" in result
        
        # Check nesting is preserved
        markup_part = result[result.find("<b>"):result.find("</b>") + 4]
        assert "{REF:2}" in markup_part
    
    @pytest.mark.asyncio 
    async def test_translation_provider_factory(self):
        """Test translation provider factory."""
        
        # Test default (mock) provider
        with patch.dict('os.environ', {'TRANSLATION_PROVIDER': 'mock'}):
            provider = get_translation_provider()
            assert isinstance(provider, MockTranslationProvider)
        
        # Test OpenAI provider (falls back to mock without API key)
        with patch.dict('os.environ', {'TRANSLATION_PROVIDER': 'openai', 'OPENAI_API_KEY': ''}):
            provider = get_translation_provider()
            # Should create OpenAI provider even without API key (will fallback internally)
            assert provider is not None
    
    def test_mock_concise_logic(self, mock_provider):
        """Test the concise translation logic."""
        
        text = "这是一段很长的测试文本，需要被压缩处理，包含很多冗余的词语和短语。"
        
        # Test concise reduction
        result = mock_provider._make_concise(text, target_ratio=0.8)
        assert len(result) <= len(text)
        
        # Test with very short text (should not change much)
        short_text = "短文本"
        result_short = mock_provider._make_concise(short_text, target_ratio=0.8)
        assert result_short == short_text  # Too short to reduce
    
    @pytest.mark.asyncio
    async def test_german_translation_patterns(self, mock_provider):
        """Test German-specific translation patterns."""
        
        # Test common German words
        german_phrases = [
            "der Buchdruck",
            "die Entwicklung", 
            "das Jahrhundert",
            "und so weiter",
            "mit der Zeit"
        ]
        
        for phrase in german_phrases:
            result = await mock_provider.translate_text(
                text=phrase,
                source_lang="de",
                target_lang="zh-CN"
            )
            
            # Should produce some translation
            assert result != phrase
            assert len(result) > 0
            
            # Should contain Chinese characters for substantial phrases
            if len(phrase) > 5:
                chinese_chars = [c for c in result if ord(c) > 127]
                assert len(chinese_chars) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_provider):
        """Test error handling in translation."""
        
        # Test with invalid language codes
        try:
            result = await mock_provider.translate_text(
                text="Test text",
                source_lang="invalid",
                target_lang="zh-CN"
            )
            # Should still produce some result (fallback)
            assert result is not None
        except Exception:
            pytest.fail("Translation should handle invalid language codes gracefully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])