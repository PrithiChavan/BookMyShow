from django.urls import path
from . import views

urlpatterns = [

    #Movie list & details
    path('', views.movie_list, name='movie_list'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('movie/<int:movie_id>/theaters/', views.theater_list, name='theater_list'),

    #Seat booking
    path('theater/<int:theater_id>/seats/book/', views.book_seats, name='book_seats'),

    #Mock payment
    path('payment/<int:theater_id>/', views.payment_page, name='payment_page'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),

    #Booking success
    path('booking-success/', views.booking_success, name='booking_success'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
