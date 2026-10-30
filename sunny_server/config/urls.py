from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import path
from apps.legacy import views
from apps.legacy import sepay
from apps.legacy.counter import counter_page, counter_api
from apps.legacy.counter_details import booking_detail
from apps.legacy.counter_payment import confirm_payment
from apps.legacy.counter_email_template import email_template_page, email_template_api
from apps.legacy.counter_tickets import replace_tickets, reread_tickets
from apps.legacy.counter_report import report_page, report_api, report_detail, report_file
from apps.legacy.counter_tickets import booking_tickets, ticket_qr, generate_tickets, tickets_pdf, email_tickets, email_draft
from apps.legacy.operations import operations, quote
from apps.legacy.copy_prices import copy_prices
from apps.legacy.bulk_receipts import bulk_receipts, bulk_supplier_payments
urlpatterns = [path('api/sepay/webhook/',sepay.webhook),path('pay/sepay/',sepay.customer_page),path('api/sepay/display/',sepay.display_status),path('api/counter/bookings/<str:booking_id>/sepay/',sepay.create_intent),path('api/counter/sepay/intents/<uuid:intent_id>/',sepay.staff_intent),path('api/counter/ticket-batches/<uuid:batch_id>/email-draft/',email_draft),path('counter/email-template/',email_template_page),path('api/counter/email-template/',email_template_api),path('api/counter/bookings/<str:booking_id>/confirm-payment/',confirm_payment),path('api/counter/ticket-batches/<uuid:batch_id>/reread/',reread_tickets),path('api/counter/bookings/<str:booking_id>/',booking_detail),path('api/counter/ticket-batches/<uuid:batch_id>/replace/',replace_tickets),path('counter/report/',report_page),path('api/counter/report/',report_api),path('api/counter/report/<uuid:batch_id>/',report_detail),path('api/counter/report/<uuid:batch_id>/file/',report_file),path('api/counter/<str:booking_id>/tickets/',booking_tickets),path('api/counter/ticket-batches/<uuid:batch_id>/qr/<int:page>/',ticket_qr),path('api/counter/ticket-batches/<uuid:batch_id>/generate/',generate_tickets),path('api/counter/ticket-batches/<uuid:batch_id>/pdf/',tickets_pdf),path('api/counter/ticket-batches/<uuid:batch_id>/email/',email_tickets),path('counter/',counter_page,name='counter-page'),path('api/counter/',counter_api),path('api/bulk-supplier-payments/',bulk_supplier_payments),path('api/bulk-receipts/',bulk_receipts),path('admin/',admin.site.urls),path('login/',auth.LoginView.as_view(template_name='registration/login.html')),path('logout/',auth.LogoutView.as_view()),path('',views.home),path('api/state/',views.state),path('api/operations/',operations),path('api/copy-prices/',copy_prices),path('api/quote/',quote),path('api/media/<str:key>/',views.media)]
