from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


def create_user(email="email@mysimpleapplication.com", password="User123!"):
    """Creates a sample user"""
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


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

    def test_tag_str(self):
        """Test the tag representation"""
        tag = models.Tag.objects.create(
            user=create_user(),
            name="Any Tag"
        )
        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """Test the ingredient string representation"""
        ingredient = models.Ingredient.objects.create(
            user=create_user(),
            name="Roast Beef"
        )

        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """Test recipe string representation"""
        recipe = models.Recipe.objects.create(
            user=create_user(),
            title="roast beef on honey mustard sauce",
            time_minutes=5,
            price=30.00
        )

        self.assertEqual(str(recipe), recipe.title)

    @patch("uuid.uuid4")
    def test_recipe_filename_uuid(self, mock_uuid):
        """Test if the image is begin saved in the correct location"""
        test_uuid = "test-uuid"
        mock_uuid.return_value = test_uuid
        file_path = models.recipe_image_file_path(None, "my-image.png")

        exp_path = f"upload/recipes/{test_uuid}.png"
        self.assertEqual(file_path, exp_path)
