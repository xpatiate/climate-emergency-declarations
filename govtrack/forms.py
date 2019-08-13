from django.forms import ModelForm
import django.forms as forms
from django.core.validators import URLValidator

from .models import Country, Node, Structure, Declaration, Link

class CountryForm(ModelForm):
    class Meta:
        model = Country
        fields = ['name', 'population', 'description', 'admin_notes']
    description = forms.CharField(widget=forms.Textarea,label='Description', required=False)
    admin_notes = forms.CharField(widget=forms.Textarea,label='Admin Notes', required=False)

class StructureForm(ModelForm):
    class Meta:
        model = Structure
        fields = ['name','country','level','parent', 'admin_notes']
        widgets = {
            'country': forms.HiddenInput(),
            'level': forms.HiddenInput(),
            'parent': forms.HiddenInput()
            }

class NodeForm(ModelForm):
    
    class Meta:
        model = Node
        fields = ['name','sort_name','structure','country','location', 'population','parent','supplements','description','admin_notes']
        widgets = {
            'structure': forms.HiddenInput(),
            'parent': forms.HiddenInput(),
            'country': forms.HiddenInput(),
        }
    description = forms.CharField(widget=forms.Textarea,label='Description', required=False)
    admin_notes = forms.CharField(widget=forms.Textarea,label='Admin Notes', required=False)


class DeclarationForm(ModelForm):
    class Meta:
        model = Declaration
        fields = ['node','status', 'event_date', 'declaration_type', 'verified',
            'description_short', 'description_long', 'admin_notes']
        widgets = {
            'node': forms.HiddenInput(),
        }

    event_date = forms.DateField(
        input_formats=['%d %b, %Y','%d %b %Y', '%d %B %Y','%Y-%m-%d','%d %B, %Y','%d-%m-%Y'],
        widget=forms.DateInput(format='%d %b %Y'),
        )
    description_short = forms.CharField(widget=forms.Textarea, label='Summary', required=False)
    description_long = forms.CharField(widget=forms.Textarea,label='Details', required=False)
    admin_notes = forms.CharField(widget=forms.Textarea,label='Admin Notes', required=False)


class LinkForm(ModelForm):
    prefix = 'link'
    url = forms.CharField(required=False, label='Add link', validators=[URLValidator()])
    class Meta:
        model = Link
        fields = ['url', 'content_type', 'object_id']
        widgets = {
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
        }
