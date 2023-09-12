import csv
import os
import ast
from ..recipe_visualizer.models import Recipe, Ingredient, RecipeIngredient, Tag, RecipeTag, RecipeStep

# Define the path to your CSV file
csv_file = 'final_dataset.csv'

# Assuming your images are located in a folder named 'rimg'
image_folder = 'rimg'

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
    
    for row in csv_reader:
        # Create a Recipe instance
        recipe = Recipe.objects.create(
            title=row['title'],
            description=row['description'],
            making_time=row['minutes']+"minutes",
            recipe_image=os.path.join(image_folder, f"{row['image_path']}.PNG"),
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

print("Data import completed.")
