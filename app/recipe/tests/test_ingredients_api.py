"""
Tests for ingredients API.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def get_url(ingredient_id=0):
    """Return list or detail url for ingredients."""
    if ingredient_id:
        return reverse('recipe:ingredient-detail', args=[ingredient_id])
    return reverse('recipe:ingredient-list')


def create_user(email='example@test.com', password='Testpass1234'):
    """Creating and return a user"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsApiClient(TestCase):
    """Test unauthinticated API requests."""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication is required for retrieving ingredients."""

        res = self.client.get(get_url())

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiClient(TestCase):
    """Test authenticated API requests."""
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients."""
        Ingredient.objects.create(user=self.user, name='Ingredient1')
        Ingredient.objects.create(user=self.user, name='Ingredient2')

        res = self.client.get(get_url())

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_list_limited_to_user(self):
        """Test list of ingredients is limited for authenticated user."""
        other_user = create_user(
            email='user2@example.com',
            password='Anotherpass123'
            )

        Ingredient.objects.create(user=other_user, name='Ingredient2')
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Ingredient1'
            )

        res = self.client.get(get_url())

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredients(self):
        """Test updating ingredients."""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Ingredient1'
            )

        url = get_url(ingredient.id)
        payload = {'name': 'Ingredient2'}

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """Test deleting ingredients."""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Ingredient1'
            )
        url = get_url(ingredient.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())
