"""
Tests for tags API.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer


def get_url(tag_id=0):
    if tag_id:
        return reverse('recipe:tag-detail', args=[tag_id])
    return reverse('recipe:tag-list')

# TAGS_URL = reverse('recipe:tag-list')

# def detail_url(tag_id):
#     """Create and return tag detail url."""
#     return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='test@example.com', password='Testpass1234'):
    """Create and return a user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def SetUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags."""

        res = self.client.get(get_url())

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiClient(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(get_url())

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_list_limited_to_user(self):
        """Test list of tags is limited for authenticated user."""
        other_user = create_user(
            email='other_user@test.com',
            password='Otherpass1234'
            )

        Tag.objects.create(user=self.user, name='Salad')
        Tag.objects.create(user=other_user, name='Fruity')

        res = self.client.get(get_url())

        tags = Tag.objects.filter(user=self.user)
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_update_tag(self):
        """Test updating tags."""
        tag = Tag.objects.create(user=self.user, name='After Dinner')

        payload = {'name': 'Dessert'}
        url = get_url(tag.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test deleting tags."""
        tag = Tag.objects.create(user=self.user, name='After Dinner')
        url = get_url(tag.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())
