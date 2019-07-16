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
    path('node/convert/<int:node_id>/', views.node_convert, name='node_convert'),
    path('node/child/<int:parent_id>/<int:nodetype_id>', views.node_child, name='node_child'),
    path('govt/<int:govt_id>/', views.govt, name='govt'),
    path('govt/edit/<int:govt_id>/', views.govt_edit, name='govt_edit'),
    path('govt/child/<int:parent_id>/<int:nodetype_id>', views.govt_child, name='govt_child'),
    path('govt/convert/<int:node_id>/', views.govt_convert, name='govt_convert'),
    # TODO prevent path-based deletion - integrate into edit path
    path('govt/del/<int:govt_id>', views.govt_del, name='govt_del'),
    path('node/del/<int:node_id>', views.node_del, name='node_del'),
]
