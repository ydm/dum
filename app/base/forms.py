from django import forms


class UploadFileForm(forms.Form):
    table = forms.FileField()
