"""Tests for model """
from unittest.mock import patch
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models

def create_user(email='user@exmple.com',password='textpass123'):
    """create and return user"""
    return get_user_model().objects.create_user(email,password)

class ModelTests(TestCase):
    """Tests Models"""

    def test_create_user_with_email_successfull(self):
        """test creating a user with a email is successfull"""
        email = 'testexample@gmail.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test new user email normalized"""
        sample_email = [
            'test1@EMAMPLE.com', 'test1@example.com',
            'Test2@Example.com', 'Test2@example.com',
            'TEST3@EXAMPLE.COM', 'TEST3@example.com',
            'test4@example.COM', 'test4@example.com',
        ]
        for email, expected in sample_email:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """test that creating a user without an email raises a VlueError"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        """Test for creating a super user"""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123',
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """test for creating recipe successfull"""
        user = create_user()
        recipe = models.Recipe.object.create(
            user = user,
            title = 'sample recipe name',
            time_minutes=5,
            price = Decimal(5.5),
            description = 'sample recipe description',
        )
        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """test for creating tag successfull"""
        user = create_user()
        tag = models.Tag.object.create(user=user,tag='tag1')

        self.assertEqual(str(tag),tag.name)

    def test_create_ingredient(self):
        """test for creating intredient successfull"""
        user = create_user()
        ingredient = models.Ingredient.create(user=user, ingredient='paneer')

        self.assertEqual(str(ingredient),ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self):
        """test generating image path"""
        uuid ='test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')
        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')




