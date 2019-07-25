from django.forms import ModelForm
import django.forms as forms

from .models import Country, Node, NodeType, Declaration, Link

class CountryForm(ModelForm):
    class Meta:
        model = Country
        fields = ['name', 'population']

class NodeTypeForm(ModelForm):
    class Meta:
        model = NodeType
        fields = ['name','country','level','parent', 'is_governing']
        widgets = {
            'country': forms.HiddenInput(),
            'level': forms.HiddenInput(),
            'parent': forms.HiddenInput()
            }

class NodeForm(ModelForm):
    
    class Meta:
        model = Node
        fields = ['name','sort_name','nodetype','country','population','parent','supplements','comment_public','comment_private']
        widgets = {
            'nodetype': forms.HiddenInput(),
            'parent': forms.HiddenInput(),
            'country': forms.HiddenInput(),
        }


class DeclarationForm(NodeForm):
    class Meta:
        model = Declaration
        fields = ['node','status', 'date_declared', 'declaration_type']
        widgets = {
            'node': forms.HiddenInput(),
        }

    date_declared = forms.DateField(input_formats=['%Y-%m-%d'])

class LinkForm(ModelForm):
    url = forms.CharField(required=False)
    class Meta:
        model = Link
        fields = ['url', 'content_type', 'object_id']
        widgets = {
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
        }
