from django.urls import path
from . import views,cart,fulfillment
from .weather import weather_api
urlpatterns=[path('checkout/now/',cart.checkout,{'direct':True},name='online-buy-now-checkout'),path('cart/',cart.page,name='online-cart'),path('cart/checkout/',cart.checkout,name='online-cart-checkout'),path('cart/orders/<uuid:key>/',cart.order_page,name='online-cart-order'),path('cart/orders/<uuid:key>/status/',cart.status,name='online-cart-status'),path('services/<slug:slug>/prices/',cart.prices,name='online-prices'),path('services/<slug:slug>/add/',cart.add,name='online-cart-add'),path('online/staff/cart/<uuid:key>/',fulfillment.process,name='online-cart-process'),path('online/staff/tickets/<int:key>/',fulfillment.ticket_file,name='online-order-ticket'),path('api/public/weather/',weather_api,name='online-weather'),
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
