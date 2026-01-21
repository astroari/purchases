import pdfplumber
from typing import Dict, List, Any


def extract_pdf_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extract text and tables from a PDF file using pdfplumber.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing extracted text and tables per page
    """
    extracted_data = {
        'pages': [],
        'total_pages': 0,
        'total_tables': 0
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            extracted_data['total_pages'] = len(pdf.pages)
            
            # Iterate through pages to extract text and tables
            for page_num, page in enumerate(pdf.pages, start=1):
                page_data = {
                    'page_number': page_num,
                    'text': None,
                    'tables': []
                }
                
                # Extract the text
                text = page.extract_text()
                if text:
                    page_data['text'] = text
                
                # Extract the tables
                tables = page.extract_tables()
                if tables:
                    page_data['tables'] = tables
                    extracted_data['total_tables'] += len(tables)
                
                extracted_data['pages'].append(page_data)
                if page_data['text'].find('18 Идентификация') != -1 and page_data['text'].find('21 Идентификация') != -1:
                    substring = page_data['text'][page_data['text'].find('18 Идентификация') : page_data['text'].find('21 Идентификация')]
                    print(substring)
                print("--------------------------------")
    
    except Exception as e:
        extracted_data['error'] = str(e)
    
    return extracted_data


def extract_pdf_from_file(file) -> Dict[str, Any]:
    """
    Extract text and tables from an uploaded Django file object.
    
    Args:
        file: Django UploadedFile object
        
    Returns:
        Dictionary containing extracted text and tables per page
    """
    extracted_data = {
        'pages': [],
        'total_pages': 0,
        'total_tables': 0,
        'file_name': file.name
    }
    
    try:
        # Save the uploaded file temporarily to process it
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            for chunk in file.chunks():
                tmp_file.write(chunk)
            tmp_path = tmp_file.name
        
        try:
            # Extract data from the temporary file
            extracted_data = extract_pdf_data(tmp_path)
            extracted_data['file_name'] = file.name
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        extracted_data['error'] = str(e)
    
    return extracted_data
