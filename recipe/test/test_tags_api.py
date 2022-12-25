"""
test for tags api
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase


from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Tag,
    Recipe,
)
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-lits')

def details_url(tag_id):
    """create and return url"""
    return reverse('tag:tag-detail',args=['tag_id'])

def create_user(email='user@example.com', password='testpass123'):
    """create and return user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagApiTests(TestCase):
    """test for unauthenticated api request"""
    def setUp(self):
        self.client = APIClient()
    def test_auth_required(self):
        """test auth is required for retriving tags"""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code,status.HTTP_401_UNAUTHORIZED)

class PrivateTagApiTEst(TestCase):
    """test for authenticated api request"""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_tags_retrive(self):
        """test for retrieving a tag list"""
        Tag.objects.create(user=self.user, name='vegan')
        Tag.objects.create(user=self.user, name='dessert')

        res =  self.client.get(TAGS_URL)

        tags =Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,serializer.data)

    def test_tags_limited_user(self):
        """test list of tag for limited to authenticate user."""
        user2 =create_user(email = 'user2@example.com')
        Tag.objects.create(user=user2,name='fruity')
        tag =Tag.objects.create(user=self.user, name='comfort-food')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data),1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """test updating a tag"""
        tag = Tag.objects.create(user=self.user,name='after-dinner')

        payload={'nmae':'Dessert'}
        url = details_url(tag.id)
        res = self.client.patch(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """test delete a tag"""

        tag = Tag.objects.create(user=self.user, name='Breakfast')

        url = details_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_those_assig_in_recipe(self):
        """test listing tags those assign recipe"""
        tag1 = Tag.objects.create(user = self.user, name='Breakfast')
        tag2 = Tag.objects.create(user = self.user, name='Lunch')
        recipe = Recipe.objects.create(
            title = 'Bread Omlate',
            time_minutes=10,
            price = Decimal(20.00),
            user = self.user,
        )

        recipe.tags.add(tag1)
        res = self.client.get(TAGS_URL, {'assigned_only':1})
        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)
    def test_filter_tags_unique(self):
        """test filtering tag those return unique list"""
        tag1 = Tag.objects.create(user=self.user, name='Dinner')
        Tag.objects.create(user=self.user, name='Snack')

        recipe1 = Recipe.objects.create(
            title = 'Butter Paneer',
            time_minutes = 45,
            price = Decimal(250.0),
            user = self.user,
        )

        recipe2 = Recipe.objects.create(
            title = 'Pasta',
            time_minutes = 30,
            price = Decimal(45.0),
            user = self.user,
        )
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag1)
        res = self.client.get(TAGS_URL, {'assigned_only':1 })
        self.assertEqual(len(res.data), 1)


























