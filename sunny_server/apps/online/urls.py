from django.urls import path
from . import views
urlpatterns=[
 path('discover/',views.homepage,name='online-home'),
 path('services/',views.services,name='online-services'),
 path('services/<slug:slug>/',views.detail,name='online-service'),
 path('services/<slug:slug>/book/',views.checkout,name='online-checkout'),
 path('stories/',views.articles,name='online-articles'),
 path('stories/<slug:slug>/',views.detail,{'kind':'article'},name='online-article'),
 path('online/content/<str:kind>/<int:key>/',views.image,name='online-image'),
 path('online/orders/<uuid:key>/',views.order_page,name='online-order'),
 path('online/orders/<uuid:key>/status/',views.status,name='online-status'),
 path('online/staff/',views.queue,name='online-queue'),
]
