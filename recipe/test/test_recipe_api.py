"""
test recipe api
"""
from decimal import Decimal
import tempfile
import os
from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import(
    Recipe,
    Tag,
    Ingredient,
)
from recipe.serializers import(
    RecipeSerializer,
    RecipeDetailSerializer,
    IngredientSerilizer,
    )

RECIPE_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """create and return recipe details url"""
    return reverse('recipe:recipe-detail',args=[recipe_id])

def image_upload_url(recipe_id):
    """create and return recipe image url"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

def create_recipe(user **params):
    """create and return a sample recipe """
    defaults = {
        'title':'sample recipe title',
        'time_minute':22,
        'price':Decimal(5.3),
        'description':'sample recipe description',
        'link':'htt[://sample.com/recipe.pdf',
    }
    defaults.update(params)
    recipe =Recipe.objects.create(user=user,**defaults)
    return recipe

def create_user(**params):
    """create and return a new user"""
    return get_user_model().objects.create_user(**params)

class PublicRecipeApiTests(TestCase):
    """Test unauthenticated api request."""
    def setUp(self):
        self.client = APIClient()
    def test_auth_required(self):
        """test auth is required to call api"""
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code,status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeApiTests(TestCase):
    """test authenticated api request"""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='testpass123')
        self.client.force_authenticate(self.user)
    def test_retrive_recipe(self):
        """test retriving a list of recipe"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipe = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipe, maany=True)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """test list for recipe is limited to authenticated user"""
        other_user =create_user(email='user@example.com', password='testpass123')
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipe =Recipe.objects.filter(user=self.user)
        serialzer = RecipeSerializer(recipe, many =True)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,serialzer.data)


    def test_get_recipe_details(self):
        """test get recipe details"""
        recipe =create_recipe(user=self.user)

        url = detail_url(recipe_id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data,serializer.data)

    def test_create_recipe(self):
        """test creating a recipe"""

        payload = {
            'title':'sample recipe title',
            'time_minute':22,
            'price':Decimal(5.3),
        }

        res = self.client.post(RECIPE_URL,payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k,v in payload.items():
            self.assertEqual(getattr(recipe, k),v)
        self.assertEqual(recipe.user,self.user)
    def test_partial_update(self):
        """Test partial update of a recipe."""
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link=original_link,
        )

        payload = {'title': 'New recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update of recipe."""
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link='https://exmaple.com/recipe.pdf',
            description='Sample recipe description.',
        )

        payload = {
            'title': 'New recipe title',
            'link': 'https://example.com/new-recipe.pdf',
            'description': 'New recipe description',
            'time_minutes': 10,
            'price': Decimal('2.50'),
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the recipe user results in an error."""
        new_user = create_user(email='user2@example.com', password='test123')
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe successful."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self):
        """Test trying to delete another users recipe gives error."""
        new_user = create_user(email='user2@example.com', password='test123')
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """test create a recipe with new tags"""
        payload = {
            'title':'thai prawn curry',
            'time_minutes':30,
            'price':Decimal(5.6),
            'tags':[{'name':'Thai'},{'name':'dinner'}],
        }
        res = self.client.post(RECIPE_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name = tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)


    def test_create_racipe_with_existing_tag(self):
        """creating a recipe with tag is already exists"""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title':'pongal',
            'time_minute':32,
            'price':Decimal(4.5),
            'tags':[{'name':'Indian'},{'name':'Breakfast'}],
        }

        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertEqual(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name = tag['name'],
                user = self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating a tag when update the recipe"""
        recipe = create_recipe(user=self.user)

        payload = {'tag':[{'name':'lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url,payload,format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='lunch')
        self.assertEqual(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        tag_breakfast = Tag.objects.create(user=self.user,name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'name':[{'name':'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch,recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        tag =Tag.objects.create(user=self.user, name='Desert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags':[]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count, 0)

    def test_create_recipe_with_new_ingredient(self):
        """test recipe with new ingredient"""

        payload = {
            'name':'butter paneer',
            'time_minute':36,
            'price':Decimal(105.6),
            'ingredients':[{'name':'paneer'},{'name':'paneer masala'}],
        }

        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name = ingredient['name'],
                user = self.user,
            ).exists()
            self.assertTrue(exists)


    def test_create_recipe_with_existing_ingredient(self):
        """test for creating recipe with ingredient is already exist"""
        ind_ingredient = Ingredient.objects.create(user=self.user, name='Indian')
        payload = {
            'name':'chichek-tikka',
            'time_minute':36,
            'price':Decimal(236.5),
            'ingredients':[{'name':'Indian'},{'name':'chicken'},{'name':'capcicam'}],
        }

        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user = self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertEqual(ind_ingredient,recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name = ingredient['name'],
                user = self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """test creating a ingredient when update the recipe"""
        recipe = create_recipe(user = self.user)

        payload = {'ingredients':[{'name':'salt'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='salt')
        self.assertEqual(new_ingredient,recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe."""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Pepper')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='Chili')
        payload = {'ingredients': [{'name': 'Chili'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing a recipes ingredients."""
        ingredient = Ingredient.objects.create(user=self.user, name='Garlic')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {'ingredients': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
    def test_filter_by_tag(self):
        """filter recipe by tag"""
        r1 = create_recipe(user=self.user, title='butter paneer')
        r2 = create_recipe(user=self.user, title='chichen butter masala')
        tag1 = Tag.objects.create(user=self.user, name='dinner')
        tag2 = Tag.objects.create(User = self.user, name='lunch')
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title='chicken lalipop')

        params = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(RECIPE_URL, params)
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


    def test_filter_by_ingredient(self):
        """filter recipe by ingredient"""
        r1 = create_recipe(user=self.user, title='masur dal')
        r2 = create_recipe(user=self.user, title='bhindi fry')
        ing1 = Ingredient.objects.create(user=self.user, name='dal')
        ing2 =Ingredient.objects.create(user=self.user, name='masala')
        r1.ingredients.add(ing1)
        r2.ingredients.add(ing2)
        r3 = create_recipe(user=self.user, title='chicken kadai')
        parama = {'ingredients':f'{ing1.id},{ing2.id}'}
        res = self.client.get(RECIPE_URL, params)
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """Test for image upload api"""
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model.object.create_user(
            'user@example.com',
            'pass123'
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)
    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe."""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image."""
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)




















