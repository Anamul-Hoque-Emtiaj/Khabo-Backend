from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import CustomUser, Category, IngredientCategory, Brand, Ingredient, Type, Recipe, RecipeType, Image, RecipeStep, StepImage, Search, Feedback, RecipeIngredient

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'image_path', 'points', 'registration_date')

class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id','email', 'first_name', 'last_name', 'image_path')

    def validate_email(self, value):
        """
        Check that the email is unique.
        """
        user = self.instance
        if CustomUser.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("This email address is already in use. Please try another one.")
        return value


class UpdatePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate_current_password(self, value):
        """
        Check that the current password is correct.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("The current password is incorrect.")
        return value

    def validate(self, data):
        """
        Check that the new password and confirmation match.
        """
        new_password = data.get('new_password')
        confirm_new_password = data.get('confirm_new_password')

        if new_password != confirm_new_password:
            raise serializers.ValidationError("The new password and confirmation do not match.")
        
        return data

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class IngredientCategorySerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    class Meta:
        model = IngredientCategory
        fields = ('id', 'category')

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'

class IngredientSerializer(serializers.ModelSerializer):
    brand = BrandSerializer()
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'description', 'brand')

class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = '__all__'


class RecipeTypeSerializer(serializers.ModelSerializer):
    type = TypeSerializer()
    class Meta:
        model = RecipeType
        fields = ( 'id', 'type')

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = '__all__'



class StepImageSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    class Meta:
        model = StepImage
        fields = ('id', 'serial_no', 'image')

class RecipeStepSerializer(serializers.ModelSerializer):
    step_images = StepImageSerializer(many=True)
    class Meta:
        model = RecipeStep
        fields = ('id', 'step_no', 'descriptions', 'step_images')

class SearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Search
        fields = '__all__'

class FeedbackSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()  # Include the user information here
    class Meta:
        model = Feedback
        fields = ('id', 'rating', 'review_text', 'user')

class CreateFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ('id', 'rating', 'review_text')

class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer()
    class Meta:
        model = RecipeIngredient
        fields = ('id', 'ingredient', 'quantity')

class RecipeSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    feedback = FeedbackSerializer(many=True)
    ingredients = RecipeIngredientSerializer(many=True)
    steps = RecipeStepSerializer(many=True)
    recipe_types = RecipeTypeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('id', 'recipe_image', 'title', 'description', 'making_time', 'is_valid', 'is_feature', 'rating', 'user', 'feedback', 'ingredients', 'steps', 'recipe_types')
class AddRecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    steps = RecipeStepSerializer(many=True)
    recipe_types = RecipeTypeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('id', 'recipe_image', 'title', 'description', 'making_time', 'ingredients', 'steps', 'recipe_types')
class RecipeListSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    class Meta:
        model = Recipe
        fields = ('id', 'recipe_image', 'title', 'description', 'making_time', 'is_valid', 'is_feature', 'rating', 'user')
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})  

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not username:
            raise serializers.ValidationError("Username is required.")

        if not password:
            raise serializers.ValidationError("Password is required.")

        return data

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirmation = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password', 'password_confirmation', 'first_name', 'last_name')

    def validate(self, data):
        # Check if passwords match
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        # Remove password_confirmation field
        validated_data.pop('password_confirmation', None)
        # Hash the password
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class SearchByIngredientsSerializer(serializers.Serializer):
    ingredients = serializers.ListField(child=serializers.CharField())
    def validate(self, data):
        if len(data['ingredients']) < 1:
            raise serializers.ValidationError("Please select at least two ingredients.")
        return data
    
class SearchByDescriptionSerializer(serializers.Serializer):    
    description = serializers.CharField()
    def validate(self, data):
        if len(data['description']) < 1:
            raise serializers.ValidationError("Please enter a description.")
        return data
    
class UserProfilesSerializer(serializers.ModelSerializer):
    recipes = RecipeListSerializer(many=True)
    class Meta:
        model = CustomUser
        fields = ('id', 'username','email', 'first_name', 'last_name', 'image_path', 'points', 'registration_date', 'recipes')
