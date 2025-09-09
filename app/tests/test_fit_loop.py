import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.shared.utils.fit_loop import FitLoop, FitResult, MockMeasureFunc
from app.shared.schemas import FitLoopConfig, TypesetFrame


class TestFitLoop:
    """Test cases for the automatic fit loop functionality."""
    
    @pytest.fixture
    def fit_loop(self):
        config = FitLoopConfig(
            initial_line_height=1.5,
            min_line_height=1.4,
            max_line_height=1.7,
            initial_letter_spacing=0.0,
            min_letter_spacing=-0.02,
            max_letter_spacing=0.01
        )
        return FitLoop(config)
    
    @pytest.fixture
    def test_frame(self):
        return TypesetFrame(
            block_id=1,
            x=100, y=100,
            width=200, height=100,
            content="测试内容"
        )
    
    @pytest.fixture
    def mock_measure_func(self):
        return MockMeasureFunc(char_width=16, char_height=24)
    
    @pytest.mark.asyncio
    async def test_fit_loop_success(self, fit_loop, test_frame, mock_measure_func):
        """Test successful text fitting within frame."""
        
        # Short text should fit easily
        short_content = "测试"
        
        result = await fit_loop.fit_text_to_frame(
            frame=test_frame,
            content=short_content,
            measure_func=mock_measure_func
        )
        
        assert result.fits is True
        assert result.iterations >= 1
        assert result.final_content == short_content
        assert "line-height" in result.css_properties
    
    @pytest.mark.asyncio
    async def test_fit_loop_overflow_compression(self, fit_loop, test_frame, mock_measure_func):
        """Test compression when text overflows."""
        
        # Long text that should require compression
        long_content = "这是一段很长的测试内容，用来测试自动拟合算法" * 5
        
        result = await fit_loop.fit_text_to_frame(
            frame=test_frame,
            content=long_content,
            measure_func=mock_measure_func
        )
        
        assert result.iterations > 1
        assert float(result.css_properties["line-height"]) <= fit_loop.config.initial_line_height
        assert result.overflow_ratio > 0
    
    @pytest.mark.asyncio
    async def test_fit_loop_with_concise_translation(self, fit_loop, test_frame, mock_measure_func):
        """Test fit loop with concise translation fallback."""
        
        async def mock_concise_translate(text: str) -> str:
            # Simulate shortening text by 20%
            return text[:int(len(text) * 0.8)]
        
        long_content = "这是一段很长的测试内容，需要压缩翻译" * 10
        
        result = await fit_loop.fit_text_to_frame(
            frame=test_frame,
            content=long_content,
            measure_func=mock_measure_func,
            translate_concise_func=mock_concise_translate
        )
        
        # Should have tried concise translation
        assert len(result.final_content) <= len(long_content)
    
    @pytest.mark.asyncio
    async def test_css_compression_steps(self, fit_loop):
        """Test individual CSS compression steps."""
        
        css_props = {
            "line-height": "1.5",
            "letter-spacing": "0em",
            "font-weight": "normal",
            "font-stretch": "normal"
        }
        
        # Test letter spacing compression
        success = await fit_loop._compress_text(css_props, 0)
        assert success is True
        assert float(css_props["letter-spacing"].rstrip("em")) < 0
        
        # Test line height compression
        success = await fit_loop._compress_text(css_props, 1)
        assert success is True
        assert float(css_props["line-height"]) < 1.5
        
        # Test font stretch compression
        success = await fit_loop._compress_text(css_props, 2)
        assert success is True
        assert css_props["font-stretch"] == "condensed"
    
    @pytest.mark.asyncio
    async def test_css_expansion_steps(self, fit_loop):
        """Test CSS expansion for sparse text."""
        
        css_props = {
            "line-height": "1.5",
            "letter-spacing": "0em"
        }
        
        # Test line height expansion
        result_props = await fit_loop._expand_text(css_props, 0)
        assert float(result_props["line-height"]) > 1.5
        
        # Test letter spacing expansion
        result_props = await fit_loop._expand_text(css_props, 1)
        assert float(result_props["letter-spacing"].rstrip("em")) > 0
    
    def test_mock_measure_func(self):
        """Test mock measurement function."""
        
        measure_func = MockMeasureFunc(char_width=16, char_height=24)
        
        # Test with single line
        result = asyncio.run(measure_func("测试", {"line-height": "1.5"}))
        width, height = result
        
        assert width > 0
        assert height > 0
        
        # Test with multiple lines
        result = asyncio.run(measure_func("测试\n内容", {"line-height": "1.5"}))
        width, height = result
        
        assert height > 24  # Should be taller than single line
    
    @pytest.mark.asyncio
    async def test_fit_loop_edge_cases(self, fit_loop, mock_measure_func):
        """Test edge cases and error conditions."""
        
        # Empty frame
        empty_frame = TypesetFrame(
            block_id=1,
            x=0, y=0,
            width=0, height=0,
            content=""
        )
        
        result = await fit_loop.fit_text_to_frame(
            frame=empty_frame,
            content="测试",
            measure_func=mock_measure_func
        )
        
        # Should handle gracefully
        assert result is not None
        
        # Empty content
        normal_frame = TypesetFrame(
            block_id=1,
            x=0, y=0,
            width=100, height=100,
            content=""
        )
        
        result = await fit_loop.fit_text_to_frame(
            frame=normal_frame,
            content="",
            measure_func=mock_measure_func
        )
        
        assert result.final_content == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])