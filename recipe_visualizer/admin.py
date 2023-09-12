from django.contrib import admin
from .models import (
    CustomUser,
    Category,
    IngredientCategory,
    Brand,
    Ingredient,
    Type,
    Recipe,
    RecipeType,
    Image,
    RecipeStep,
    StepImage,
    Search,
    Feedback,
    RecipeIngredient,
    Tag,
    RecipeTag
)

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Category)
admin.site.register(IngredientCategory)
admin.site.register(Brand)
admin.site.register(Ingredient)
admin.site.register(Type)
admin.site.register(Recipe)
admin.site.register(RecipeType)
admin.site.register(Image)
admin.site.register(RecipeStep)
admin.site.register(StepImage)
admin.site.register(Search)
admin.site.register(Feedback)
admin.site.register(RecipeIngredient)
admin.site.register(Tag)
admin.site.register(RecipeTag)
