from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import path
from apps.legacy import views
from apps.legacy.counter import counter_page, counter_api
from apps.legacy.operations import operations, quote
from apps.legacy.copy_prices import copy_prices
from apps.legacy.bulk_receipts import bulk_receipts, bulk_supplier_payments
urlpatterns = [path('counter/',counter_page,name='counter-page'),path('api/counter/',counter_api),path('api/bulk-supplier-payments/',bulk_supplier_payments),path('api/bulk-receipts/',bulk_receipts),path('admin/',admin.site.urls),path('login/',auth.LoginView.as_view(template_name='registration/login.html')),path('logout/',auth.LogoutView.as_view()),path('',views.home),path('api/state/',views.state),path('api/operations/',operations),path('api/copy-prices/',copy_prices),path('api/quote/',quote),path('api/media/<str:key>/',views.media)]
