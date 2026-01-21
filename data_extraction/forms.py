from django import forms


class MultipleFileInput(forms.FileInput):
    """Custom widget that supports multiple file uploads."""
    def __init__(self, attrs=None):
        # Remove 'multiple' from attrs temporarily to pass Django's check
        if attrs is None:
            temp_attrs = {}
            multiple = True
        else:
            temp_attrs = attrs.copy()
            multiple = temp_attrs.pop('multiple', True)
        super().__init__(attrs=temp_attrs)
        # Now set multiple after initialization to bypass Django's validation
        self.attrs['multiple'] = multiple
    
    def value_from_datadict(self, data, files, name):
        # Return all files as a list
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        return []


class MultipleFileField(forms.Field):
    """Custom field that handles multiple file uploads."""
    widget = MultipleFileInput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget = MultipleFileInput(attrs={
            'multiple': True,
            'accept': '.pdf,.jpeg,.jpg,.xls,.xlsx',
            'class': 'file-input'
        })

    def clean(self, data, initial=None):
        # data will be a list of files from the widget
        if not data:
            if self.required:
                raise forms.ValidationError('Please select at least one file.')
            return []
        
        allowed_extensions = ['.pdf', '.jpeg', '.jpg', '.xls', '.xlsx']
        validated_files = []
        
        for file in data:
            if not file:
                continue
            file_name = file.name.lower()
            if not any(file_name.endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError(
                    f'File "{file.name}" is not a valid format. '
                    'Only PDF, JPEG, and XLS files are allowed.'
                )
            validated_files.append(file)
        
        if not validated_files and self.required:
            raise forms.ValidationError('Please select at least one file.')
        
        return validated_files


class FileUploadForm(forms.Form):
    files = MultipleFileField(
        label='Upload Files',
        help_text='Select one or more files (PDF, JPEG, or XLS)',
        required=True
    )
