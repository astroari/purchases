from django.shortcuts import render
from .forms import FileUploadForm
from .pdf_extractor import extract_pdf_from_file


def upload_files(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = form.cleaned_data['files']
            file_names = [f.name for f in files]
            extracted_data_list = []
            
            # Process PDF files
            for file in files:
                if file.name.lower().endswith('.pdf'):
                    extracted_data = extract_pdf_from_file(file)
                    extracted_data_list.append(extracted_data)
                else:
                    # For non-PDF files, just store the file info
                    extracted_data_list.append({
                        'file_name': file.name,
                        'file_type': 'non-pdf',
                        'error': 'Only PDF extraction is currently implemented'
                    })
            
            return render(request, 'data_extraction/upload_success.html', {
                'file_names': file_names,
                'file_count': len(file_names),
                'extracted_data_list': extracted_data_list
            })
    else:
        form = FileUploadForm()
    
    return render(request, 'data_extraction/upload.html', {'form': form})
