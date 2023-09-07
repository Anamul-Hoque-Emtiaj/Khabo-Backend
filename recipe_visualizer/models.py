# models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    image_path = models.ImageField(upload_to='user_images/',null=True, default=None)
    points = models.DecimalField(default=0,decimal_places=2,max_digits=10)
    registration_date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.get_full_name()

class Category(models.Model):  # Category of Ingredient
    name = models.CharField(max_length=100)
    details = models.TextField()

    def __str__(self):
        return self.name



class Brand(models.Model): # Brand of Ingredient
    name = models.CharField(max_length=100)
    details = models.TextField()

    def __str__(self):
        return self.name

class Ingredient(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True, default=None)
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class IngredientCategory(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

class Type(models.Model): # Type of Recipe
    name = models.CharField(max_length=100)
    details = models.TextField()

    def __str__(self):
        return self.name

class Recipe(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    recipe_image = models.ImageField(upload_to='recipe_images/',null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    making_time = models.CharField(max_length=50)
    is_valid = models.BooleanField(default=True)
    is_feature = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    def __str__(self):
        return self.title

class RecipeType(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    type = models.ForeignKey(Type, on_delete=models.CASCADE)

class Image(models.Model): # Image of Recipe-Step
    image_path = models.ImageField(upload_to='recipe_step_images/')
    descriptions = models.TextField()

class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    step_no = models.IntegerField()
    descriptions = models.TextField()


class StepImage(models.Model):
    step = models.ForeignKey(RecipeStep, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    serial_no = models.IntegerField()

class Search(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)

class Feedback(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=3, decimal_places=2)
    review_text = models.TextField()

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.CharField(max_length=50)
