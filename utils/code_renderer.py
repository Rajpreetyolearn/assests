#!/usr/bin/env python3
"""
Source Code Rendering Utility

This utility uses Pygments to create syntax-highlighted HTML 
from source code and Playwright to render it as a PNG image.
"""

from playwright.async_api import async_playwright
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from fastapi import HTTPException

async def render_code_to_image(
    code: str, 
    language: str, 
    style: str = "default",
    show_line_numbers: bool = True
) -> bytes:
    """
    Renders source code to a PNG image with syntax highlighting.

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
            lexer = get_lexer_by_name(language)
        except Exception:
            # If the language is not found, try to guess it
            lexer = guess_lexer(code)

        # Create an HTML formatter with specified style and line numbers
        formatter = HtmlFormatter(
            style=style, 
            linenos=show_line_numbers, 
            full=True,
            cssclass="codehilite"
        )
        
        # Generate the HTML
        highlighted_code = highlight(code, lexer, formatter)
        
        # Launch Playwright to render the HTML
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Set the HTML content
            await page.set_content(highlighted_code)
            
            # Find the code element and take a screenshot
            element = await page.query_selector(".codehilite")
            if not element:
                raise Exception("Could not find highlighted code element.")

            # Add some padding around the code
            await page.evaluate("""
                const element = document.querySelector('.codehilite');
                if (element) {
                    element.style.padding = '20px';
                    element.style.borderRadius = '5px';
                }
            """)

            image_bytes = await element.screenshot(type="png")
            await browser.close()
            
            return image_bytes

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to render code to image: {str(e)}"
        ) 