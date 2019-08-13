from django.urls import path

from . import views

urlpatterns = [
    # API paths
    path('extract_areas', views.extract_area_data, name='area_extract'),
    path('areas/add/<int:parent_id>/<int:structure_id>', views.add_multi_areas, name='area_multi_add'),
    path('country/<str:country_code>/declarations', views.country_declarations, name='country_api_code'),
    path('area/del/<int:area_id>', views.area_del, name='area_del'),
    path('structure/del/<int:structure_id>', views.structure_del, name='structure_del'),
    path('declaration/del/<int:declaration_id>', views.declaration_del, name='declaration_del'),
    path('link/del/<int:link_id>', views.link_del, name='link_del'),
]
