#!/usr/bin/env python3
"""
Source Code Rendering Utility

This utility uses Pygments to create syntax-highlighted HTML 
from source code and Playwright to render it as a PNG image.
"""

from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from fastapi import HTTPException
from PIL import Image
import io

async def render_code_to_image(
    code: str, 
    language: str, 
    style: str = "default",
    show_line_numbers: bool = True
) -> bytes:
    """
    Renders source code to a PNG image with syntax highlighting using Pygments and Pillow.

    Args:
        code: The source code to render.
        language: The programming language of the code.
        style: The Pygments style to use for highlighting.
        show_line_numbers: Whether to include line numbers in the output.

    Returns:
        The rendered PNG image as bytes.
    """
    try:
        # Get the lexer for the specified language
        try:
            lexer = get_lexer_by_name(language, stripall=True)
        except Exception:
            # If the language is not found, try to guess it
            lexer = guess_lexer(code, stripall=True)

        # Create an Image formatter with specified style and line numbers
        formatter = ImageFormatter(
            style=style, 
            linenos=show_line_numbers,
            font_name='Courier New',
            font_size=24,
            image_pad=20,
        )
        
        # Generate the image bytes
        image_bytes = highlight(code, lexer, formatter)
        
        # Add padding and a border using Pillow
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Add padding
            padded_img = Image.new(
                "RGB", 
                (img.width + 40, img.height + 40), 
                color=formatter.style.background_color
            )
            padded_img.paste(img, (20, 20))
            
            # Save to a bytes buffer to return
            output_buffer = io.BytesIO()
            padded_img.save(output_buffer, format="PNG")
            return output_buffer.getvalue()

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to render code to image: {str(e)}"
        ) 