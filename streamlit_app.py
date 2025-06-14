import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import requests
import json

# --- Configuration for Fonts and APIs ---
FONT_DIR = "fonts"
LANGUAGE_FONTS = {
    "Telugu": "NotoSansTelugu-Regular.ttf",
    "Hindi": "NotoSansDevanagari-Regular.ttf",
    "Tamil": "NotoSansTamil-Regular.ttf",
    "Kannada": "NotoSansKannada-Regular.ttf",
    "Malayalam": "NotoSansMalayalam-Regular.ttf",
    "Bengali": "NotoSansBengali-Regular.ttf",
    "English": "NotoSans-Regular.ttf" # Added for a generic fallback font if needed
}

# Your Gemini API Key
# IMPORTANT: In a real app, use st.secrets["GEMINI_API_KEY"]
GEMINI_API_KEY = "AIzaSyC5oxJPaBr2x2KnkT6PtP0etivV4trAu9o" # Replace with your actual Gemini Key if different
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Your DeepAI API Key
# IMPORTANT: In a real app, use st.secrets["DEEPAI_API_KEY"]
DEEPAI_API_KEY = "616a18ce-d4c9-442d-b115-e253492844b2"
DEEPAI_IMAGE_API_URL = "https://api.deepai.org/api/text2img"

# --- Helper function for text wrapping ---
def get_lines(draw_context, text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        test_line = (current_line + ' ' + word).strip()
        # Calculate text width using textbbox
        bbox = draw_context.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width < max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

# --- Function to generate image using DeepAI ---
def generate_image_with_deepai(prompt, api_key):
    headers = {
        "api-key": api_key
    }
    payload = {
        "text": prompt,
        # You can add other parameters supported by DeepAI's text2img model
        # For example, 'grid_size': '1x1' or 'width', 'height' if supported by the model
    }
    try:
        st.info(f"Sending image generation request to DeepAI for: '{prompt[:50]}...'") # Show brief prompt
        response = requests.post(DEEPAAI_IMAGE_API_URL, data=payload, headers=headers)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        api_response = response.json()
        
        if 'output_url' in api_response:
            image_url = api_response['output_url']
            st.info(f"DeepAI image URL received: {image_url}")
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            return Image.open(io.BytesIO(image_response.content))
        else:
            st.error(f"DeepAI response did not contain 'output_url'. Response: {api_response}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"DeepAI API request failed: {e}. Check API key and DeepAI usage limits.")
        if response and hasattr(response, 'text'):
            st.error(f"DeepAI API raw error: {response.text}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during DeepAI image generation: {e}")
        return None

# --- Streamlit UI ---
st.set_page_config(page_title="Indic Story Infographic Generator", layout="wide")
st.title("📚 Indic Language Story Infographic Generator")

language = st.selectbox("Choose target language", list(LANGUAGE_FONTS.keys()))
input_text = st.text_area("Enter your message in English:", "Save water, save life. Protect our planet. Every drop counts for a sustainable future.")

if st.button("Generate Story Infographic"):
    if not GEMINI_API_KEY or not DEEPAI_API_KEY:
        st.error("Please provide valid API keys for Gemini and DeepAI.")
        st.stop()

    with st.spinner("Breaking down story, translating, and generating images..."):
        story_points_data = []
        try:
            # Phase 1: Get Story Breakdown from Gemini
            gemini_story_prompt = f"""
            Given the English message: '{input_text}', create a short, 3-5 point visual story for an infographic.
            For each point, provide:
            1. A concise English sentence summarizing the point.
            2. A detailed visual description (image prompt) for an AI image generator to illustrate this point. The prompt should be creative and describe a scene or concept clearly, suitable for a general image model. Avoid mentioning specific artists or proprietary styles.
            3. The translation of the concise English sentence into {language}.

            Format your response as a JSON array of objects, where each object has 'english_summary', 'image_prompt', and 'translated_text' keys.
            Example for 'Save water, save life.':
            [
              {{
                "english_summary": "Water is essential for life.",
                "image_prompt": "A close-up of a single glistening water droplet falling onto a vibrant green leaf in bright daylight, symbolizing life and nature's vitality.",
                "translated_text": "నీరు జీవితానికి అవసరం."
              }},
              {{
                "english_summary": "Conserve water daily.",
                "image_prompt": "A person's hands gently turning off a faucet that was dripping, with a healthy, potted plant thriving nearby, illustrating responsible water conservation in a home setting.",
                "translated_text": "నీటిని రోజూ సంరక్షించండి."
              }},
              {{
                "english_summary": "Protect our planet for future.",
                "image_prompt": "A stylized, serene image of the Earth being cradled gently by a pair of diverse human hands, surrounded by lush, healthy ecosystems and a clear, hopeful sky, emphasizing global protection.",
                "translated_text": "భవిష్యత్ కోసం మన గ్రహాన్ని రక్షించండి."
              }}
            ]
            """
            gemini_payload = {
                "contents": [{"role": "user", "parts": [{"text": gemini_story_prompt}]}]
            }
            gemini_headers = {'Content-Type': 'application/json'}
            gemini_params = {'key': GEMINI_API_KEY} if GEMINI_API_KEY else {}

            gemini_response = requests.post(GEMINI_API_URL, headers=gemini_headers, params=gemini_params, json=gemini_payload)
            gemini_response.raise_for_status()
            gemini_api_result = gemini_response.json()

            raw_json_string = "" # Initialize raw_json_string
            if gemini_api_result.get('candidates') and len(gemini_api_result['candidates']) > 0:
                response_content = gemini_api_result['candidates'][0].get('content')
                if response_content and response_content.get('parts'):
                    raw_json_string = response_content['parts'][0]['text']
                    # Clean up any markdown or extra text before parsing JSON
                    if raw_json_string.startswith("```json"):
                        raw_json_string = raw_json_string[7:]
                    if raw_json_string.endswith("```"):
                        raw_json_string = raw_json_string[:-3]
                    story_points_data = json.loads(raw_json_string.strip())
                else:
                    st.error("Gemini response format error: 'parts' not found.")
                    st.json(gemini_api_result)
                    st.stop()
            else:
                st.error("Gemini response error: No candidates found.")
                st.json(gemini_api_result)
                st.stop()

        except requests.exceptions.RequestException as e:
            st.error(f"Gemini API request failed: {e}")
            st.stop()
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse Gemini's JSON response. Error: {e}. Raw response: ```{raw_json_string}```")
            st.stop()
        except Exception as e:
            st.error(f"An unexpected error occurred during story breakdown: {e}")
            st.stop()

        if not story_points_data:
            st.warning("No story points generated by Gemini. Please try again with a different message.")
            st.stop()

        # Phase 2 & 3: Generate Images and Assemble Infographic
        generated_images_and_texts = [] # Store both image and its text
        for i, point in enumerate(story_points_data):
            st.markdown(f"**Generating image for point {i+1}:** _{point['image_prompt']}_")
            img = generate_image_with_deepai(point['image_prompt'], DEEPAI_API_KEY)
            if img:
                generated_images_and_texts.append({'image': img, 'translated_text': point['translated_text']})
            else:
                st.warning(f"Skipping image for point {i+1} due to generation failure. Using a placeholder.")
                # Fallback: Use a blank image or skip
                # Attempt to load a default font for fallback text, or use Pillow's built-in font
                try:
                    default_font_path = os.path.join(FONT_DIR, LANGUAGE_FONTS.get("English"))
                    if not os.path.exists(default_font_path):
                        default_font = ImageFont.load_default()
                    else:
                        default_font = ImageFont.truetype(default_font_path, 20)
                except Exception:
                    default_font = ImageFont.load_default()

                blank_img = Image.new('RGB', (500, 300), color=(200, 200, 200))
                draw_blank = ImageDraw.Draw(blank_img)
                draw_blank.text((blank_img.width/2, blank_img.height/2), "Image Failed", fill=(0,0,0), anchor="mm", font=default_font)
                generated_images_and_texts.append({'image': blank_img, 'translated_text': point['translated_text']})


        if not generated_images_and_texts:
            st.error("No images were successfully generated for the infographic.")
            st.stop()

        # --- Infographic Assembly (Multi-Panel Vertical Layout) ---
        panel_width = 700 # Consistent width for each panel
        image_display_height = 300 # Height for the generated image within each panel
        text_area_height = 100 # Estimated height for text below image

        # Load font for text
        font_file_path = os.path.join(FONT_DIR, LANGUAGE_FONTS.get(language))
        if not os.path.exists(font_file_path):
            st.error(f"Font for {language} not found at: {font_file_path}")
            st.warning("Please ensure the required Noto Sans font file is in the 'fonts' subfolder.")
            st.stop()
        text_font_size = 36 # Smaller font for multiple lines
        try:
            text_font = ImageFont.truetype(font_file_path, text_font_size)
        except IOError:
            st.error(f"Could not load font from {font_file_path}. Is the file corrupted or incorrectly named?")
            st.stop()

        # Calculate total infographic height
        panel_vertical_padding = 40 # Padding above and below image/text within a panel
        panel_spacing = 30 # Space between panels
        
        # Each panel includes image height, text area height, and internal padding
        # Let's adjust for vertical centering of text.
        
        # Calculate the actual required height for each text block
        max_text_height_per_panel = 0
        for item in generated_images_and_texts:
            lines = get_lines(ImageDraw.Draw(Image.new('RGB', (1,1))), item['translated_text'], text_font, panel_width - 40)
            max_text_height_per_panel = max(max_text_height_per_panel, len(lines) * (text_font_size * 1.2))
        
        # Adjust panel_total_height to accommodate the maximum text height needed across all panels
        # This makes sure no text gets cut off if one panel has more lines
        panel_content_height = image_display_height + max_text_height_per_panel + panel_vertical_padding * 2
        
        total_infographic_height = len(generated_images_and_texts) * panel_content_height + \
                                   (len(generated_images_and_texts) - 1) * panel_spacing + \
                                   60 # Overall top/bottom padding for the whole infographic

        # Create the main infographic image
        main_img = Image.new('RGB', (panel_width + 60, int(total_infographic_height)), color=(255, 255, 255)) # White background
        main_draw = ImageDraw.Draw(main_img)

        current_y_offset = 30 # Initial vertical offset for the first panel

        for i, panel_content in enumerate(generated_images_and_texts):
            panel_top_y = current_y_offset
            panel_bottom_y = current_y_offset + panel_content_height - panel_vertical_padding # Approx bottom of the actual content area, before padding for next panel

            # Draw panel background (light blue) and border
            main_draw.rectangle(
                [(30, panel_top_y), (panel_width + 30, panel_top_y + panel_content_height - panel_vertical_padding)],
                fill=(240, 248, 255), # Light blue for panel background
                outline=(150, 150, 150),
                width=2
            )

            # Resize image to fit panel display height and paste
            img_to_paste = panel_content['image']
            # Maintain aspect ratio while fitting into image_display_height
            aspect_ratio = img_to_paste.width / img_to_paste.height
            new_width = int(image_display_height * aspect_ratio)
            resized_img = img_to_paste.resize((min(new_width, panel_width - 40), image_display_height - 40), Image.Resampling.LANCZOS)
            
            # Center image horizontally within the panel's content area
            image_x_pos = 30 + (panel_width - resized_img.width) // 2
            image_y_pos = current_y_offset + 20 # 20px top padding within panel

            main_img.paste(resized_img, (image_x_pos, image_y_pos))

            # Draw translated text below the image
            translated_text = panel_content['translated_text']
            lines_to_draw = get_lines(main_draw, translated_text, text_font, panel_width - 40)
            line_height = text_font_size * 1.2

            text_block_height = len(lines_to_draw) * line_height
            
            # Calculate starting Y for text, centered vertically in its remaining space
            text_area_start_y = image_y_pos + resized_img.height + 10 # 10px padding between image and text
            
            # Ensure text is somewhat centered in the remaining height available for text
            text_y_start_for_lines = text_area_start_y + (max_text_height_per_panel - text_block_height) / 2
            
            text_x_pos = (panel_width // 2) + 30 # Centered horizontally within the panel

            for j, line in enumerate(lines_to_draw):
                main_draw.text((text_x_pos, text_y_start_for_lines + j * line_height), line,
                               font=text_font, fill=(0, 0, 0), anchor="mm")

            current_y_offset += panel_content_height + panel_spacing # Move to the next panel's starting Y

        # Display and Download
        buf = io.BytesIO()
        main_img.save(buf, format="PNG")
        st.image(buf.getvalue(), caption=f"{language} Story Infographic", use_column_width=True)

        st.download_button(
            "Download Story Infographic",
            data=buf.getvalue(),
            file_name=f"{language}_story_infographic.png",
            mime="image/png"
        )
