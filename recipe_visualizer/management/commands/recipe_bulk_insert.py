from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from recipe_visualizer.models import Recipe, Ingredient, RecipeIngredient, Tag, RecipeTag, RecipeStep
import csv
import os
import ast

class Command(BaseCommand):
    help = 'Import data from CSV file'

    def handle(self, *args, **options):
        # Define the path to your CSV file
        csv_file = 'final_dataset.csv'

        # Assuming your images are located in a folder named 'rimg'
        image_folder = 'recipe_images'

        # Create a function to get or create an Ingredient instance
        def get_or_create_ingredient(name):
            ingredient, created = Ingredient.objects.get_or_create(name=name)
            return ingredient

        # Create a function to get or create a Tag instance
        def get_or_create_tag(name):
            tag_instance, created = Tag.objects.get_or_create(name=name)
            return tag_instance

        # Open and read the CSV file
        with open(csv_file, 'r', newline='') as file:
            csv_reader = csv.DictReader(file)
            admin_user = get_user_model().objects.get(username='scrapper_bot')
            for row in csv_reader:
                # Create a Recipe instance
                recipe = Recipe.objects.create(
                    title=row['title'],
                    description=row['description'],
                    making_time=row['minutes']+"minutes",
                    recipe_image=os.path.join(image_folder, f"{row['image_path']}-min.png"),
                    user=admin_user
                )
                
                # Create Ingredients and RecipeIngredients
                ingredients = ast.literal_eval(row['ingredients'])
                quantities = ast.literal_eval(row['quantities'])
                
                for ingredient_name, quantity in zip(ingredients, quantities):
                    ingredient = get_or_create_ingredient(ingredient_name)
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ingredient,
                        quantity=quantity
                    )
                
                # Create Tags and RecipeTags
                tags = ast.literal_eval(row['tags'])
                
                for tag_name in tags:
                    tag_instance = get_or_create_tag(tag_name)
                    RecipeTag.objects.create( 
                        recipe=recipe,
                        tag=tag_instance
                    )
                
                # Create Recipe Steps
                steps = ast.literal_eval(row['steps'])
                
                for step_number, description in enumerate(steps, start=1):
                    RecipeStep.objects.create(
                        recipe=recipe,
                        step_no=step_number,
                        descriptions=description
                    )

        self.stdout.write(self.style.SUCCESS('Data import completed.'))
