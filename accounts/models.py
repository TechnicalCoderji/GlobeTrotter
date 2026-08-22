from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username

    @property
    def avatar_letter(self):
        """Always derived dynamically from the first letter of username - not changeable by user."""
        if self.first_name:
            return self.first_name[0].upper()
        elif self.username:
            return self.username[0].upper()
        return 'T'