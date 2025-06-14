import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import requests
import json
import base64 # For decoding base64 image data

# --- Configuration for Fonts and APIs ---
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
GEMINI_API_KEY = "" # Will be injected by Canvas runtime if empty.
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
IMAGEN_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict"

# --- Streamlit UI ---
st.set_page_config(page_title="Indic Infographic Generator (Streamlit)", layout="wide")
st.title("🌐 Indic Language Infographic Generator (Streamlit)")

# Input for text translation
st.subheader("1. Text Translation & Infographic Content")
language = st.selectbox("Choose target language for text:", list(LANGUAGE_FONTS.keys()), key="lang_select_text")
input_text = st.text_area("Enter your message in English for translation:", "Save water, save life. Protect our planet.", key="input_text_area")

st.markdown("---") # Separator for clarity

# Input for image generation
st.subheader("2. Background Image Generation (Optional)")
enable_image_gen = st.checkbox("Enable Image Generation for Background", value=False)

image_prompt = ""
if enable_image_gen:
    image_prompt = st.text_input("Describe the background image you want:", "A vibrant, peaceful natural landscape with a clear sky.", key="image_prompt_input")
    st.info("The generated image will be used as the background for your infographic.")

# Button to trigger translation and generation
if st.button("Generate Infographic"):
    st.session_state.translated_text = ""
    st.session_state.generated_image = None
    
    # Display a spinner while processing
    with st.spinner("Processing..."):
        # --- Step 1: Translate Text ---
        translated_text = ""
        try:
            translation_prompt = f"Translate the following English text into {language}. Provide only the translated text, nothing else. Text: \"{input_text}\""
            payload = {"contents": [{"role": "user", "parts": [{"text": translation_prompt}]}]}
            
            headers = {'Content-Type': 'application/json'}
            params = {'key': GEMINI_API_KEY} if GEMINI_API_KEY else {}

            response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=payload)
            response.raise_for_status()

            api_result = response.json()
            if api_result.get('candidates') and len(api_result['candidates']) > 0 and \
               api_result['candidates'][0].get('content') and \
               api_result['candidates'][0]['content'].get('parts') and \
               len(api_result['candidates'][0]['content']['parts']) > 0:
                translated_text = api_result['candidates'][0]['content'].get('parts')[0].get('text', '')
                if not translated_text:
                    st.error("Translation returned empty text. Please try a different input.")
                    st.stop()
            else:
                st.error("Translation failed: Unexpected response structure from Gemini API.")
                st.json(api_result)
                st.stop()

            st.session_state.translated_text = translated_text

        except requests.exceptions.RequestException as e:
            st.error(f"Translation API request failed: {e}. Check your internet connection or API key.")
            st.stop()
        except Exception as e:
            st.error(f"An unexpected error occurred during translation: {e}")
            st.stop()

        # --- Step 2: Generate Image (if enabled) ---
        generated_image = None
        if enable_image_gen and image_prompt:
            try:
                st.write("Generating background image...")
                image_payload = {
                    "instances": {"prompt": image_prompt},
                    "parameters": {"sampleCount": 1}
                }

                # IMPORTANT: For imagen-3.0-generate-002, the API key needs to be in the URL for 'predict'
                # If GEMINI_API_KEY is empty, Canvas will inject it.
                image_api_url_with_key = f"{IMAGEN_API_URL}?key={GEMINI_API_KEY}" if GEMINI_API_KEY else IMAGEN_API_URL

                image_response = requests.post(image_api_url_with_key, headers=headers, json=image_payload)
                image_response.raise_for_status()
                image_result = image_response.json()

                if image_result.get('predictions') and len(image_result['predictions']) > 0 and \
                   image_result['predictions'][0].get('bytesBase64Encoded'):
                    base64_image = image_result['predictions'][0]['bytesBase64Encoded']
                    image_bytes = base64.b64decode(base64_image)
                    generated_image = Image.open(io.BytesIO(image_bytes)).convert("RGB") # Ensure RGB mode
                    st.session_state.generated_image = generated_image
                else:
                    st.warning("Image generation failed or returned no image.")
                    st.json(image_result)

            except requests.exceptions.RequestException as e:
                st.warning(f"Image generation API request failed: {e}. Skipping image background.")
            except Exception as e:
                st.warning(f"An unexpected error occurred during image generation: {e}. Skipping image background.")

    # --- Step 3: Generate Infographic using Pillow ---
    if translated_text: # Proceed only if translation was successful
        # Construct the full path to the font file
        font_file_path = os.path.join(FONT_DIR, LANGUAGE_FONTS.get(language))

        # Check if font file exists
        if not os.path.exists(font_file_path):
            st.error(f"Font for {language} not found at: `{font_file_path}`")
            st.warning("Please ensure the required Noto Sans font file is in the 'fonts' subfolder and the filename matches exactly (e.g., NotoSansTelugu-Regular.ttf).")
            st.stop()

        # Load font
        try:
            font_size = 48 # Increased font size for better infographic visibility
            font = ImageFont.truetype(font_file_path, font_size)
        except IOError:
            st.error(f"Could not load font from {font_file_path}. Is the file corrupted or incorrectly named?")
            st.stop()

        img_width = 800
        img_height = 450

        # Use generated image as background or create a new plain image
        if generated_image:
            # Resize generated image to fit infographic dimensions
            img = generated_image.resize((img_width, img_height), Image.LANCZOS)
        else:
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
        def get_lines(draw_context, text, font, max_width):
            words = text.split(' ')
            lines = []
            current_line = ""
            for word in words:
                test_line = (current_line + ' ' + word).strip()
                bbox = draw_context.textbbox((0, 0), test_line, font=font)
                text_width = bbox[2] - bbox[0]
                
                if text_width < max_width:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            return lines

        text_max_width = img_width - 80 # Padding for text
        lines_to_draw = get_lines(draw, translated_text, font, text_max_width)
        line_height = font.getbbox("Tg")[3] * 1.5
        total_text_height = len(lines_to_draw) * line_height

        y_start = (img_height - total_text_height) / 2 + (line_height / 2)

        # Draw each line of text
        for i, line in enumerate(lines_to_draw):
            x = img_width / 2
            y = y_start + i * line_height
            
            # Add a subtle text background for better readability over complex images
            text_bbox_current_line = draw.textbbox((x,y), line, font=font, anchor="mm")
            padding = 10 # Padding around text for background
            bg_rect = (text_bbox_current_line[0] - padding, text_bbox_current_line[1] - padding, 
                       text_bbox_current_line[2] + padding, text_bbox_current_line[3] + padding)
            
            draw.rectangle(bg_rect, fill=(255, 255, 255, 180)) # Semi-transparent white background
            draw.text((x, y), line, font=font, fill=(0, 0, 0), anchor="mm")

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
