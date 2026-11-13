from django.urls import path
from . import views,sepay

urlpatterns=[path('api/orders/<uuid:key>/sepay/',sepay.intent_api),path('catalog/',views.catalog),path('p/<slug:slug>/',views.detail),path('assets/<uuid:key>/',views.media),path('manage/',views.management),path('products/new/',views.edit_product),path('products/<uuid:key>/edit/',views.edit_product),path('products/<uuid:key>/label/',views.qr_label),path('api/sales/',views.sales),path('api/orders/<uuid:key>/',views.order_action),path('api/report/',views.report)]
