from django.urls import path
from .views import ArticleDetailView, ArticleListView, home, page_detail, robots_txt, sitemap_xml

urlpatterns = [
    path('', home, name='home'),
    path('robots.txt', robots_txt, name='robots-txt'),
    path('sitemap.xml', sitemap_xml, name='sitemap-xml'),
    path('articles/', ArticleListView.as_view(), name='article-list'),
    path('articles/<slug:slug>/', ArticleDetailView.as_view(), name='article-detail'),
    path('<slug:slug>/', page_detail, name='page-detail'),
]
