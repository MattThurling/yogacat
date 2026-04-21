from django.db import models
from django.urls import reverse
from django.utils import timezone


class PageTemplate(models.TextChoices):
  HOMEPAGE = "homepage", "Homepage"
  STANDARD = "standard", "Standard page"
  SERVICE = "service", "Service / landing page"
  SIMPLE = "simple", "Simple text page"
  CONTACT = "contact", "Contact / CTA page"


class SectionType(models.TextChoices):
  HERO = "hero", "Hero"
  RICH_TEXT = "rich_text", "Rich text"
  CARD_GRID = "card_grid", "Card grid"
  BENEFIT_LIST = "benefit_list", "Icon / benefit list"
  CTA = "cta", "CTA block"
  TESTIMONIALS = "testimonials", "Testimonial block"
  FAQ = "faq", "FAQ block"
  QUOTE = "quote", "Quote block"
  LINK_CARDS = "link_cards", "Link cards / child page cards"
  IMAGE_TEXT = "image_text", "Image + text split"
  GALLERY = "gallery", "Simple gallery / image block"


class NavArea(models.TextChoices):
  PRIMARY = "primary", "Primary navigation"
  FOOTER = "footer", "Footer navigation"


class ImagePosition(models.TextChoices):
  LEFT = "left", "Image left"
  RIGHT = "right", "Image right"


class ContentGenerationStatus(models.TextChoices):
  DRAFT = "draft", "Draft"
  GENERATED = "generated", "Generated"
  APPLIED = "applied", "Applied to draft pages"
  FAILED = "failed", "Failed"


class ContentSchema(models.Model):
  name = models.CharField(max_length=120, unique=True)
  version = models.CharField(max_length=40, default="1.0")
  description = models.TextField(blank=True)
  schema = models.JSONField(help_text="JSON Schema used for OpenAI Structured Outputs.")
  active = models.BooleanField(default=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ["name", "-version"]

  def __str__(self):
    return f"{self.name} v{self.version}"


class Page(models.Model):
  title = models.CharField(max_length=255, help_text="Internal/admin title for this page.")
  slug = models.SlugField(
    max_length=255,
    unique=True,
    help_text="URL slug, for example 'about' creates /about/. The homepage can use 'home'.",
  )
  template = models.CharField(
    max_length=40,
    choices=PageTemplate.choices,
    default=PageTemplate.STANDARD,
    help_text="Controls the layout. Content still comes from editable sections below.",
  )
  h1 = models.CharField(
    "H1 heading",
    max_length=255,
    blank=True,
    help_text="Optional page-level H1. Leave blank if the first hero section owns the H1.",
  )
  intro = models.TextField(blank=True, help_text="Optional short intro shown by standard templates.")
  seo_title = models.CharField(max_length=255, blank=True, help_text="Meta title. Defaults to the page title.")
  meta_description = models.CharField(max_length=160, blank=True)
  social_image_url = models.URLField(blank=True, help_text="Optional Open Graph/social sharing image URL.")
  canonical_url = models.URLField(blank=True, help_text="Optional canonical URL override.")
  noindex = models.BooleanField(default=False, help_text="Ask search engines not to index this page.")
  published = models.BooleanField(default=False)
  published_at = models.DateTimeField(blank=True, null=True)
  is_homepage = models.BooleanField(default=False, help_text="Serve this page at /.")
  show_navigation = models.BooleanField(default=True)
  show_footer = models.BooleanField(default=True)
  sort_order = models.PositiveIntegerField(default=0, help_text="Useful when listing pages or link cards.")
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ["sort_order", "title"]

  def __str__(self):
    return self.title

  def save(self, *args, **kwargs):
    if self.published and not self.published_at:
      self.published_at = timezone.now()
    super().save(*args, **kwargs)
    if self.is_homepage:
      Page.objects.exclude(pk=self.pk).filter(is_homepage=True).update(is_homepage=False)

  def get_absolute_url(self):
    if self.is_homepage:
      return reverse("home")
    return reverse("page-detail", kwargs={"slug": self.slug})

  @property
  def template_name(self):
    return f"pages/{self.template}.html"

  @property
  def display_h1(self):
    return self.h1 or self.title

  @property
  def meta_title(self):
    return self.seo_title or self.title

  @property
  def preview_url(self):
    return f"{self.get_absolute_url()}?preview=1"


class CallToAction(models.Model):
  name = models.CharField(max_length=120, help_text="Admin label for reusing this CTA.")
  heading = models.CharField(max_length=255)
  body = models.TextField(blank=True, help_text="Plain text only. Do not store raw HTML.")
  primary_label = models.CharField(max_length=80, blank=True)
  primary_url = models.CharField(max_length=255, blank=True, help_text="External URL or local path.")
  primary_page = models.ForeignKey(
    Page,
    blank=True,
    null=True,
    related_name="primary_cta_snippets",
    on_delete=models.SET_NULL,
  )
  secondary_label = models.CharField(max_length=80, blank=True)
  secondary_url = models.CharField(max_length=255, blank=True, help_text="External URL or local path.")
  secondary_page = models.ForeignKey(
    Page,
    blank=True,
    null=True,
    related_name="secondary_cta_snippets",
    on_delete=models.SET_NULL,
  )
  visible = models.BooleanField(default=True)

  class Meta:
    ordering = ["name"]

  def __str__(self):
    return self.name

  @property
  def primary_href(self):
    return self.primary_page.get_absolute_url() if self.primary_page_id else self.primary_url

  @property
  def secondary_href(self):
    return self.secondary_page.get_absolute_url() if self.secondary_page_id else self.secondary_url


class PageSection(models.Model):
  page = models.ForeignKey(Page, related_name="sections", on_delete=models.CASCADE)
  section_type = models.CharField(max_length=40, choices=SectionType.choices, default=SectionType.RICH_TEXT)
  name = models.CharField(
    max_length=120,
    blank=True,
    help_text="Admin-only label. Useful when a page has several sections of the same type.",
  )
  eyebrow = models.CharField(max_length=120, blank=True)
  heading = models.CharField(max_length=255, blank=True)
  intro = models.TextField(blank=True, help_text="Plain text only. Do not store raw HTML.")
  body = models.TextField(blank=True, help_text="Plain text only. Use blank lines for paragraph breaks.")
  image_url = models.URLField(blank=True)
  image_alt = models.CharField(max_length=255, blank=True)
  image_position = models.CharField(max_length=10, choices=ImagePosition.choices, default=ImagePosition.RIGHT)
  is_full_height = models.BooleanField(
    default=False,
    help_text="Useful for a splash-style hero. Other section types ignore this.",
  )
  primary_cta_label = models.CharField(max_length=80, blank=True)
  primary_cta_url = models.CharField(max_length=255, blank=True, help_text="External URL or local path.")
  primary_cta_page = models.ForeignKey(
    Page,
    blank=True,
    null=True,
    related_name="primary_section_ctas",
    on_delete=models.SET_NULL,
  )
  secondary_cta_label = models.CharField(max_length=80, blank=True)
  secondary_cta_url = models.CharField(max_length=255, blank=True, help_text="External URL or local path.")
  secondary_cta_page = models.ForeignKey(
    Page,
    blank=True,
    null=True,
    related_name="secondary_section_ctas",
    on_delete=models.SET_NULL,
  )
  reusable_cta = models.ForeignKey(
    CallToAction,
    blank=True,
    null=True,
    on_delete=models.SET_NULL,
    help_text="Optional shared CTA snippet. CTA sections can use this instead of local fields.",
  )
  visible = models.BooleanField(default=True)
  sort_order = models.PositiveIntegerField(default=0)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ["sort_order", "id"]

  def __str__(self):
    label = self.name or self.heading or self.get_section_type_display()
    return f"{self.page}: {label}"

  @property
  def template_name(self):
    return f"sections/{self.section_type}.html"

  @property
  def primary_href(self):
    return self.primary_cta_page.get_absolute_url() if self.primary_cta_page_id else self.primary_cta_url

  @property
  def secondary_href(self):
    return self.secondary_cta_page.get_absolute_url() if self.secondary_cta_page_id else self.secondary_cta_url

  @property
  def cta_heading(self):
    return self.reusable_cta.heading if self.reusable_cta_id else self.heading

  @property
  def cta_body(self):
    return self.reusable_cta.body if self.reusable_cta_id else self.body

  @property
  def cta_primary_label(self):
    return self.reusable_cta.primary_label if self.reusable_cta_id else self.primary_cta_label

  @property
  def cta_primary_href(self):
    return self.reusable_cta.primary_href if self.reusable_cta_id else self.primary_href

  @property
  def cta_secondary_label(self):
    return self.reusable_cta.secondary_label if self.reusable_cta_id else self.secondary_cta_label

  @property
  def cta_secondary_href(self):
    return self.reusable_cta.secondary_href if self.reusable_cta_id else self.secondary_href


class SectionItem(models.Model):
  section = models.ForeignKey(PageSection, related_name="items", on_delete=models.CASCADE)
  title = models.CharField(max_length=255, blank=True)
  subtitle = models.CharField(max_length=255, blank=True)
  body = models.TextField(blank=True, help_text="Plain text only. Do not store raw HTML.")
  icon = models.CharField(max_length=80, blank=True, help_text="Optional icon name or short label.")
  image_url = models.URLField(blank=True)
  image_alt = models.CharField(max_length=255, blank=True)
  link_label = models.CharField(max_length=80, blank=True)
  link_url = models.CharField(max_length=255, blank=True, help_text="External URL or local path.")
  link_page = models.ForeignKey(Page, blank=True, null=True, related_name="section_items", on_delete=models.SET_NULL)
  visible = models.BooleanField(default=True)
  sort_order = models.PositiveIntegerField(default=0)

  class Meta:
    ordering = ["sort_order", "id"]

  def __str__(self):
    return self.title or self.subtitle or f"Item {self.pk}"

  @property
  def href(self):
    return self.link_page.get_absolute_url() if self.link_page_id else self.link_url


class SiteSettings(models.Model):
  site_name = models.CharField(max_length=120, default="YogaCat")
  logo_url = models.URLField(blank=True)
  logo_alt = models.CharField(max_length=255, blank=True)
  contact_email = models.EmailField(blank=True)
  contact_phone = models.CharField(max_length=80, blank=True)
  contact_address = models.TextField(blank=True)
  instagram_url = models.URLField(blank=True)
  facebook_url = models.URLField(blank=True)
  linkedin_url = models.URLField(blank=True)
  youtube_url = models.URLField(blank=True)
  default_meta_title = models.CharField(max_length=255, blank=True)
  default_meta_description = models.CharField(max_length=160, blank=True)
  default_social_image_url = models.URLField(blank=True)

  class Meta:
    verbose_name = "Site settings"
    verbose_name_plural = "Site settings"

  def __str__(self):
    return self.site_name

  @classmethod
  def load(cls):
    obj, _ = cls.objects.get_or_create(pk=1)
    return obj


class NavigationItem(models.Model):
  site_settings = models.ForeignKey(SiteSettings, related_name="navigation_items", on_delete=models.CASCADE)
  nav_area = models.CharField(max_length=20, choices=NavArea.choices, default=NavArea.PRIMARY)
  label = models.CharField(max_length=80)
  page = models.ForeignKey(Page, blank=True, null=True, related_name="navigation_items", on_delete=models.SET_NULL)
  url = models.CharField(max_length=255, blank=True, help_text="External URL or local path. Ignored if page is set.")
  opens_new_tab = models.BooleanField(default=False)
  visible = models.BooleanField(default=True)
  sort_order = models.PositiveIntegerField(default=0)

  class Meta:
    ordering = ["nav_area", "sort_order", "label"]

  def __str__(self):
    return f"{self.get_nav_area_display()}: {self.label}"

  @property
  def href(self):
    return self.page.get_absolute_url() if self.page_id else self.url


class ContentGenerationJob(models.Model):
  name = models.CharField(max_length=120)
  content_schema = models.ForeignKey(
    ContentSchema,
    blank=True,
    null=True,
    on_delete=models.SET_NULL,
    help_text="Schema used for OpenAI Structured Outputs. Leave blank to use the active brochure schema.",
  )
  model = models.CharField(
    max_length=80,
    default="gpt-4.1-mini",
    help_text="OpenAI model used by the generation command.",
  )
  brief = models.TextField(help_text="Client/site brief. Include audience, offer, tone, pages needed, and constraints.")
  status = models.CharField(
    max_length=20,
    choices=ContentGenerationStatus.choices,
    default=ContentGenerationStatus.DRAFT,
  )
  generated_content = models.JSONField(
    blank=True,
    null=True,
    help_text="Schema-valid generated content. Applying it creates draft pages and structured sections.",
  )
  replace_existing_sections = models.BooleanField(
    default=True,
    help_text="When applying generated content, rebuild sections for pages included in the generated payload.",
  )
  replace_navigation = models.BooleanField(
    default=True,
    help_text="When applying generated content, replace navigation with generated navigation.",
  )
  error_message = models.TextField(blank=True)
  generated_at = models.DateTimeField(blank=True, null=True)
  applied_at = models.DateTimeField(blank=True, null=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ["-created_at"]

  def __str__(self):
    return self.name

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

  def get_absolute_url(self):
    return reverse("article-detail", kwargs={"slug": self.slug})
