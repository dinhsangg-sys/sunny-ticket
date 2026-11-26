from django.urls import path
from . import views
from apps.online import chat
urlpatterns=[path('api/public/chat/services/',chat.services),path('api/public/chat/ask/',chat.ask),path('',views.catalog),path('catalog/',views.catalog),path('p/<slug:slug>/',views.detail),path('assets/<uuid:key>/',views.media)]
