from django.forms import ModelForm
import django.forms as forms

from .models import Country, Node, NodeType, Declaration

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
        fields = ['name','sort_name','nodetype','country','population','parent','supplements','comment_public','comment_private','reference_links']
        widgets = {
            'nodetype': forms.HiddenInput(),
            'parent': forms.HiddenInput(),
            'country': forms.HiddenInput(),
        }

    #parent = Form.get_initial_for_field('parent')
    #supplements = forms.ModelMultipleChoiceField(queryset = Node.objects.filter(country_id=11))

class DeclarationForm(NodeForm):
    class Meta:
        model = Declaration
        fields = ['node','status', 'date_declared', 'declaration_links', 'declaration_type']
        widgets = {
            'node': forms.HiddenInput(),
        }

    date_declared = forms.DateField(input_formats=['%Y-%m-%d'])
