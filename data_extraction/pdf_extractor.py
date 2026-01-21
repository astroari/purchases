import pdfplumber
import re
from typing import Dict, List, Any


def format_extracted_text(text: str) -> str:
    """
    Format the extracted text substring into a readable format.
    
    Args:
        text: Raw extracted text substring
        
    Returns:
        Formatted string with identification and delivery terms
    """
    if not text:
        return ""
    
    # Remove any leading/trailing whitespace and special characters like '@Python (1012-1013)'
    text = text.strip()
    
    # Remove patterns like '@Python (1012-1013) ' at the start
    text = re.sub(r'^@\w+\s*\(\d+-\d+\)\s*', '', text)
    print(text)
    
    # Find the identification number - extract everything between '18 Идентификация...' and '19 Конт.'
    identification_number = None
    id_header = '20 Условия поставки'
    id_start = text.find(id_header)
    kont_pos = text.find('FCA')
    
    if id_start != -1 and kont_pos != -1:
        # Extract the section between the header and '19 Конт.'
        identification_section = text[id_start:kont_pos].strip()
        # Remove the header text to get just the identification number
        if identification_section.startswith(id_header):
            identification_number = identification_section[len(id_header):].strip()
            identification_number = identification_number[:-1]
        else:
            identification_number = identification_section.strip()
    
    # Find delivery terms - look for '20 Условия поставки' and extract what comes after
    delivery_terms = None
    usloviya_pos = text.find('20 Условия поставки')
    if usloviya_pos != -1:
        # Extract everything after '20 Условия поставки'
        delivery_section = text[usloviya_pos + len('20 Условия поставки'):].strip()
        # Look for delivery term codes (FCA, EXW, etc.) and extract from there
        delivery_match = re.search(r'(FCA|EXW|FOB|CFR|CIF|DAP|DDP|CPT|CIP)\s+([А-ЯЁA-Z\s]+)', delivery_section, re.IGNORECASE)
        if delivery_match:
            delivery_terms = delivery_section[delivery_match.start():].strip()
        else:
            # If no delivery code found, just take the text after '20 Условия поставки'
            delivery_terms = delivery_section.strip()
    
    # Build the formatted output with simple UI-friendly bullets
    formatted_lines = []
    
    identification_value = identification_number if identification_number else "—"
    formatted_lines.append(
        f"- <strong>Идентификация и страна регистрации трансп. средства при отправлении/прибытии:</strong> {identification_value}"
    )
    
    if delivery_terms:
        # Indent multiline delivery terms to align under the bullet
        delivery_block = delivery_terms.replace("\n", "\n  ")
    else:
        delivery_block = "—"
    
    formatted_lines.append(f"- <strong>Условия поставки:</strong> {delivery_block}")
    
    # Ensure we don't carry any accidental leading indentation on the first line
    return "\n".join(formatted_lines).lstrip()


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
    target_string = 'Идентификация и страна регистрации трансп.'
    skip_tables = False
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            extracted_data['total_pages'] = len(pdf.pages)
            
            # Iterate through pages to extract text and tables
            for page_num, page in enumerate(pdf.pages, start=1):
                page_data = {
                    'page_number': page_num,
                    'text': None,  # Only populate when target substring is found
                    'tables': []
                }

                # Extract the text
                text = page.extract_text()
                if text and target_string in text:
                    # If the target string is present anywhere in the file, drop all tables
                    skip_tables = True
                    extracted_data['total_tables'] = 0
                    for existing_page in extracted_data['pages']:
                        existing_page['tables'] = []

                # Extract tables only if we have not encountered the target string
                if not skip_tables:
                    tables = page.extract_tables()
                    if tables:
                        # Apply this normalization ONLY to the first table on page 1
                        if page_num == 1 and tables[0]:
                            # drop header row
                            if len(tables[0]) > 0:
                                tables[0].pop(0)
                            # drop first column from each remaining row (if present)
                            for row in tables[0]:
                                if row:
                                    row.pop(0)

                        # Drop the last two rows of the last table on the last PDF page
                        if page_num == extracted_data['total_pages']:
                            last_table = tables[-1]
                            if last_table and len(last_table) >= 2:
                                del last_table[-2:]

                        page_data['tables'] = tables
                        extracted_data['total_tables'] += len(tables)
                        print(tables)

                # Extract text if the target pattern is found
                if text and text.find('18 Идентификация') != -1 and text.find('21 Идентификация') != -1:
                    substring = text[text.find('18 Идентификация') : text.find('21 Идентификация')]
                    formatted_text = format_extracted_text(substring)
                    page_data['text'] = formatted_text
                    print(formatted_text)
                
                # Only add the page if it has content (text or tables)
                if page_data['text'] or page_data['tables']:
                    extracted_data['pages'].append(page_data)
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
