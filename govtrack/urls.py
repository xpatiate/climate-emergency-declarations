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
    path('structure/del/<int:structure_id>', views.structure_del, name='structure_del'),
    path('area/edit/<int:area_id>/', views.area_edit, name='area_edit'),
    path('declaration/<int:declaration_id>/', views.declaration, name='declaration'),
    path('declaration/add/<int:area_id>/', views.declaration_add, name='declaration_add'),
    path('declaration/edit/<int:declaration_id>/', views.declaration_edit, name='declaration_edit'),
    path('area/child/<int:parent_id>/<int:structure_id>', views.area_child, name='area_child'),
    # API paths
    path('api/extract_areas', views.extract_area_data, name='area_extract'),
    path('api/areas/add/<int:parent_id>/<int:structure_id>', views.add_multi_areas, name='area_multi_add'),
    path('api/country/<str:country_code>/declarations', views.country_declarations, name='country_api_code'),
    path('api/del/area/<int:area_id>', views.area_del, name='area_del'),
    path('api/del/structure/<int:structure_id>', views.structure_del, name='structure_del'),
    path('api/del/declaration/<int:declaration_id>', views.declaration_del, name='declaration_del'),
    path('api/del/link/<int:link_id>', views.link_del, name='link_del'),
]
