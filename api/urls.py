from django.urls import path

from . import views

urlpatterns = [
    # API paths
    path('import_declarations/add/<str:country_id>', views.add_multi_import_declarations, name='api_import_declaration_multi_add'),
    path('import_declaration/del/<int:import_declaration_id>', views.import_declaration_del, name='api_import_declaration_del'),
    path('import_declaration/pro/<int:parent_id>/<int:structure_id>/<int:import_declaration_id>', views.import_declaration_pro, name='api_import_declaration_pro'),
    path('import_declaration/dec/<int:area_id>/<int:import_declaration_id>', views.declaration_from_import, name='api_import_declaration_dec'),
    path('areas/add/<int:parent_id>/<int:structure_id>', views.add_multi_areas, name='api_area_multi_add'),
    path('country/<str:country_code>/population', views.country_population, name='api_country_population'),
    path('country/<str:country_code>/declarations', views.country_declarations, name='api_country_declarations'),
    path('country/<str:country_code>/population_timeline', views.country_population_timeline, name='api_country_pop_time'),
    path('country/<str:country_code>/regenerate_timeline', views.country_regenerate_timeline, name='api_country_regen_time'),
    path('country/<str:country_code>/trigger_recount', views.country_trigger_recount, name='api_country_trigger_recount'),
    path('area/del/<int:area_id>', views.area_del, name='api_area_del'),
    path('area/<int:area_id>/row', views.area_data, name='api_area_data'),
    path('structure/del/<int:structure_id>', views.structure_del, name='api_structure_del'),
    path('declaration/del/<int:declaration_id>', views.declaration_del, name='api_declaration_del'),
    path('link/del/<int:link_id>', views.link_del, name='api_link_del'),
]
