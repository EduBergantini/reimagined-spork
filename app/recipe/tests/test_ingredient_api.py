from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def create_recipe(user, title):
    return Recipe.objects.create(
        title=title,
        time_minutes=10,
        price=5.00,
        user=user
    )


class PublicIngredientApiTests(TestCase):
    """Test publicly avaliable ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        response = self.client.get(INGREDIENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test private avaliable ingredients API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="user@mysimpleapplication.com",
            password="test-password",
            name="User"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """Test retrieving a list of ingredients"""
        Ingredient.objects.create(user=self.user, name="Ingredient 1")
        Ingredient.objects.create(user=self.user, name="Ingredient 2")

        response = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_ingredient_belongs_authenticated_user(self):
        """Test ingredient belongs to the authenticated user"""
        diff_user = get_user_model().objects.create_user(
            email="email_2@mysimpleapplication.com",
            password="test-pass-2",
            name="User 2"
        )
        ingredient = Ingredient.objects.create(
            user=self.user,
            name="Ingredient 1"
        )
        Ingredient.objects.create(user=diff_user, name="Ingredient 2")
        Ingredient.objects.create(user=diff_user, name="Ingredient 3")

        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], ingredient.name)

    def test_create_ingredient_successful(self):
        """Test creating a new ingredient"""
        payload = {"name": "Ingredient 1"}
        response = self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload["name"]
        ).exists()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(exists)

    def test_create_invalid_ingredient(self):
        """Test cannot create invalid ingredient"""
        payload = {"name": ""}
        response = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipe(self):
        """Test Retrieving Ingredients that are assigned to recipes"""
        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name="Ingredient 1"
        )
        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name="Ingredient 2"
        )
        recipe = create_recipe(self.user, "Recipe 1")
        recipe.ingredients.add(ingredient1)

        response = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_retrieve_ingredients_assigned_unique(self):
        """test filtering returns non duplicate assigned Ingredients"""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name="Ingredient 1"
        )
        Ingredient.objects.create(user=self.user, name="Ingredient 2")
        recipe1 = create_recipe(self.user, "Recipe 1")
        recipe1.ingredients.add(ingredient)

        recipe2 = create_recipe(self.user, "Recipe 2")
        recipe2.ingredients.add(ingredient)

        response = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertEqual(len(response.data), 1)
