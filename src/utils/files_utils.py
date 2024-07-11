import fitz

def read_text_from_pdf(pdf_path):
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    
    # Initialize an empty string to store the extracted text
    extracted_text = ""
    
    # Iterate through each page in the PDF
    for page_num in range(len(pdf_document)):
        # Get the page
        page = pdf_document.load_page(page_num)
        
        # Extract text from the page
        page_text = page.get_text()
        
        # Append the text of the current page to the extracted text
        extracted_text += page_text + "\n"
    
    # Close the PDF document
    pdf_document.close()
    
    return extracted_text
