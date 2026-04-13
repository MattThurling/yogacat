from django.shortcuts import render
from django.db import models
from django.utils import timezone
from django.views.generic import DetailView, ListView
from django.http import Http404
from .models import Article

RESERVED_SLUGS = {"admin", "login", "logout", "articles", "health", "sitemap.xml", "robots.txt"}

def home(request):
  return render(request, 'website/index.html')

class ArticleDetailView(DetailView):
  model = Article
  template_name = "articles/detail.html"
  slug_field = "slug"
  slug_url_kwarg = "slug"

  def get_object(self, queryset=None):
    slug = self.kwargs.get(self.slug_url_kwarg)
    if slug in RESERVED_SLUGS:
      raise Http404("Not an article")
    obj = super().get_object(queryset)
    # Public only if published and live
    is_preview = self.request.user.is_staff and self.request.GET.get("preview") == "1"
    if not is_preview:
      if not obj.published or (obj.published_at and obj.published_at > timezone.now()):
        raise Http404("Article not found")
    return obj


class ArticleListView(ListView):
  model = Article
  template_name = "articles/list.html"
  paginate_by = 10

  def get_queryset(self):
    now = timezone.now()
    return (
      Article.objects.filter(published=True)
      .filter(models.Q(published_at__isnull=True) | models.Q(published_at__lte=now))
      .order_by("-published_at", "-created_at")
    )
