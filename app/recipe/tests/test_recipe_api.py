import tempfile
import os

from PIL import Image
from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse("recipe:recipe-list")


def image_upload_url(recipe_id):
    """return URL for recipe image upload"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def get_detail_url(recipe_id):
    """Return the recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **params):
    """Creates and return a recipe"""
    defaults = {
        "title": "Recipe Title",
        "time_minutes": 10,
        "price": 5.00
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


def create_tag(user, name="Tag"):
    """Creates and return a tag"""
    return Tag.objects.create(user=user, name=name)


def create_ingredient(user, name="Ingredient"):
    """Creates and return a ingredient"""
    return Ingredient.objects.create(user=user, name=name)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test required authentication"""
        response = self.client.get(RECIPES_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
                email="user@mysimpleapplication.com",
                password="test-password",
                name="User"
            )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """test retrieving recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipes_limited_user(self):
        """Test recipes belong to the authenticated user"""
        user2 = get_user_model().objects.create_user(
            email="user2@mysimpleapplication.com",
            password="test2-password",
            name="User2"
        )
        create_recipe(user=self.user)
        create_recipe(user=user2)
        create_recipe(user=user2)

        response = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)

    def test_detail_recipe_view(self):
        """test retrieving the recipe detail"""
        recipe = create_recipe(user=self.user)
        recipe.tags.add(create_tag(user=self.user))
        recipe.ingredients.add(create_ingredient(self.user))

        detail_url = get_detail_url(recipe.id)
        response = self.client.get(detail_url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(response.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating a basic recipe"""
        payload = {
            "title": "Recipe's title",
            "time_minutes": 30,
            "price": 5.00
        }
        response = self.client.post(RECIPES_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        tag1 = create_tag(user=self.user, name="User Tag 1")
        tag2 = create_tag(user=self.user, name="User Tag 2")
        payload = {
            "title": "Recipe with tags",
            "tags": [tag1.id, tag2.id],
            "time_minutes": 30,
            "price": 5.00
        }
        response = self.client.post(RECIPES_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data["id"])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_tag_with_ingredient(self):
        """Create a recipe with ingredients"""
        ingredient1 = create_ingredient(user=self.user, name="Ingredient 1")
        ingredient2 = create_ingredient(user=self.user, name="Ingredient 2")
        payload = {
            "title": "Recipe with ingredients",
            "ingredients": [ingredient1.id, ingredient2.id],
            "time_minutes": 20,
            "price": 7.00
        }
        response = self.client.post(RECIPES_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data["id"])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        """Test updating a recipe with PATCH"""
        recipe = create_recipe(user=self.user)
        recipe.tags.add(create_tag(user=self.user))
        new_tag = create_tag(user=self.user, name="Updated Tag")

        payload = {
            "title": "Updated Title PATCH",
            "tags": [new_tag.id]
        }

        url = get_detail_url(recipe.id)
        response = self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload["title"])

        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        recipe = create_recipe(user=self.user)
        recipe.tags.add(create_tag(user=self.user))
        payload = {
            "title": "Updated title PUT",
            "time_minutes": 25,
            "price": 23.00
        }
        url = get_detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.time_minutes, payload["time_minutes"])
        self.assertEqual(recipe.price, payload["price"])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)

    def filter_recipe_by_tags(self):
        """test filtering recipes by tags"""
        recipe1 = create_recipe(user=self.user, title="Recipe 1")
        tag1 = create_tag(user=self.user, name="Tag 1")
        recipe1.tags.add(tag1)
        recipe2 = create_recipe(user=self.user, title="Recipe 2")
        tag2 = create_tag(user=self.user, name="Tag 2")
        recipe2.tags.add(tag2)
        recipe3 = create_recipe(user=self.user, title="Recipe 3")

        response = self.client.get(
            RECIPES_URL,
            {"tags": f"{tag1.id},{tag2.id}"}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)

    def test_filtering_recipes_by_ingredients(self):
        """Test Filtering Recipes by Ingredients"""
        recipe1 = create_recipe(user=self.user, title="Recipe 1")
        ingredient1 = create_ingredient(self.user, name="Ingredient 1")
        recipe1.ingredients.add(ingredient1)
        serializer1 = RecipeSerializer(recipe1)

        recipe2 = create_recipe(user=self.user, title="Recipe 2")
        ingredient2 = create_ingredient(self.user, name="Ingredient 2")
        recipe2.ingredients.add(ingredient2)
        serializer2 = RecipeSerializer(recipe2)

        recipe3 = create_recipe(user=self.user, title="Recipe 3")
        serializer3 = RecipeSerializer(recipe3)

        response = self.client.get(
            RECIPES_URL,
            {"ingredients": f"{ingredient1.id},{ingredient2.id}"}
        )

        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)


class RecipeImageUploadTest(TestCase):
    """pass"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@mysimpleapplication.com",
            password="test-password",
            name="User"
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading an image to the recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            rsp = self.client.post(url, {"image": ntf}, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(rsp.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("image", rsp.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_upload_url(self.recipe.id)
        rsp = self.client.post(url, {"image": "no-image"}, format="multipart")

        self.assertEqual(rsp.status_code, status.HTTP_400_BAD_REQUEST)
