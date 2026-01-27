from PyPDF2 import PdfReader

# Load the PDF file
reader = PdfReader("./input_pdfs/AR-Z8-900245-02-STAINBLASTER ENZYME BOOST.PDF")
input = " "
# Extract text from each page
for page in reader.pages:
    input += page.extract_text()
    print(input)

