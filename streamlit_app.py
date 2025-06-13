import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import requests
import json # For handling JSON responses from API

# --- Configuration for Fonts and API ---
# IMPORTANT:
# 1. Download Google Noto Sans fonts for Telugu, Hindi, Tamil, Kannada, Malayalam, Bengali.
#    You can find them at https://fonts.google.com/noto/specimen/Noto+Sans
# 2. Create a 'fonts' directory in the same location as this Python script.
# 3. Place the downloaded .ttf font files (e.g., NotoSansTelugu-Regular.ttf) into the 'fonts' directory.
#    Ensure the filenames below match the actual filenames of your .ttf files.

FONT_DIR = "fonts"
LANGUAGE_FONTS = {
    "Telugu": "NotoSansTelugu-Regular.ttf",
    "Hindi": "NotoSansDevanagari-Regular.ttf",
    "Tamil": "NotoSansTamil-Regular.ttf",
    "Kannada": "NotoSansKannada-Regular.ttf",
    "Malayalam": "NotoSansMalayalam-Regular.ttf",
    "Bengali": "NotoSansBengali-Regular.ttf"
}

# The API key will be provided by the Canvas runtime if empty.
# In a real-world scenario outside Canvas, you would replace this with your actual Gemini API key.
GEMINI_API_KEY = "AIzaSyC5oxJPaBr2x2KnkT6PtP0etivV4trAu9o"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# --- Streamlit UI ---
st.set_page_config(page_title="Indic Infographic Generator (Streamlit)", layout="wide")
st.title("🌐 Indic Language Infographic Generator (Streamlit)")

# Selectbox for language selection
language = st.selectbox("Choose target language", list(LANGUAGE_FONTS.keys()))

# Text area for English input
input_text = st.text_area("Enter your message in English:", "Save water, save life. Protect our planet.")

# Button to trigger translation and generation
if st.button("Translate & Generate Infographic"):
    # Display a spinner while processing
    with st.spinner("Translating and generating infographic..."):
        translated_text = ""
        try:
            # Construct the prompt for the Gemini API
            prompt = f"Translate the following English text into {language}. Provide only the translated text, nothing else. Text: \"{input_text}\""

            # Prepare the API request payload
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}]
            }

            # Make the API call
            # Note: For security and proper API key handling, in a production Streamlit app
            # you might use st.secrets or environment variables for GEMINI_API_KEY.
            headers = {'Content-Type': 'application/json'}
            params = {'key': GEMINI_API_KEY} if GEMINI_API_KEY else {} # Only add key if it's not empty

            response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=payload)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

            api_result = response.json()

            # Parse the API response
            if api_result.get('candidates') and len(api_result['candidates']) > 0 and \
               api_result['candidates'][0].get('content') and \
               api_result['candidates'][0]['content'].get('parts') and \
               len(api_result['candidates'][0]['content']['parts']) > 0:
                translated_text = api_result['candidates'][0]['content']['parts'][0]['text']
            else:
                st.error("Translation failed: Unexpected response structure from API.")
                st.json(api_result) # Display full API response for debugging
                st.stop() # Stop execution if translation fails

        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {e}")
            st.stop()
        except Exception as e:
            st.error(f"An unexpected error occurred during translation: {e}")
            st.stop()

    # --- Infographic Generation using Pillow ---
    if translated_text: # Proceed only if translation was successful
        # Construct the full path to the font file
        font_file_path = os.path.join(FONT_DIR, LANGUAGE_FONTS.get(language))

        # Check if font file exists
        if not os.path.exists(font_file_path):
            st.error(f"Font for {language} not found at: {font_file_path}")
            st.warning("Please ensure the required Noto Sans font file is in the 'fonts' subfolder.")
            st.stop()

        # Load font
        try:
            font_size = 48 # Increased font size for better infographic visibility
            font = ImageFont.truetype(font_file_path, font_size)
        except IOError:
            st.error(f"Could not load font from {font_file_path}. Is the file corrupted or incorrectly named?")
            st.stop()

        # Create image
        img_width = 800
        img_height = 450
        img = Image.new('RGB', (img_width, img_height), color=(240, 248, 255)) # Light blue background
        draw = ImageDraw.Draw(img)

        # Add a simple border to the image
        border_color = (100, 100, 100) # Gray
        border_width = 3
        draw.rectangle(
            [(border_width, border_width), (img_width - border_width, img_height - border_width)],
            outline=border_color,
            width=border_width
        )

        # Function to wrap text based on canvas width
        # This is crucial for handling longer translated sentences
        def get_lines(draw_context, text, font, max_width):
            words = text.split(' ')
            lines = []
            current_line = words[0] if words else ""

            for i in range(1, len(words)):
                word = words[i]
                test_line = current_line + ' ' + word
                if draw_context.textbbox((0, 0), test_line, font=font)[2] < max_width:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line: # Add the last line
                lines.append(current_line)
            return lines

        text_max_width = img_width - 80 # Padding for text
        lines_to_draw = get_lines(draw, translated_text, font, text_max_width)
        line_height = font_size * 1.2 # 1.2 times font size for line height
        total_text_height = len(lines_to_draw) * line_height

        # Calculate starting Y position to center text vertically
        y_start = (img_height - total_text_height) / 2 + line_height / 2

        # Draw each line of text
        for i, line in enumerate(lines_to_draw):
            x = img_width / 2 # Center horizontally
            y = y_start + i * line_height
            draw.text((x, y), line, font=font, fill=(0, 0, 0), anchor="mm") # Anchor "mm" for middle-middle alignment

        # Display image in Streamlit
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        st.image(buf.getvalue(), caption=f"{language} Infographic", use_column_width=True)

        # Download button
        st.download_button(
            "Download Infographic",
            data=buf.getvalue(),
            file_name=f"{language}_infographic.png",
            mime="image/png"
        )
