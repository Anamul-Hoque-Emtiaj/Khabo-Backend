from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password,check_password
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login, logout as django_logout
from django.shortcuts import get_object_or_404
from django.db.models import Q
from fuzzywuzzy import fuzz
from django.utils import timezone
from decimal import Decimal


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
)
from .serializers import (
    CustomUserSerializer,
    CategorySerializer,
    IngredientCategorySerializer,
    BrandSerializer,
    IngredientSerializer,
    TypeSerializer,
    RecipeSerializer,
    RecipeTypeSerializer,
    ImageSerializer,
    RecipeStepSerializer,
    StepImageSerializer,
    SearchSerializer,
    FeedbackSerializer,
    RecipeIngredientSerializer,
)

class HomePageView(generics.ListAPIView):
    queryset = Recipe.objects.filter(is_feature=True)
    serializer_class = RecipeSerializer

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class SignupView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = CustomUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_data = serializer.validated_data
        password = user_data.pop('password')
        user_data['password'] = make_password(password)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response({'user_id': serializer.instance.id}, status=status.HTTP_201_CREATED, headers=headers)


class LoginView(generics.GenericAPIView):
    serializer_class = CustomUserSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            django_login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    django_logout(request)
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

class UserProfileView(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        # Get the user by their ID
        user = self.get_object()

        # Get recipes added by the user
        user_recipes = Recipe.objects.filter(user=user)

        # Calculate user's points based on the weighted sum
        user_points = Decimal(len(user_recipes) *2)
        total_recipe_rating = Decimal(0)
        # Calculate the weighted sum of recipe ratings
        for recipe in user_recipes:
            total_recipe_rating += Decimal(recipe.rating)
            
        user_points += (total_recipe_rating/len(user_recipes)) * Decimal(3)

        # Calculate the weighted sum based on user registration date
        current_date = timezone.now()
        registration_date = user.registration_date
        days_since_registration = (current_date - registration_date).days

        user_points += days_since_registration * Decimal(0.1)

        # Update the user's points and save
        user.points = user_points
        user.save()

        # Serialize user data
        serializer = self.get_serializer(user)

        # Serialize user's added recipes
        recipe_serializer = RecipeSerializer(user_recipes, many=True)

        # Create a response with both user data and user's added recipes
        response_data = serializer.data
        response_data['added_recipes'] = recipe_serializer.data

        return Response(response_data, status=status.HTTP_200_OK)

class UpdatePasswordView(generics.UpdateAPIView):
    queryset = get_user_model().objects.all()
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')  # Get the user_id from URL
        try:
            user = get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist:
            return Response({'message': 'User not found.'}, status=404)

        # Ensure the user making the request is the same as the user being updated
        if request.user != user:
            return Response({'message': 'Permission denied.'}, status=403)
        

        current_password = request.data.get('current_password', None)
        new_password = request.data.get('new_password', None)
        
        if not current_password or not new_password:
            return Response(
                {'message': 'Both current and new password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not check_password(current_password, user.password):
            return Response(
                {'message': 'Current password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password updated successfully.'}, status=status.HTTP_200_OK)


class UpdateProfileView(generics.UpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, user_id, *args, **kwargs):
        instance = get_object_or_404(self.queryset, pk=user_id)

        # Check if the request user is the owner of the profile
        if request.user.id != user_id:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to update this profile.'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'status': 'success',
            'message': 'User profile updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

class RecipeListView(generics.ListAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    
    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RecipeDetailsView(generics.RetrieveAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    

    def retrieve(self, request, *args, **kwargs):
        # Get the recipe by its ID
        recipe = self.get_object()

        # Get feedback for the recipe
        feedback = Feedback.objects.filter(recipe=recipe)

        # Get ingredients of the recipe
        ingredients = RecipeIngredient.objects.filter(recipe=recipe)

        # Get steps of the recipe
        steps = RecipeStep.objects.filter(recipe=recipe)

        # Get type of the recipe
        recipe_type = Type.objects.filter(recipetype__recipe=recipe)

        # Get step images for each step
        step_images = StepImage.objects.filter(step__recipe=recipe)

        # Get recipe owner (CustomUser) details
        owner = recipe.user

        # Serialize recipe data
        serializer = self.get_serializer(recipe)



        # Serialize feedback, ingredients, steps, type, and step images
        feedback_serializer = FeedbackSerializer(feedback, many=True)
        ingredients_serializer = RecipeIngredientSerializer(ingredients, many=True)
        steps_serializer = RecipeStepSerializer(steps, many=True)
        recipe_type_serializer = TypeSerializer(recipe_type, many=True)
        step_images_serializer = StepImageSerializer(step_images, many=True)
        owner_serializer = CustomUserSerializer(owner)

        # Create a response with all the data
        response_data = serializer.data
        response_data['feedback'] = feedback_serializer.data
        response_data['ingredients'] = ingredients_serializer.data
        response_data['steps'] = steps_serializer.data
        response_data['recipe_types'] = recipe_type_serializer.data
        response_data['owner'] = owner_serializer.data

        # Include step images inside corresponding steps
        for step_data in response_data['steps']:
            step_data['step_images'] = [img for img in step_images_serializer.data if img['step'] == step_data['id']]

        return Response(response_data, status=status.HTTP_200_OK) 



class AddRecipeView(generics.CreateAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Create the recipe
        recipe = serializer.save(user=self.request.user)

        # Process and save ingredients
        ingredients_data = self.request.data.get('ingredients', [])
        for ingredient_data in ingredients_data:
            ingredient_name = ingredient_data.get('name')
            ingredient, created = Ingredient.objects.get_or_create(name=ingredient_name)
            quantity = ingredient_data.get('quantity')
            RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, quantity=quantity)

        # Process and save recipe type
        recipe_type_data = self.request.data.get('recipe_type', {})
        type_name = recipe_type_data.get('name')
        recipe_type, created = Type.objects.get_or_create(name=type_name)
        RecipeType.objects.create(recipe=recipe, type=recipe_type)

        # Process and save recipe steps along with images
        steps_data = self.request.data.get('steps', [])
        for step_data in steps_data:
            step_serializer = RecipeStepSerializer(data=step_data)
            if step_serializer.is_valid():
                step = step_serializer.save(recipe=recipe)

                # Process and save step images
                step_images_data = step_data.get('step_images', [])
                for image_data in step_images_data:
                    image_serializer = ImageSerializer(data=image_data)
                    if image_serializer.is_valid():
                        image = image_serializer.save()
                        step_image = StepImage(step=step, image=image)
                        step_image.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SearchByIngredientsView(generics.ListAPIView):
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ingredient_names = self.request.query_params.getlist('ingredient')
        queryset = Recipe.objects.filter(is_valid=True)

        # Create a list of Q objects for ingredient name filtering
        ingredient_filters = [Q(recipeingredient__ingredient__name=ingredient) for ingredient in ingredient_names]

        # Combine the Q objects with OR operator
        if ingredient_filters:
            query = ingredient_filters.pop()
            for item in ingredient_filters:
                query |= item

            # Filter recipes based on ingredients
            queryset = queryset.filter(query)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SearchByDescriptionView(generics.ListAPIView):
    serializer_class = RecipeSerializer

    def get_queryset(self):
        description = self.request.query_params.get('description', '')

        # Filter recipes based on a similarity threshold
        queryset = Recipe.objects.filter(
            is_valid=True,
            description__isnull=False,
        ).filter(
            Q(description__icontains=description) |
            Q(description__isnull=False, description__icontains=description)
        ).order_by('-id')

        # Use fuzzywuzzy's fuzz.partial_ratio to compare descriptions
        matching_recipes = []
        for recipe in queryset:
            similarity = fuzz.partial_ratio(description.lower(), recipe.description.lower())
            # You can adjust the threshold (e.g., 80) as needed
            if similarity >= 60:
                matching_recipes.append(recipe)

        return matching_recipes

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GiveFeedbackView(generics.CreateAPIView):
    serializer_class = FeedbackSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        recipe_id = kwargs.get('recipe_id')
        rating = serializer.validated_data.get('rating')

        try:
            recipe = Recipe.objects.get(pk=recipe_id)
        except Recipe.DoesNotExist:
            return Response(
                {'detail': 'Recipe not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calculate the new average rating
        feedbacks = Feedback.objects.filter(recipe=recipe)
        total_rating = sum(feedback.rating for feedback in feedbacks) + rating
        new_rating = total_rating / (len(feedbacks) + 1)

        # Update the recipe's rating
        recipe.rating = new_rating
        recipe.save()

        # Create the feedback
        serializer.save(user=user, recipe=recipe)

        return Response(
            {'detail': 'Feedback submitted successfully.'},
            status=status.HTTP_201_CREATED
        )
