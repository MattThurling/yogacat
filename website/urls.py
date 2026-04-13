from django.urls import path
from .views import home, ArticleDetailView, ArticleListView

urlpatterns = [
    path('', home, name='home'),
    path('articles/', ArticleListView.as_view(), name='article-list'),
    path('<slug:slug>/', ArticleDetailView.as_view(), name='article-detail'),
]
