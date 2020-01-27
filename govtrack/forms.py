from django.forms import ModelForm, Form
import django.forms as forms
from django.core.validators import URLValidator

from .models import Country, Area, Structure, Declaration, Link

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
            'parent': forms.HiddenInput(),
            'name': forms.TextInput(attrs={'autofocus': 'autofocus'})
            }

class AreaForm(ModelForm):
    
    class Meta:
        model = Area
        fields = ['name','sort_name','structure','country','agglomeration', 'location', 'population','parent','description','admin_notes']
        widgets = {
            'structure': forms.HiddenInput(),
            'parent': forms.HiddenInput(),
            'country': forms.HiddenInput(),
            'name': forms.TextInput(attrs={'autofocus': 'autofocus'})
        }
    description = forms.CharField(widget=forms.Textarea,label='Description', required=False)
    admin_notes = forms.CharField(widget=forms.Textarea,label='Admin Notes', required=False)

class DeclarationForm(ModelForm):
    class Meta:
        model = Declaration
        fields = ['area','status', 'event_date', 'declaration_type', 'verified',
            'description_short', 'description_long', 'key_contact', 'admin_notes']
        widgets = {
            'area': forms.HiddenInput(),
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
    object_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    class Meta:
        model = Link
        fields = ['url', 'content_type', 'object_id']
        widgets = {
            'content_type': forms.HiddenInput(),
        }

class BulkAreaForm(Form):
    location = forms.CharField(required=False)
    link = forms.CharField(required=False, label='Add link', validators=[URLValidator()])
    supplements_add = forms.MultipleChoiceField(
        label='Add supplementary parents',
        required=False
        )
    supplements_rm = forms.MultipleChoiceField(
        label='Remove supplementary parents',
        required=False
        )

