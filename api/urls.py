from django.urls import path

from . import views

urlpatterns = [
    # API paths
    path('extract_areas', views.extract_area_data, name='api_area_extract'),
    path('areas/add/<int:parent_id>/<int:structure_id>', views.add_multi_areas, name='api_area_multi_add'),
    path('country/<str:country_code>/population', views.country_population, name='api_country_population'),
    path('country/<str:country_code>/declarations', views.country_declarations, name='api_country_declarations'),
    path('country/<str:country_code>/population_timeline', views.country_population_timeline, name='api_country_pop_time'),
    path('country/<str:country_code>/regenerate_timeline', views.country_regenerate_timeline, name='api_country_regen_time'),
    path('area/del/<int:area_id>', views.area_del, name='api_area_del'),
    path('area/<int:area_id>/row', views.area_data, name='api_area_data'),
    path('structure/del/<int:structure_id>', views.structure_del, name='api_structure_del'),
    path('declaration/del/<int:declaration_id>', views.declaration_del, name='api_declaration_del'),
    path('link/del/<int:link_id>', views.link_del, name='api_link_del'),
]
