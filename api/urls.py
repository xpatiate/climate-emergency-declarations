from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"structures", views.StructureViewSet)

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
    path('country/<str:country_code>/pop_by_location', views.country_pop_by_location, name='api_country_pop_location'),
    path('country/<str:country_code>/regenerate_timeline', views.country_regenerate_timeline, name='api_country_regen_time'),
    path('country/<str:country_code>/trigger_recount', views.country_trigger_recount, name='api_country_trigger_recount'),
    path('popcount/regenerate', views.trigger_all_recounts, name='api_trigger_all_recounts'),
    path('area/del/<int:area_id>', views.area_del, name='api_area_del'),
    path('area/<int:area_id>/row', views.area_data, name='api_area_data'),
    path('structure/del/<int:structure_id>', views.structure_del, name='api_structure_del'),
    path('declaration/del/<int:declaration_id>', views.declaration_del, name='api_declaration_del'),
    path('link/del/<int:link_id>', views.link_del, name='api_link_del'),
    path('world/population_timeline', views.world_population_timeline, name='api_world_pop_time'),
    # DRF API paths
    path('area/', views.AreaList.as_view()),
    path('area/<int:pk>', views.AreaDetail.as_view()),
    path('area/<int:pk>/children/', views.AreaChildren.as_view()),
    path("", include(router.urls)),
]
