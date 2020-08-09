from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Test creating a new user"""
        email = "email@gmail.com"
        password = "T3st_P4sSw0Rd@!"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for the new user is normalized"""
        email = "email@GMAIL.COM"
        user = get_user_model().objects.create_user(
            email=email,
            password="123Mudar"
        )
        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, "123Mudar")

    def test_create_new_useruser(self):
        """Test creating new super user"""
        user = get_user_model().objects.create_superuser(
            email="email@gmail.com",
            password="123Mudar"
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
