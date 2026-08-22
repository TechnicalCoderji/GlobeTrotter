from django.urls import path
from .views import (
    home_view,
    start_trip,
    step2_events,
    step3_final_plan,
    trip_list_view,
    trip_detail_or_builder,
    trip_edit_view,
    trip_delete_view,
    add_day_view,
    delete_day_view,
    add_item_view,
    delete_item_view,
    trip_budget_view,
    trip_calendar_view,
    trip_export_json_view,
    trip_copy_view,
    city_search_view,
    activity_search_view,
    community_view,
    analytics_view,
    generate_itinerary_api,
    smart_budget_api,
    activity_recommendation_api,
    ai_tools_view,
)

urlpatterns = [
    path('', home_view, name='home'),
    path('dashboard/', home_view, name='dashboard'),
    
    # Step-by-step multi-city flow
    path('start/', start_trip, name='start_trip'),
    path('trips/create/', start_trip, name='trip_create'),
    path('events/', step2_events, name='step2_events'),
    path('plan/', step3_final_plan, name='step3_final_plan'),
    
    # Trip Management
    path('trips/', trip_list_view, name='trip_list'),
    path('trips/<int:trip_id>/', trip_detail_or_builder, name='trip_detail'),
    path('trips/<int:trip_id>/itinerary/', trip_detail_or_builder, name='itinerary_builder'),
    path('trips/<int:trip_id>/edit/', trip_edit_view, name='trip_edit'),
    path('trips/<int:trip_id>/delete/', trip_delete_view, name='trip_delete'),
    path('trips/<int:trip_id>/add-day/', add_day_view, name='add_day'),
    path('trips/<int:trip_id>/days/<int:day_id>/delete/', delete_day_view, name='delete_day'),
    path('trips/<int:trip_id>/days/<int:day_id>/add-item/', add_item_view, name='add_item'),
    path('trips/<int:trip_id>/items/<int:item_id>/delete/', delete_item_view, name='delete_item'),
    path('trips/<int:trip_id>/budget/', trip_budget_view, name='trip_budget'),
    path('trips/<int:trip_id>/calendar/', trip_calendar_view, name='trip_calendar'),
    path('trips/<int:trip_id>/export/', trip_export_json_view, name='trip_export_json'),
    path('trips/<int:trip_id>/copy/', trip_copy_view, name='trip_copy'),
    
    # Discovery & Community
    path('cities/search/', city_search_view, name='city_search'),
    path('activities/search/', activity_search_view, name='activity_search'),
    path('community/', community_view, name='community'),
    path('analytics/', analytics_view, name='analytics'),
    
    # AI REST Endpoints
    path('ai/generate-itinerary/', generate_itinerary_api, name='ai_generate_itinerary'),
    path('ai/budget/', smart_budget_api, name='ai_smart_budget'),
    path('ai/activities/', activity_recommendation_api, name='ai_activities'),
    path('ai/tools/', ai_tools_view, name='ai_tools'),
]