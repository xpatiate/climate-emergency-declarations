from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('countries/', views.countries, name='countries'),
    path('country/<int:country_id>', views.country, name='country'),
    path('country/edit/<int:country_id>', views.country, {'action': 'edit'}, name='country_edit'),
    path('node/<int:node_id>/', views.node, name='node'),
    path('nodetype/edit/<int:nodetype_id>/', views.nodetype_edit, name='nodetype_edit'),
    path('nodetype/child/<int:parent_id>/', views.nodetype_child, name='nodetype_child'),
    path('nodetype/del/<int:nodetype_id>', views.nodetype_del, name='nodetype_del'),
    path('node/edit/<int:node_id>/', views.node_edit, name='node_edit'),
    path('declaration/<int:declaration_id>/', views.declaration, name='declaration'),
    path('declaration/add/<int:node_id>/', views.declaration_add, name='declaration_add'),
    path('declaration/edit/<int:declaration_id>/', views.declaration_edit, name='declaration_edit'),
    path('node/child/<int:parent_id>/<int:nodetype_id>', views.node_child, name='node_child'),
    # API paths
    path('api/extract_nodes', views.extract_node_data, name='node_extract'),
    path('api/nodes/add/<int:parent_id>/<int:nodetype_id>', views.add_multi_nodes, name='node_multi_add'),
    path('api/country/<str:country_code>/declarations', views.country_declarations, name='country_api_code'),
    path('api/del/node/<int:node_id>', views.node_del, name='node_del'),
    path('api/del/nodetype/<int:nodetype_id>', views.nodetype_del, name='nodetype_del'),
    path('api/del/declaration/<int:declaration_id>', views.declaration_del, name='declaration_del'),
    path('api/del/link/<int:link_id>', views.link_del, name='link_del'),
]
