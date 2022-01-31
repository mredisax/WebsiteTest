from django.urls import re_path, path
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf.urls import url
from . import views
from .views import homepage_view, website_view, website_view_api, website_update_api, website_report_view


urlpatterns = [
    path('', views.homepage_view, name='home'),
    path('strony/<str:slug>/<id>/', views.website_view, name='website_list'),
    path('generate', views.website_report_view, name='report'),
    path('api/websites/<id>', views.website_update_api),
    url(r'^api/websites/', views.website_view_api),

]

urlpatterns += format_suffix_patterns(urlpatterns)
