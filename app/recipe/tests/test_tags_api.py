from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Tag
from recipe.serializers import TagSerializer
import json


TAGS_URL = reverse("recipe:tag-list")


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
        # self.assertEqual(response.data[0]["name"], tag.name)
