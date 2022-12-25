"""
test for ingredient api
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Ingredient,
    Recipe,
)
from recipe.serializers import IngredientSerilizer

INGREDIENT_URL = reverse('recipe:ingredient-list')

def details_url(ingredient_id):
    """create and return """
    return reverse('recipe:ingredient-details',args=['ingredient_id'])

def create_user(email='user@example.com', password='testpass123'):
    """create and return user"""
    return get_user_model().objects.create_user(email=email, password=password)

class PublicIngredientApiTest(TestCase):
    """test for unauthenticated api tets"""
    def setUp(self):
        self.client = APIClient()
    def test_ingredient_list(self):
        """test for retriving ingredient of list"""
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateIngredientApiTest(TestCase):
    """test for authenticated api request"""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)
    def test_ingredient_list(self):
        """test for retriving ingredient of list"""
        Ingredient.objects.create(user=self.user, name='salt')
        Ingredient.objects.create(user=self.user, name='tomoto')

        res =  self.client.get(INGREDIENT_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerilizer(ingredients, many='True')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tag_limited_user(self):
        """test for retriving ingredient list for authenticated user """
        user2 =create_user(email='user2@example.com')
        Ingredient.objects.create(user=user2, name='potato')
        ingredient = Ingredient.objects.create(user=user2, name='cucumber')

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'],ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """test for updating the ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='tomato')

        payload = {'name':'tomato'}
        url = details_url(ingredient.id)
        res = self.client.patch(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name,payload['name'])

    def test_delete_ingredient(self):
        """test for deleting the ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='salt')

        url = details_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipe(self):
        """Test listing ingredients by those assigned to recipe"""
        ing1 = Ingredient.objects.create(user=self.user, name='egg')
        ing2 = Ingredient.objects.create(user=self.user, name='onion')

        recipe = Recipe.objects.create(
            title = 'Egg curry',
            time_minutes = 6,
            price = Decimal('63'),
            user = self.user,
        )
        recipe.ingredients.add(ing1)
        res = self.client.get(INGREDIENT_URL, {'assigned_only':1})
        s1 = IngredientSerilizer(ing1)
        s2 = IngredientSerilizer(ing2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):
        """test filtered ingredients return a unique list"""
        ing1 = Ingredient.objects.create(user = self.user, name='egg')
        Ingredient.objects.create(user=self.user, name='onion')
        recipe1 = Recipe.objects.create(
            title = 'Egg Curry',
            time_minutes = 30,
            price = Decimal('34.00'),
            user = self.user,
        )
        recipe2 = Recipe.objects.create(
            title = 'Egg Omlate',
            time_minutes= 14,
            price = Decimal('15.0'),
            user = self.user,
        )
        recipe1.ingredients.add(ing1)
        recipe2.ingredients.add(ing1)

        res = self.client.get(INGREDIENT_URL, {'assigned_only':1})
        self.assertEqual(len(res.data), 1)



























