import streamlit as st
import pandas as pd
from google.cloud import translate_v2 as translate
import os
import tempfile
import re

# Step 1: Set up Google Cloud credentials
# Write the Google Translate API credentials from Streamlit Secrets to a temporary file
with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_json_file:
    temp_json_file.write(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"].encode("utf-8"))
    temp_json_file_path = temp_json_file.name

# Set the environment variable to point to the temporary credentials file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_json_file_path

# Initialize the Google Translate client
translate_client = translate.Client()

# Function to translate text, skipping content inside curly brackets
def translate_text(text, target_language):
    if isinstance(text, str) and text.strip():  # Ensure it's a valid string
        
        # Step 1: Find and preserve content inside curly brackets
        parts = re.split(r'(\{.*?\})', text)  # Split by curly brackets, keeping them in the result

        # Step 2: Translate only the parts that are not within curly brackets
        translated_parts = [
            part if re.match(r'\{.*?\}', part) else translate_client.translate(part, target_language=target_language)['translatedText']
            for part in parts
        ]

        # Step 3: Recombine everything
        return ''.join(translated_parts)

    return text  # Return original if empty or not a valid string

# Streamlit app structure
st.title("CSV Translator with Google Translate API")

# Step 2: File upload
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    # Read the uploaded CSV
    df = pd.read_csv(uploaded_file)
    st.write("Here is a preview of your uploaded file:")
    st.write(df.head())

    # Step 3: Select target language
    target_language = st.selectbox(
        "Select the target language for translation",
        ["en", "es", "fr", "de", "it", "pt", "pt-br", ],  # Example: Spanish, French, German, etc.
        index=0
    )

    # Step 4: List columns to translate
    columns_to_translate = ['Subject', 'Message', 'Expected Action Title']
    text_button_columns = [col for col in df.columns if 'Text Button' in col]
    columns_to_translate.extend(text_button_columns)

    st.write("The following columns will be translated:", columns_to_translate)

    # Step 5: Perform the translation
    if st.button("Translate"):
        for col in columns_to_translate:
            df[col] = df[col].apply(lambda x: translate_text(x, target_language))

        st.success("Translation completed!")

        # Step 6: Display the translated CSV and provide download option
        st.write("Here is a preview of the translated file:")
        st.write(df.head())

        # Save translated CSV to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
            df.to_csv(tmp_file.name, index=False)
            tmp_file_path = tmp_file.name

        # Provide a download button for the translated CSV
        with open(tmp_file_path, 'rb') as f:
            st.download_button(
                label="Download Translated CSV",
                data=f,
                file_name="translated_file.csv",
                mime="text/csv"
            )
