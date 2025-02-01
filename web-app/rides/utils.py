from django.core.mail import send_mail
from django.conf import settings

def send_ride_confirmation_email(ride):
    send_mail(
        'Your ride has been confirmed',
        f'Your ride to {ride.destination} has been confirmed by the driver.',
        settings.EMAIL_HOST_USER,
        [ride.owner.email],
        fail_silently=False,
    )

    for sharer in ride.sharers.all():
        send_mail(
            'Your ride has been confirmed',
            f'Your ride to {ride.destination} has been confirmed by the driver.',
            settings.EMAIL_HOST_USER,
            [sharer.user.email],
            fail_silently=False,
        )