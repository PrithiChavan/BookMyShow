from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings

from .models import Movie, Theater, Seat, Booking, Genre, Language
from .utils import release_expired_seats
from django.utils import timezone


# =========================
# MOVIE LIST (SEARCH + FILTER)
# =========================
def movie_list(request):
    search_query = request.GET.get('search')
    genre_id = request.GET.get('genre')
    language_id = request.GET.get('language')

    movies = Movie.objects.all()

    if search_query:
        movies = movies.filter(name__icontains=search_query)

    if genre_id:
        movies = movies.filter(genres__id=genre_id)

    if language_id:
        movies = movies.filter(languages__id=language_id)

    context = {
        'movies': movies,
        'genres': Genre.objects.all(),
        'languages': Language.objects.all(),
        'search_query': search_query,
    }
    return render(request, 'movies/movie_list.html', context)


# =========================
# MOVIE DETAIL (WITH TRAILER)
# =========================
def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    return render(request, 'movies/movie_detail.html', {'movie': movie})


# =========================
# THEATER LIST
# =========================
def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    theaters = Theater.objects.filter(movie=movie)
    return render(request, 'movies/theater_list.html', {
        'movie': movie,
        'theaters': theaters
    })


# =========================
# SEAT SELECTION (NO BOOKING HERE)
# =========================
@login_required(login_url='/login/')
def book_seats(request, theater_id):
    theater = get_object_or_404(Theater, id=theater_id)

    #Release expired reservations
    release_expired_seats()

    seats = Seat.objects.filter(theater=theater)

    if request.method == 'POST':
        selected_seats = request.POST.getlist('seats')

        if not selected_seats:
            return render(request, 'movies/seat_selection.html', {
                'theaters': theater,
                'seats': seats,
                'error': 'Please select at least one seat'
            })

        #Reserve seats
        for seat_id in selected_seats:
            seat = get_object_or_404(Seat, id=seat_id, theater=theater)

            if seat.is_booked or seat.is_reserved:
                return render(request, 'movies/seat_selection.html', {
                    'theaters': theater,
                    'seats': seats,
                    'error': 'One or more seats are already reserved'
                })

            seat.is_reserved = True
            seat.reserved_at = timezone.now()
            seat.save()

        request.session['selected_seats'] = selected_seats
        request.session['theater_id'] = theater.id

        return redirect('payment_page', theater_id=theater.id)

    return render(request, 'movies/seat_selection.html', {
        'theaters': theater,
        'seats': seats
    })



# =========================
# MOCK PAYMENT PAGE
# =========================
@login_required(login_url='/login/')
def payment_page(request, theater_id):
    selected_seats = request.session.get('selected_seats')

    if not selected_seats:
        return redirect('movie_list')

    theater = get_object_or_404(Theater, id=theater_id)
    amount = len(selected_seats) * 200  # ₹200 per seat

    return render(request, 'movies/payment.html', {
        'theater': theater,
        'amount': amount
    })


# =========================
# PAYMENT SUCCESS (BOOK SEATS + EMAIL)
# =========================
@login_required
def payment_success(request):
    selected_seats = request.session.get('selected_seats')
    theater_id = request.session.get('theater_id')

    if not selected_seats or not theater_id:
        return redirect('movie_list')

    theater = get_object_or_404(Theater, id=theater_id)
    movie = theater.movie
    booked_numbers = []

    for seat_id in selected_seats:
        seat = get_object_or_404(Seat, id=seat_id, theater=theater)

        if seat.is_booked:
            continue

        Booking.objects.create(
            user=request.user,
            seat=seat,
            movie=movie,
            theater=theater
        )

        seat.is_booked = True
        seat.is_reserved = False
        seat.reserved_at = None
        seat.save()

        booked_numbers.append(seat.seat_number)

    # clear session
    del request.session['selected_seats']
    del request.session['theater_id']

    return redirect('booking_success')

# =========================
# PAYMENT FAILED
# =========================
@login_required(login_url='/login/')
def payment_failed(request):
    return render(request, 'movies/payment_failed.html')


# =========================
# BOOKING SUCCESS PAGE
# =========================
@login_required(login_url='/login/')
def booking_success(request):
    return render(request, 'movies/booking_success.html')
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
from .models import Booking, Movie, Theater

@staff_member_required
def admin_dashboard(request):

    total_revenue = Booking.objects.aggregate(
        total=Sum('price')
    )['total'] or 0

    total_bookings = Booking.objects.count()

    popular_movies = (
        Booking.objects
        .values('movie__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    busiest_theaters = (
        Booking.objects
        .values('theater__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    context = {
        'total_revenue': total_revenue,
        'total_bookings': total_bookings,
        'popular_movies': popular_movies,
        'busiest_theaters': busiest_theaters,
    }

    return render(request, 'movies/admin_dashboard.html', context)
