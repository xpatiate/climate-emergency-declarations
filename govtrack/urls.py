from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('countries/', views.countries, name='countries'),
    path('country/<int:country_id>', views.country, name='country'),
    path('node/<int:node_id>/', views.node, name='node'),
    path('nodetype/edit/<int:nodetype_id>/', views.nodetype_edit, name='nodetype_edit'),
    path('nodetype/child/<int:parent_id>/', views.nodetype_child, name='nodetype_child'),
    path('nodetype/del/<int:nodetype_id>', views.nodetype_del, name='nodetype_del'),
    path('node/edit/<int:node_id>/', views.node_edit, name='node_edit'),
    path('declaration/<int:node_id>/', views.declaration_add, name='declaration_add'),
    path('declaration/edit/<int:declaration_id>/', views.declaration_edit, name='declaration_edit'),
    path('node/child/<int:parent_id>/<int:nodetype_id>', views.node_child, name='node_child'),
    # TODO prevent path-based deletion - integrate into edit path
    path('node/del/<int:node_id>', views.node_del, name='node_del'),
]
