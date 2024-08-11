from fpdf import FPDF
import os

def txt_to_pdf(txt_file, output_pdf):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=10)  # Adjusted font size to 10
    
    with open(txt_file, "r", encoding="utf-8") as f:
        for line in f:
            pdf.write(5, txt=line.encode('latin-1', 'replace').decode('latin-1'))  # Adjusted line height to 5
            pdf.ln()
    
    pdf.output(output_pdf)

def convert_txt_files_to_pdf(txt_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(txt_folder):
        if filename.endswith(".txt"):
            txt_file = os.path.join(txt_folder, filename)
            pdf_file = os.path.join(output_folder, filename.replace(".txt", ".pdf"))
            
            txt_to_pdf(txt_file, pdf_file)
            print(f"Converted {filename} to PDF.")

# Example usage:
txt_folder = "txt_data"
output_folder = "data"

convert_txt_files_to_pdf(txt_folder, output_folder)
