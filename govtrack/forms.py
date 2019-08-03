from django.forms import ModelForm
import django.forms as forms
from django.core.validators import URLValidator

from .models import Country, Node, NodeType, Declaration, Link

class CountryForm(ModelForm):
    class Meta:
        model = Country
        fields = ['name', 'population']

class NodeTypeForm(ModelForm):
    class Meta:
        model = NodeType
        fields = ['name','country','level','parent', 'is_governing', 'admin_notes']
        widgets = {
            'country': forms.HiddenInput(),
            'level': forms.HiddenInput(),
            'parent': forms.HiddenInput()
            }

class NodeForm(ModelForm):
    
    class Meta:
        model = Node
        fields = ['name','sort_name','nodetype','country','location', 'population','parent','supplements','description','admin_notes']
        widgets = {
            'nodetype': forms.HiddenInput(),
            'parent': forms.HiddenInput(),
            'country': forms.HiddenInput(),
        }


class DeclarationForm(ModelForm):
    class Meta:
        model = Declaration
        fields = ['node','status', 'date_declared', 'declaration_type', 'verified',
            'description_short', 'description_long', 'admin_notes']
        widgets = {
            'node': forms.HiddenInput(),
        }

    date_declared = forms.DateField(
        input_formats=['%d %b %Y','%Y-%m-%d','%d %B, %Y'],
        widget=forms.DateInput(format='%d %b %Y'),
        )
    description_short = forms.CharField(widget=forms.Textarea, label='Summary')
    description_long = forms.CharField(widget=forms.Textarea,label='Details')
    admin_notes = forms.CharField(widget=forms.Textarea,label='Admin Notes')


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
