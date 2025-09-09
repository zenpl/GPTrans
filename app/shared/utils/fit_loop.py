import asyncio
import logging
from typing import Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from app.shared.schemas import FitLoopConfig, TypesetFrame

logger = logging.getLogger(__name__)


@dataclass
class FitResult:
    """Result of a fit loop iteration."""
    fits: bool
    overflow_ratio: float
    density_ratio: float
    css_properties: Dict[str, str]
    iterations: int
    final_content: str


class FitLoop:
    """Auto-fitting algorithm for Chinese text within containers."""
    
    def __init__(self, config: FitLoopConfig = None):
        self.config = config or FitLoopConfig()
        
    async def fit_text_to_frame(
        self,
        frame: TypesetFrame,
        content: str,
        measure_func: Callable[[str, Dict[str, str]], Tuple[float, float]],
        translate_concise_func: Optional[Callable[[str], str]] = None
    ) -> FitResult:
        """
        Fit text content to frame using progressive adjustments.
        
        Args:
            frame: Target frame with dimensions
            content: Text content to fit
            measure_func: Function to measure text dimensions given content and CSS
            translate_concise_func: Optional function to generate more concise translation
            
        Returns:
            FitResult with final fitting state
        """
        original_content = content
        current_content = content
        
        # Initialize CSS properties
        css_props = {
            "line-height": str(self.config.initial_line_height),
            "letter-spacing": f"{self.config.initial_letter_spacing}em",
            "font-weight": "normal",
            "font-stretch": "normal"
        }
        
        for iteration in range(10):  # FIT_LOOP_MAX_ITERATIONS
            # Measure current text
            text_width, text_height = await measure_func(current_content, css_props)
            
            # Calculate ratios
            overflow_ratio = text_height / frame.height if frame.height > 0 else 0
            density_ratio = text_width / frame.width if frame.width > 0 else 0
            
            logger.debug(f"Iteration {iteration}: overflow={overflow_ratio:.3f}, density={density_ratio:.3f}")
            
            # Check if we fit within tolerance
            if overflow_ratio <= (1.0 + self.config.overflow_tolerance):
                # Check if density is reasonable (not too sparse)
                if density_ratio >= 0.4:  # Minimum density threshold
                    return FitResult(
                        fits=True,
                        overflow_ratio=overflow_ratio,
                        density_ratio=density_ratio,
                        css_properties=css_props,
                        iterations=iteration + 1,
                        final_content=current_content
                    )
                else:
                    # Text is too sparse, try to expand it
                    css_props = await self._expand_text(css_props, iteration)
                    continue
            
            # Text doesn't fit, try to compress it
            success = await self._compress_text(css_props, iteration)
            if not success:
                # Compression failed, try concise translation
                if translate_concise_func and iteration < 3:  # Only try concise early
                    logger.info("Attempting concise translation")
                    try:
                        concise_content = await translate_concise_func(original_content)
                        if len(concise_content) < len(current_content):
                            current_content = concise_content
                            # Reset CSS to defaults for new content
                            css_props = {
                                "line-height": str(self.config.initial_line_height),
                                "letter-spacing": f"{self.config.initial_letter_spacing}em",
                                "font-weight": "normal",
                                "font-stretch": "normal"
                            }
                            continue
                    except Exception as e:
                        logger.warning(f"Concise translation failed: {e}")
                
                # Last resort: allow slight overflow
                logger.warning(f"Could not fit text after {iteration + 1} iterations, allowing overflow")
                break
        
        # Final measurement
        text_width, text_height = await measure_func(current_content, css_props)
        overflow_ratio = text_height / frame.height if frame.height > 0 else 0
        density_ratio = text_width / frame.width if frame.width > 0 else 0
        
        return FitResult(
            fits=overflow_ratio <= 1.1,  # Allow 10% overflow as final fallback
            overflow_ratio=overflow_ratio,
            density_ratio=density_ratio,
            css_properties=css_props,
            iterations=10,  # FIT_LOOP_MAX_ITERATIONS
            final_content=current_content
        )
    
    async def _compress_text(self, css_props: Dict[str, str], iteration: int) -> bool:
        """Apply compression techniques progressively."""
        
        if iteration == 0:
            # Step 1: Reduce letter spacing
            current_spacing = float(css_props["letter-spacing"].rstrip("em"))
            if current_spacing > self.config.min_letter_spacing:
                new_spacing = max(self.config.min_letter_spacing, current_spacing - 0.01)
                css_props["letter-spacing"] = f"{new_spacing}em"
                return True
        
        elif iteration == 1:
            # Step 2: Reduce line height
            current_height = float(css_props["line-height"])
            if current_height > self.config.min_line_height:
                new_height = max(self.config.min_line_height, current_height - 0.05)
                css_props["line-height"] = str(new_height)
                return True
        
        elif iteration == 2:
            # Step 3: Use condensed font if available
            if css_props.get("font-stretch", "normal") == "normal":
                css_props["font-stretch"] = "condensed"
                return True
        
        elif iteration == 3:
            # Step 4: Use lighter font weight
            if css_props.get("font-weight", "normal") == "normal":
                css_props["font-weight"] = "300"
                return True
        
        return False
    
    async def _expand_text(self, css_props: Dict[str, str], iteration: int) -> Dict[str, str]:
        """Apply expansion techniques for sparse text."""
        
        if iteration == 0:
            # Step A: Increase line height
            current_height = float(css_props["line-height"])
            if current_height < self.config.max_line_height:
                new_height = min(self.config.max_line_height, current_height + 0.1)
                css_props["line-height"] = str(new_height)
        
        elif iteration == 1:
            # Step B: Increase letter spacing
            current_spacing = float(css_props["letter-spacing"].rstrip("em"))
            if current_spacing < self.config.max_letter_spacing:
                new_spacing = min(self.config.max_letter_spacing, current_spacing + 0.005)
                css_props["letter-spacing"] = f"{new_spacing}em"
        
        return css_props


class MockMeasureFunc:
    """Mock text measurement function for testing."""
    
    def __init__(self, char_width: float = 16, char_height: float = 24):
        self.char_width = char_width
        self.char_height = char_height
    
    async def __call__(self, content: str, css_props: Dict[str, str]) -> Tuple[float, float]:
        """Estimate text dimensions based on character count."""
        await asyncio.sleep(0.001)  # Simulate async measurement
        
        lines = content.split('\n')
        max_line_length = max(len(line) for line in lines) if lines else 0
        
        # Apply CSS property effects
        line_height = float(css_props.get("line-height", "1.5"))
        letter_spacing_em = float(css_props.get("letter-spacing", "0").rstrip("em"))
        
        # Calculate dimensions
        width = max_line_length * self.char_width * (1 + letter_spacing_em)
        height = len(lines) * self.char_height * line_height
        
        # Apply font-stretch effects
        if css_props.get("font-stretch") == "condensed":
            width *= 0.85
        
        return width, height


# Example usage and testing functions
async def test_fit_loop():
    """Test the fit loop with mock data."""
    config = FitLoopConfig()
    fit_loop = FitLoop(config)
    
    # Create a test frame (200x100 pixels)
    frame = TypesetFrame(
        block_id=1,
        x=0, y=0,
        width=200, height=100,
        content=""
    )
    
    # Test content that should overflow
    long_content = "这是一段很长的中文文本，用来测试自动拟合算法的效果。" * 5
    
    # Mock measure function
    measure_func = MockMeasureFunc()
    
    # Mock concise translation function
    async def mock_concise_translate(text: str) -> str:
        # Simulate reducing text by 10%
        return text[:int(len(text) * 0.9)]
    
    result = await fit_loop.fit_text_to_frame(
        frame=frame,
        content=long_content,
        measure_func=measure_func,
        translate_concise_func=mock_concise_translate
    )
    
    print(f"Fit result: fits={result.fits}, iterations={result.iterations}")
    print(f"Overflow ratio: {result.overflow_ratio:.3f}")
    print(f"Final CSS: {result.css_properties}")
    
    return result


if __name__ == "__main__":
    asyncio.run(test_fit_loop())