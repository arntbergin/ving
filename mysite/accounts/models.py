from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Overstyr email-feltet: krevet og unikt
    email = models.EmailField('E-postadresse', unique=True)

    # Angi at e-post skal brukes som brukernavn ved login
    USERNAME_FIELD = 'email'
    # Felt som alltid kreves av create_user()
    REQUIRED_FIELDS = ['username']

    def __str__(self) -> str:
        return self.email