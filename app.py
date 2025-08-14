import streamlit as st
from PIL import Image
import easyocr
import fitz  # PyMuPDF
import numpy as np

st.set_page_config(page_title="Photo to Editable PDF", layout="wide")
st.title("📸 Photo → Editable PDF")

uploaded_file = st.file_uploader("Upload an image of your document", type=["png", "jpg", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Document", use_column_width=True)

    # Step 1: OCR
    reader = easyocr.Reader(['en'])
    img_np = np.array(image)
    with st.spinner("📝 Extracting text via OCR..."):
        text_lines = reader.readtext(img_np, detail=0)
        extracted_text = "\n".join(text_lines)
    st.success("✅ OCR complete!")

    # Step 2: Let user edit text
    edited_text = st.text_area("✏️ Edit extracted text below", value=extracted_text, height=400)

    # Step 3: Save as PDF
    if st.button("💾 Save as PDF"):
        pdf = fitz.open()
        page = pdf.new_page(width=image.width, height=image.height)

        # Insert original image as background
        img_bytes = uploaded_file.read()
        page.insert_image(page.rect, stream=img_bytes)

        # Overlay edited text
        y = 40
        for line in edited_text.split("\n"):
            fontsize = max(12, image.height / 60)
            page.insert_text((40, y), line, fontsize=fontsize, fontname="helv", color=(0, 0, 0))
            y += fontsize + 2

        pdf_bytes = pdf.write()
        pdf.close()

        st.success("✅ PDF created!")
        st.download_button(
            label="⬇️ Download Edited PDF",
            data=pdf_bytes,
            file_name="edited_document.pdf",
            mime="application/pdf"
        )
else:
    st.info("📤 Please upload an image to start.")
