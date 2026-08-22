from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class AccountsAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='alex_traveler',
            email='alex@example.com',
            password='Password123!',
            first_name='Alex',
            last_name='Sharma',
            city='Ahmedabad',
            country='India'
        )

    def test_avatar_letter(self):
        self.assertEqual(self.user.avatar_letter, 'A')
        user2 = User.objects.create_user(username='technicalcoderji', password='Password123!')
        self.assertEqual(user2.avatar_letter, 'T')

    def test_signup_view(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'Traveler',
            'email': 'new@example.com',
            'phone_number': '9876543210',
            'city': 'Dwarka',
            'country': 'India',
            'bio': 'Pilgrim and culture explorer',
            'password1': 'NewPassword123!',
            'password2': 'NewPassword123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_and_logout(self):
        response = self.client.post(reverse('login'), {
            'username': 'alex_traveler',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 302)

        logout_resp = self.client.get(reverse('logout'))
        self.assertEqual(logout_resp.status_code, 302)

    def test_profile_view_and_update(self):
        self.client.login(username='alex_traveler', password='Password123!')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

        update_resp = self.client.post(reverse('profile'), {
            'first_name': 'Alex Updated',
            'last_name': 'Sharma',
            'email': 'alex@example.com',
            'phone_number': '9998887776',
            'city': 'Rajkot',
            'country': 'India',
            'bio': 'Updated travel bio'
        })
        self.assertEqual(update_resp.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Alex Updated')
