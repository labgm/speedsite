from django import forms

class UploadFileForm(forms.Form):
    name = forms.CharField(required=False, label='Name', max_length = 100, widget=forms.TextInput(attrs={
                                    'placeholder':'Enter your name...',
                                    'class': 'form-control',
                                    'id': 'inputName',
                                 }))
    email = forms.CharField(label='E-mail', widget=forms.EmailInput(attrs={
                                    'placeholder':'Enter your e-mail...',
                                    'class': 'form-control',
                                    'id': 'inputEmail',
                                 }))
    fileFastq = forms.FileField(label='Upload your Fastq files (\'.fq.gz\')',
                widget=forms.ClearableFileInput(attrs={
                'multiple': True,
                'accept': '.gz',
                'class': 'form-control',
                'id': 'inputFastq',
                }))