from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password,check_password
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login, logout as django_logout
from django.shortcuts import get_object_or_404
from django.db.models import Q
from fuzzywuzzy import fuzz
from django.utils import timezone
from decimal import Decimal
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema


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
    RecipeListSerializer,
    LoginSerializer,
    SignupSerializer,
    CreateFeedbackSerializer,
    AddRecipeSerializer,
    UpdateUserSerializer,
    UpdatePasswordSerializer,
    UserProfilesSerializer,
    SearchByDescriptionSerializer,
    SearchByIngredientsSerializer,
)

class HomePageView(generics.ListAPIView):
    queryset = Recipe.objects.filter(is_feature=True)
    serializer_class = RecipeListSerializer

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SignupView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = SignupSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check if the username is already taken
        username = serializer.validated_data['username']
        if get_user_model().objects.filter(username=username).exists():
            return Response({'error': 'Username is already taken.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the email is already taken
        email = serializer.validated_data['email']
        if get_user_model().objects.filter(email=email).exists():
            return Response({'error': 'Email is already taken.'}, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'user_id': serializer.instance.id}, status=status.HTTP_201_CREATED, headers=headers)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = get_user_model().objects.filter(username=username).first()

            if user is not None and check_password(password, user.password):
                # Password matches, log in the user
                django_login(request, user)
                return Response({'user': CustomUserSerializer(user).data}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    django_logout(request)
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

@extend_schema(responses=UserProfilesSerializer)
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
        if len(user_recipes)>0:
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
        recipe_serializer = RecipeListSerializer(user_recipes, many=True)

        # Create a response with both user data and user's added recipes
        response_data = serializer.data
        response_data['added_recipes'] = recipe_serializer.data

        return Response(response_data, status=status.HTTP_200_OK)


class UpdatePasswordView(generics.UpdateAPIView):
    serializer_class = UpdatePasswordSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response({
                'status': 'error',
                'message': 'Validation error',
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update the user's password
        user = self.request.user
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()

        return Response({
            'status': 'success',
            'message': 'Password updated successfully',
        }, status=status.HTTP_200_OK)


class UpdateProfileView(generics.UpdateAPIView):
    serializer_class = UpdateUserSerializer
    permission_classes = [IsAuthenticated]


    def update(self, request, *args, **kwargs):
        print(request.data)
        instance = self.request.user
        partial = kwargs.pop('partial', False)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # Save the updated information
        return Response({
            'status': 'success',
            'message': 'User profile updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    

class RecipeListView(generics.ListAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeListSerializer

    
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

        # Serialize recipe data
        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_200_OK) 



class AddRecipeView(generics.CreateAPIView):
    queryset = Recipe.objects.all()
    serializer_class = AddRecipeSerializer
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

@extend_schema(request=SearchByIngredientsSerializer,responses=RecipeListSerializer)
class SearchByIngredientsView(generics.ListAPIView):
    serializer_class = RecipeListSerializer

    def get_queryset(self):
        print(self.request.data)
        ingredient_names = self.request.data["ingredients"]
        print(ingredient_names)
        queryset = Recipe.objects.filter(is_valid=True)

        for ingredient in ingredient_names:
            queryset = queryset.filter(
                Q(ingredients__ingredient__name__icontains=ingredient) |
                Q(ingredients__ingredient__description__icontains=ingredient)
            )
        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

@extend_schema(request=SearchByDescriptionSerializer,responses=RecipeListSerializer)
class SearchByDescriptionView(generics.ListAPIView):
    serializer_class = RecipeListSerializer

    def get_queryset(self):
        description = self.request.data['description']
        print(description)
        # Filter recipes based on a similarity threshold
        queryset = Recipe.objects.filter(
            is_valid=True,
            description__isnull=False,
        ).filter(
            Q(title__icontains=description) |
            Q(description__icontains=description) |
            Q(description__isnull=False, description__icontains=description)
        ).order_by('-id')
        print(queryset)
        # Use fuzzywuzzy's fuzz.partial_ratio to compare descriptions
        # matching_recipes = []
        # for recipe in queryset:
        #     similarity = fuzz.partial_ratio(description.lower(), recipe.description.lower())
        #     # You can adjust the threshold (e.g., 80) as needed
        #     if similarity >= 60:
        #         matching_recipes.append(recipe)

        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

class GiveFeedbackView(generics.CreateAPIView):
    serializer_class = CreateFeedbackSerializer

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
