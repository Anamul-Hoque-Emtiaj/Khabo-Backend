from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home_page'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('profile/<int:pk>/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/update/', views.UpdateProfileView.as_view(), name='update_profile'),
    path('profile/update_password/', views.UpdatePasswordView.as_view(), name='update_password'),
    path('recipes/', views.RecipeListView.as_view(), name='recipe_list'),
    path('recipes/<int:pk>/', views.RecipeDetailsView.as_view(), name='recipe_details'),
    path('recipes/add/', views.AddRecipeView.as_view(), name='add_recipe'),
    path('recipes/search_by_ingredients/', views.SearchByIngredientsView.as_view(), name='search_by_ingredients'),
    path('recipes/search_by_description/', views.SearchByDescriptionView.as_view(), name='search_by_description'),
    path('recipes/<int:recipe_id>/feedback/', views.GiveFeedbackView.as_view(), name='give_feedback'),
    path('logout/', views.logout, name='logout'),
    path('recipes/<int:pk>/update/', views.UpdateRecipeView.as_view(), name='recipe-update'),
    path('recipes/<int:pk>/delete/', views.RecipeDeleteView.as_view(), name='recipe-delete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
