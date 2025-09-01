from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

class AuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='arnt', password='hemmelig123')
        self.client = Client()

    def test_login_success(self):
        self.assertTrue(self.client.login(username='arnt', password='hemmelig123'))
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        # 1. Logg inn
        self.client.login(username='arnt', password='hemmelig123')

        # 2. POST til logout-URLen
        response = self.client.post(reverse('logout'))

        # 3. Sjekk at vi får redirect (302) til login-siden
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])