from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Tag, Recipe
from recipe.serializers import TagSerializer


TAGS_URL = reverse("recipe:tag-list")


def create_recipe(user, title):
    return Recipe.objects.create(
        title=title,
        time_minutes=10,
        price=5.00,
        user=user
    )


class PublicTagsApiTest(TestCase):
    """Tests the public methods of tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    """Tests the authenticated methods of tags API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="email@mysimpleapplication.com",
            password="Password123"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags"""
        Tag.objects.create(user=self.user, name="Tag 1")
        Tag.objects.create(user=self.user, name="Tag 2")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_belong_authenticated_user(self):
        diff_user = get_user_model().objects.create_user(
            "another_email@mysimpleapplication.com",
            "testpass"
        )
        Tag.objects.create(user=diff_user, name="Tag1")
        tag = Tag.objects.create(user=self.user, name="Tag2")

        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], tag.name)

    def test_create_tag_successful(self):
        """Test Creating a new tag"""
        payload = {"name": "Tag 1"}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload["name"]
        ).exists()

        self.assertTrue(exists)

    def test_create_invalid_tag(self):
        """test creating a tag with a invalid payload"""
        payload = {"name": ""}
        response = self.client.post(TAGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipe(self):
        """Test Retrieving tags that are assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name="Tag 1")
        tag2 = Tag.objects.create(user=self.user, name="Tag 2")
        recipe = create_recipe(self.user, "Recipe 1")
        recipe.tags.add(tag1)

        response = self.client.get(TAGS_URL, {"assigned_only": 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_retrieve_tags_assigned_unique(self):
        """test filtering returns non duplicate assigned tags"""
        tag = Tag.objects.create(user=self.user, name="Tag 1")
        Tag.objects.create(user=self.user, name="Tag 2")
        recipe1 = create_recipe(self.user, "Recipe 1")
        recipe1.tags.add(tag)

        recipe2 = create_recipe(self.user, "Recipe 2")
        recipe2.tags.add(tag)

        response = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(len(response.data), 1)
