import streamlit as st
import fitz  # PyMuPDF
import pytesseract
import io

st.set_page_config(page_title="PDF Editor (Cloud Safe)", layout="wide")
st.title("📄 PDF Editor – Text & Scanned PDFs (No Poppler Needed)")

uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file:
    uploaded_bytes = uploaded_file.read()
    uploaded_file.seek(0)
    text_content = ""
    is_scanned = False

    pdf_in = fitz.open(stream=uploaded_bytes, filetype="pdf")
    page_fonts = []

    # Step 1: Check if PDF has selectable text
    with st.spinner("🔍 Checking PDF content..."):
        for page in pdf_in:
            blocks = page.get_text("blocks")
            if blocks:
                for b in blocks:
                    text_content += b[4] + "\n"
                    # Get font info if available
                    try:
                        font_info = page.get_text("dict")["blocks"][0]["lines"][0]["spans"][0]["font"]
                        page_fonts.append(font_info)
                    except:
                        page_fonts.append("helv")

    if not text_content.strip():
        is_scanned = True
        st.warning("No selectable text found. Running OCR...")
        with st.spinner("📝 Performing OCR on PDF pages..."):
            for page in pdf_in:
                pix = page.get_pixmap()
                text_content += pytesseract.image_to_string(pix.tobytes("png")) + "\n"
        st.success("✅ OCR complete!")

    # Step 2: Let user edit text
    edited_text = st.text_area("✏️ Edit Text Below", value=text_content, height=400)

    # Step 3: Save PDF
    if st.button("💾 Save Edited PDF"):
        with st.spinner("📦 Creating PDF..."):
            pdf_out = fitz.open()
            edited_lines = edited_text.split("\n")

            if not is_scanned:
                # Text PDF: preserve font and positions
                line_idx = 0
                block_idx = 0
                for page in pdf_in:
                    new_page = pdf_out.new_page(width=page.rect.width, height=page.rect.height)
                    blocks = page.get_text("blocks")
                    for b in blocks:
                        if line_idx < len(edited_lines):
                            x, y = b[0], b[1]
                            fontname = page_fonts[block_idx] if block_idx < len(page_fonts) else "helv"
                            fontsize = max(12, b[3]-b[1]-2)
                            new_page.insert_text((x, y), edited_lines[line_idx],
                                                 fontname=fontname, fontsize=fontsize,
                                                 color=(0, 0, 0))
                            line_idx += 1
                            block_idx += 1
            else:
                # Scanned PDF: overlay text on original page image
                num_pages = len(pdf_in)
                lines_per_page = max(len(edited_lines) // num_pages, 1)
                for i, page in enumerate(pdf_in):
                    new_page = pdf_out.new_page(width=page.rect.width, height=page.rect.height)
                    pix = page.get_pixmap()
                    img_bytes = pix.tobytes("png")
                    new_page.insert_image(page.rect, stream=img_bytes)

                    start_line = i * lines_per_page
                    end_line = start_line + lines_per_page
                    y = 40
                    for line in edited_lines[start_line:end_line]:
                        fontsize = max(12, page.rect.height / 60)
                        new_page.insert_text((40, y), line, fontsize=fontsize, fontname="helv", color=(0, 0, 0))
                        y += fontsize + 2

            pdf_bytes = pdf_out.write()
            pdf_out.close()

        st.success("✅ PDF created successfully!")
        st.download_button(
            label="⬇️ Download Edited PDF",
            data=pdf_bytes,
            file_name="edited_final.pdf",
            mime="application/pdf"
        )
else:
    st.info("📤 Please upload a PDF file to start.")
