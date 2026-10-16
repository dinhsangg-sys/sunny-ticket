from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import path
from apps.legacy import views
from apps.legacy.operations import operations, quote
urlpatterns = [path('admin/',admin.site.urls),path('login/',auth.LoginView.as_view(template_name='registration/login.html')),path('logout/',auth.LogoutView.as_view()),path('',views.home),path('api/state/',views.state),path('api/operations/',operations),path('api/quote/',quote),path('api/media/<str:key>/',views.media)]
