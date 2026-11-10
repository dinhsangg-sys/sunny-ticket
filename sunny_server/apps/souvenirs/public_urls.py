from django.urls import path
from . import views
urlpatterns=[path('',views.catalog),path('catalog/',views.catalog),path('p/<slug:slug>/',views.detail),path('assets/<uuid:key>/',views.media)]
