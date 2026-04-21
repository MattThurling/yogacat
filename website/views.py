from django.db import models
from django.db.models import Prefetch
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .models import Article, Page, PageSection, SectionItem


RESERVED_SLUGS = {"admin", "login", "logout", "articles", "health", "sitemap.xml", "robots.txt"}


def is_preview_request(request):
  return request.user.is_staff and request.GET.get("preview") == "1"


def published_filter(queryset):
  now = timezone.now()
  return queryset.filter(published=True).filter(
    models.Q(published_at__isnull=True) | models.Q(published_at__lte=now)
  )


def page_queryset(preview=False):
  section_qs = PageSection.objects.select_related(
    "primary_cta_page",
    "secondary_cta_page",
    "reusable_cta",
    "reusable_cta__primary_page",
    "reusable_cta__secondary_page",
  ).order_by("sort_order", "id")
  item_qs = SectionItem.objects.select_related("link_page").order_by("sort_order", "id")

  if not preview:
    section_qs = section_qs.filter(visible=True)
    item_qs = item_qs.filter(visible=True)

  qs = Page.objects.prefetch_related(
    Prefetch("sections", queryset=section_qs),
    Prefetch("sections__items", queryset=item_qs),
  )
  return qs if preview else published_filter(qs)


def render_page(request, page):
  return render(request, page.template_name, {"page": page, "is_preview": is_preview_request(request)})


def home(request):
  page = page_queryset(is_preview_request(request)).filter(is_homepage=True).first()
  if not page:
    raise Http404("Homepage not found")
  return render_page(request, page)


def page_detail(request, slug):
  if slug in RESERVED_SLUGS:
    raise Http404("Page not found")
  page = get_object_or_404(page_queryset(is_preview_request(request)), slug=slug)
  return render_page(request, page)


def robots_txt(request):
  sitemap_url = request.build_absolute_uri("/sitemap.xml")
  body = f"User-agent: *\nAllow: /\nSitemap: {sitemap_url}\n"
  return HttpResponse(body, content_type="text/plain")


def sitemap_xml(request):
  pages = published_filter(Page.objects.all()).order_by("-is_homepage", "sort_order", "title")
  articles = published_filter(Article.objects.all()).order_by("-published_at", "-created_at")
  lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
  ]
  for page in pages:
    lines.extend([
      "  <url>",
      f"    <loc>{request.build_absolute_uri(page.get_absolute_url())}</loc>",
      f"    <lastmod>{page.updated_at.date().isoformat()}</lastmod>",
      "  </url>",
    ])
  for article in articles:
    lines.extend([
      "  <url>",
      f"    <loc>{request.build_absolute_uri(article.get_absolute_url())}</loc>",
      f"    <lastmod>{article.updated_at.date().isoformat()}</lastmod>",
      "  </url>",
    ])
  lines.append("</urlset>")
  return HttpResponse("\n".join(lines), content_type="application/xml")


class ArticleDetailView(DetailView):
  model = Article
  template_name = "articles/detail.html"
  slug_field = "slug"
  slug_url_kwarg = "slug"

  def get_object(self, queryset=None):
    obj = super().get_object(queryset)
    if not is_preview_request(self.request):
      if not obj.published or (obj.published_at and obj.published_at > timezone.now()):
        raise Http404("Article not found")
    return obj


class ArticleListView(ListView):
  model = Article
  template_name = "articles/list.html"
  paginate_by = 10

  def get_queryset(self):
    return published_filter(Article.objects.all()).order_by("-published_at", "-created_at")
