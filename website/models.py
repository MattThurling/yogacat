from django.db import models

class Article(models.Model):
  title = models.CharField(max_length=255)
  slug = models.SlugField(max_length=255, unique=True)
  meta_description = models.CharField(max_length=160, blank=True)
  tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
  content = models.TextField()
  published = models.BooleanField(default=False)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  published_at = models.DateTimeField(blank=True, null=True)

  class Meta:
    ordering = ['-published_at', '-created_at']

  def __str__(self):
    return self.title