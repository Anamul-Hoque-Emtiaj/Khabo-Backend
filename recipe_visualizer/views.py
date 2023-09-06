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
    UserRecipe,
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
    UserRecipeSerializer,
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

    def retrieve(self, request, user_id, *args, **kwargs):
        instance = get_object_or_404(self.queryset, pk=user_id)  # Get the user by user_id or return a 404 if not found
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

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

    
    def get_queryset(self):
        return super().get_queryset()

class RecipeDetailsView(generics.RetrieveAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    lookup_field = 'recipe_id'  # Use 'recipe_id' as the lookup field

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()  # Get the recipe object
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class AddRecipeView(generics.CreateAPIView):
    serializer_class = RecipeSerializer

    # Implement your add recipe logic here

class SearchByIngredientsView(generics.ListAPIView):
    serializer_class = RecipeSerializer

    # Implement your search by ingredients logic here

class SearchByDescriptionView(generics.ListAPIView):
    serializer_class = RecipeSerializer

    # Implement your search by description logic here

class GiveFeedbackView(generics.CreateAPIView):
    serializer_class = FeedbackSerializer

    # Implement your give feedback logic here
