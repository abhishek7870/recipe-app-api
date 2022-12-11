"""
upl mapping for recipe api
"""
from django.urls import(
    path,
    include
)
from recipe import views

from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('recipe',views.RecipeViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
]

