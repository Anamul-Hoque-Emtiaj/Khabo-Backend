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
    Tag,
    RecipeTag,
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
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')

# Define a list of stop words
stop_words = set(stopwords.words('english'))

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
    permission_classes = [IsAuthenticated]

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
        recipe_serializer = RecipeListSerializer(user_recipes, many=True, context={'request': request})	


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
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Create a new recipe instance
            recipe_image = serializer.validated_data.get('recipe_image')
            if recipe_image:
                recipe = Recipe.objects.create(
                    title=serializer.validated_data['title'],
                    description=serializer.validated_data['description'],
                    making_time=serializer.validated_data['making_time'],
                    recipe_image=recipe_image,
                    user=request.user  # Set the user to the authenticated user
                )
            else:
                recipe = Recipe.objects.create(
                    title=serializer.validated_data['title'],
                    description=serializer.validated_data['description'],
                    making_time=serializer.validated_data['making_time'],
                    user=request.user  # Set the user to the authenticated user
                )
            print(recipe)
            # Process and save ingredients
            ingredients_data = serializer.validated_data.get('ingredients', [])
            print(ingredients_data)
            for ingredient_data in ingredients_data:
                ingredient_name = ingredient_data.get('ingredient', {}).get('name')
                ingredient, created = Ingredient.objects.get_or_create(name=ingredient_name)
                quantity = ingredient_data.get('quantity')
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, quantity=quantity+" "+ingredient_name)

            # Process and save tags
            tags_data = serializer.validated_data.get('tags', [])
            print(tags_data)
            for tag_data in tags_data:
                tag_name = tag_data.get('tag', {}).get('name')
                tag, created = Tag.objects.get_or_create(name=tag_name)
                RecipeTag.objects.create(recipe=recipe, tag=tag)

            # Process and save steps along with images
            steps_data = serializer.validated_data.get('steps', [])
            print(steps_data)
            for step_data in steps_data:
                step = RecipeStep.objects.create(
                    recipe=recipe,
                    step_no=step_data.get('step_no'),
                    descriptions=step_data.get('descriptions')
                )
                if step_data.get('step_images'):
                    step_images_data = step_data.get('step_images', [])
                    for image_data in step_images_data:
                        image = Image.objects.create(
                            image_path=image_data.get('image', {}).get('image_path'),
                            descriptions=image_data.get('image', {}).get('descriptions')
                        )
                        StepImage.objects.create(step=step, image=image)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SearchByIngredientsView(generics.GenericAPIView):
    serializer_class = SearchByIngredientsSerializer
    queryset = Recipe.objects.all()   
    def post(self, request, *args, **kwargs):
        serializer = SearchByIngredientsSerializer(data=request.data)
        if serializer.is_valid():
            print(self.request.data)
            ingredient_names = serializer.validated_data["ingredients"]
            print(ingredient_names)
            queryset = Recipe.objects.filter(is_valid=True)

            for ingredient in ingredient_names:
                queryset = queryset.filter(
                    Q(ingredients__ingredient__name__icontains=ingredient) |
                    Q(ingredients__ingredient__description__icontains=ingredient)
                )
            queryset = queryset.order_by('-id').distinct()
            recipe_serializer = RecipeListSerializer(queryset, many=True, context={'request': request})
            return Response(recipe_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SearchByDescriptionView(generics.GenericAPIView):
    serializer_class = SearchByDescriptionSerializer
    queryset = Recipe.objects.all()   
    def post(self, request, *args, **kwargs):
        serializer = SearchByDescriptionSerializer(data=request.data)
        if serializer.is_valid():
            description = serializer.validated_data['description']
            print(description)
            
            # Tokenize the search query and remove stop words
            keywords = [word for word in description.split() if word.lower() not in stop_words]
            
            queryset = Recipe.objects.filter(
                is_valid=True,
                description__isnull=False,
            )
            for keyword in keywords:
                queryset = queryset.filter(
                    Q(title__icontains=keyword) |
                    Q(description__icontains=keyword) |
                    Q(tags__tag__name__icontains=keyword) |
                    Q(steps__descriptions__icontains=keyword)
                )
            queryset = queryset.order_by('-id').distinct()
        
            recipe_serializer = RecipeListSerializer(queryset, many=True, context={'request': request})
            return Response(recipe_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GiveFeedbackView(generics.CreateAPIView):
    serializer_class = CreateFeedbackSerializer
    permission_classes = [IsAuthenticated]

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
    


class UpdateRecipeView(generics.UpdateAPIView):
    queryset = Recipe.objects.all()
    serializer_class = AddRecipeSerializer  # Use the AddRecipeSerializer for update
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data, partial=True)

        if serializer.is_valid():
            # Update the recipe instance
            recipe.title = serializer.validated_data.get('title', recipe.title)
            recipe.description = serializer.validated_data.get('description', recipe.description)
            recipe.making_time = serializer.validated_data.get('making_time', recipe.making_time)
            
            # Update the recipe image if provided
            recipe_image = serializer.validated_data.get('recipe_image')
            if recipe_image:
                recipe.recipe_image = recipe_image
            
            recipe.save()

            # Process and update ingredients
            ingredients_data = serializer.validated_data.get('ingredients', [])
            RecipeIngredient.objects.filter(recipe=recipe).delete()  # Remove existing steps
            for ingredient_data in ingredients_data:
                ingredient_name = ingredient_data.get('ingredient', {}).get('name')
                ingredient, created = Ingredient.objects.get_or_create(name=ingredient_name)
                quantity = ingredient_data.get('quantity')
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, quantity=quantity)

            # Process and update tags
            tags_data = serializer.validated_data.get('tags', [])
            RecipeTag.objects.filter(recipe=recipe).delete()  # Remove existing tags

            for tag_data in tags_data:
                tag_name = tag_data.get('tag', {}).get('name')
                tag, created = Tag.objects.get_or_create(name=tag_name)
                RecipeTag.objects.create(recipe=recipe, tag=tag)

            # Process and update steps along with images
            steps_data = serializer.validated_data.get('steps', [])
            RecipeStep.objects.filter(recipe=recipe).delete()  # Remove existing steps
            for step_data in steps_data:
                step = RecipeStep.objects.create(
                    recipe=recipe,
                    step_no=step_data.get('step_no'),
                    descriptions=step_data.get('descriptions')
                )
                if step_data.get('step_images'):
                    step_images_data = step_data.get('step_images', [])
                    for image_data in step_images_data:
                        image = Image.objects.create(
                            image_path=image_data.get('image', {}).get('image_path'),
                            descriptions=image_data.get('image', {}).get('descriptions')
                        )
                        StepImage.objects.create(step=step, image=image)

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    
class RecipeDeleteView(generics.DestroyAPIView):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check if the user requesting the deletion is the owner of the recipe
        if instance.user != request.user:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to delete this recipe.'
            }, status=status.HTTP_403_FORBIDDEN)

        instance.delete()
        
        return Response({
            'status': 'success',
            'message': 'Recipe deleted successfully.'
        }, status=status.HTTP_204_NO_CONTENT)
    
class IngredientListView(generics.ListAPIView):	
    queryset = Ingredient.objects.all()	
    serializer_class = IngredientSerializer	
    def list(self, request, *args, **kwargs):	
        queryset = self.get_queryset()	
        serializer = self.get_serializer(queryset, many=True)	
        return Response(serializer.data)
