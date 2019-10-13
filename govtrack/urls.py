from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('countries/', views.countries, name='countries'),
    path('country/<int:country_id>', views.country, name='country'),
    path('country/edit/<int:country_id>', views.country, {'action': 'edit'}, name='country_edit'),
    path('area/<int:area_id>/', views.area, name='area'),
    path('structure/edit/<int:structure_id>/', views.structure_edit, name='structure_edit'),
    path('structure/child/<int:parent_id>/', views.structure_child, name='structure_child'),
    path('area/edit/<int:area_id>/', views.area_edit, name='area_edit'),
    path('declaration/<int:declaration_id>/', views.declaration, name='declaration'),
    path('declaration/add/<int:area_id>/', views.declaration_add, name='declaration_add'),
    path('declaration/edit/<int:declaration_id>/', views.declaration_edit, name='declaration_edit'),
    path('area/child/<int:parent_id>/<int:structure_id>', views.area_child, name='area_child'),
    path('inbox/<int:country_id>', views.inbox, name='inbox'),
]
