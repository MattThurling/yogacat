# admin.py
from django.contrib import admin
from django import forms
from django.utils import timezone
from tinymce.widgets import TinyMCE
from .models import Article


class ArticleAdminForm(forms.ModelForm):
  class Meta:
    model = Article
    fields = "__all__"
    widgets = {
      "content": TinyMCE(attrs={"rows": 30}),
      "tags": forms.TextInput(attrs={
        "placeholder": "e.g. seo, django, tutorials"
      })
    }

  def clean_tags(self):
    """
    Normalize comma-separated tags:
    - split on commas
    - trim whitespace
    - drop empties
    - rejoin as 'tag1, tag2, tag3'
    """
    raw = self.cleaned_data.get("tags", "") or ""
    parts = [p.strip() for p in raw.split(",")]
    parts = [p for p in parts if p]
    return ", ".join(dict.fromkeys(parts))  # dedupe, keep order


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
  form = ArticleAdminForm

  # Auto-fill slug from title in the admin UI
  prepopulated_fields = {"slug": ("title",)}

  # Handy list display + filters/search
  list_display = ("title", "published", "published_at", "updated_at")
  list_filter = ("published", "published_at", "updated_at", "created_at")
  search_fields = ("title", "content", "tags")
  date_hierarchy = "published_at"
  readonly_fields = ("created_at", "updated_at", "published_at")

  fieldsets = (
    (None, {
      "fields": ("title", "slug", "content", "published")
    }),
    ("Meta", {
      "fields": ("meta_description", "tags", "published_at", "created_at", "updated_at"),
      "description": "Basic SEO fields and timestamps.",
    }),
  )

  actions = ["publish_selected", "unpublish_selected"]

  def save_model(self, request, obj, form, change):
    # Auto-set published_at when publishing for the first time
    if obj.published and not obj.published_at:
      obj.published_at = timezone.now()
    super().save_model(request, obj, form, change)

  def publish_selected(self, request, queryset):
    now = timezone.now()
    updated = 0
    for obj in queryset:
      if not obj.published:
        obj.published = True
        if not obj.published_at:
          obj.published_at = now
        obj.save(update_fields=["published", "published_at"])
        updated += 1
    self.message_user(request, f"Published {updated} article(s).")
    publish_selected.short_description = "Publish selected articles"

  def unpublish_selected(self, request, queryset):
    updated = queryset.update(published=False)
    self.message_user(request, f"Unpublished {updated} article(s).")
    unpublish_selected.short_description = "Unpublish selected articles"