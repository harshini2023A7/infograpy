import streamlit as st
from deep_translator import GoogleTranslator
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import torch
from diffusers import StableDiffusionPipeline

# Streamlit UI
st.set_page_config(page_title="Indic Infographic Generator", layout="wide")
st.title("🌐 ChitraKatha")

# Load model (you only need to do this once)
@st.cache_resource
def load_model():
    model = StableDiffusionPipeline.from_pretrained(
        "CompVis/stable-diffusion-v1-4",
        torch_dtype=torch.float32
    )
    model = model.to("cpu")  # Change to "cuda" if you have GPU
    return model

pipe = load_model()

LANGUAGE_MAP = {
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Bengali": "bn"
}

FONT_PATHS = {
    "Telugu": "fonts/NotoSansTelugu-Regular.ttf",
    "Hindi": "fonts/NotoSansDevanagari-Regular.ttf",
    "Tamil": "fonts/NotoSansTamil-Regular.ttf",
    "Kannada": "fonts/NotoSansKannada-Regular.ttf",
    "Malayalam": "fonts/NotoSansMalayalam-Regular.ttf",
    "Bengali": "fonts/NotoSansBengali-Regular.ttf"
}

def translate_text(text, target_lang):
    lang_code = LANGUAGE_MAP.get(target_lang)
    return GoogleTranslator(source='en', target=lang_code).translate(text)

def generate_image(prompt):
    result = pipe(prompt).images[0]
    return result

def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = words[0]
    for word in words[1:]:
        line = f"{current} {word}"
        if draw.textbbox((0, 0), line, font=font)[2] <= max_width:
            current = line
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines

def overlay_text(image, text, language):
    draw = ImageDraw.Draw(image)
    font_path = FONT_PATHS.get(language, "arial.ttf")
    font = ImageFont.truetype(font_path, 40)
    width, height = image.size

    lines = wrap_text(draw, text, font, width - 60)
    y = height - len(lines) * 50 - 30

    for line in lines:
        w = draw.textbbox((0, 0), line, font=font)[2]
        draw.text(((width - w) / 2, y), line, font=font, fill="white")
        y += 50

    output = BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output

text_input = st.text_area("Enter a message in English:", "Save water, save life.")
language = st.selectbox("Choose target language", list(LANGUAGE_MAP.keys()))

if st.button("Generate Infographic"):
    with st.spinner("Translating and Generating..."):
        translated = translate_text(text_input, language)
        generated_img = generate_image(text_input)
        final_output = overlay_text(generated_img, translated, language)

        st.image(final_output, caption=f"Infographic in {language}", use_container_width=True)
        st.download_button(
            label="📥 Download Infographic",
            data=final_output,
            file_name=f"infographic_{language}.png",
            mime="image/png"
        )
