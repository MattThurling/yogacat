from django import forms
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import slugify
from tinymce.widgets import TinyMCE

from .models import (
  Article,
  CallToAction,
  ContentGenerationJob,
  ContentGenerationStatus,
  ContentSchema,
  NavigationItem,
  Page,
  PageSection,
  SectionType,
  SectionItem,
  SiteSettings,
)
from .content_pipeline import apply_generated_content


class PageAdminForm(forms.ModelForm):
  class Meta:
    model = Page
    fields = "__all__"
    widgets = {
      "intro": forms.Textarea(attrs={"rows": 4}),
    }


class PageSectionAdminForm(forms.ModelForm):
  class Meta:
    model = PageSection
    fields = "__all__"
    widgets = {
      "intro": forms.Textarea(attrs={"rows": 4}),
      "body": forms.Textarea(attrs={"rows": 8}),
    }


class SectionItemAdminForm(forms.ModelForm):
  class Meta:
    model = SectionItem
    fields = "__all__"
    widgets = {
      "body": forms.Textarea(attrs={"rows": 5}),
    }


class CallToActionAdminForm(forms.ModelForm):
  class Meta:
    model = CallToAction
    fields = "__all__"
    widgets = {
      "body": forms.Textarea(attrs={"rows": 4}),
    }


class PageSectionInline(admin.StackedInline):
  model = PageSection
  fk_name = "page"
  extra = 0
  show_change_link = True
  fields = ("sort_order", "section_type", "name", "heading", "visible")
  ordering = ("sort_order", "id")


class SectionItemInline(admin.StackedInline):
  model = SectionItem
  form = SectionItemAdminForm
  extra = 0
  fields = (
    "sort_order",
    "visible",
    "title",
    "subtitle",
    "body",
    "icon",
    "image_url",
    "image_alt",
    "link_label",
    "link_page",
    "link_url",
  )
  ordering = ("sort_order", "id")


class NavigationItemInline(admin.TabularInline):
  model = NavigationItem
  extra = 0
  fields = ("sort_order", "nav_area", "visible", "label", "page", "url", "opens_new_tab")
  ordering = ("nav_area", "sort_order", "label")


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
  form = PageAdminForm
  inlines = [PageSectionInline]
  list_display = ("title", "slug", "template", "published", "is_homepage", "sort_order", "updated_at", "preview_link")
  list_filter = ("template", "published", "is_homepage", "noindex", "show_navigation", "show_footer")
  search_fields = ("title", "slug", "h1", "intro", "meta_description")
  prepopulated_fields = {"slug": ("title",)}
  readonly_fields = ("created_at", "updated_at", "published_at", "preview_link")
  actions = ["publish_selected", "unpublish_selected", "duplicate_pages"]
  fieldsets = (
    ("Page", {
      "fields": ("title", "slug", "template", "h1", "intro", "sort_order"),
      "description": "Choose a layout template here. Add and order the actual page content in sections below.",
    }),
    ("Publishing", {
      "fields": ("published", "published_at", "is_homepage", "show_navigation", "show_footer", "preview_link"),
    }),
    ("SEO", {
      "fields": ("seo_title", "meta_description", "social_image_url", "canonical_url", "noindex"),
    }),
    ("System", {
      "classes": ("collapse",),
      "fields": ("created_at", "updated_at"),
    }),
  )

  def preview_link(self, obj):
    if not obj.pk:
      return "Save first to preview."
    return format_html('<a href="{}" target="_blank" rel="noopener">Preview page</a>', obj.preview_url)

  preview_link.short_description = "Preview"

  def publish_selected(self, request, queryset):
    now = timezone.now()
    updated = queryset.update(published=True, published_at=now)
    self.message_user(request, f"Published {updated} page(s).")

  publish_selected.short_description = "Publish selected pages"

  def unpublish_selected(self, request, queryset):
    updated = queryset.update(published=False)
    self.message_user(request, f"Unpublished {updated} page(s).")

  unpublish_selected.short_description = "Unpublish selected pages"

  def duplicate_pages(self, request, queryset):
    created = 0
    for page in queryset.prefetch_related("sections__items"):
      base_slug = slugify(f"{page.slug}-copy")[:230] or "page-copy"
      slug = base_slug
      counter = 2
      while Page.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

      page_data = {
        field.name: getattr(page, field.name)
        for field in page._meta.fields
        if field.name not in {"id", "slug", "title", "published", "published_at", "is_homepage", "created_at", "updated_at"}
      }
      new_page = Page.objects.create(
        **page_data,
        title=f"{page.title} copy",
        slug=slug,
        published=False,
        is_homepage=False,
      )

      for section in page.sections.all():
        section_data = {
          field.name: getattr(section, field.name)
          for field in section._meta.fields
          if field.name not in {"id", "page", "created_at", "updated_at"}
        }
        new_section = PageSection.objects.create(page=new_page, **section_data)
        for item in section.items.all():
          item_data = {
            field.name: getattr(item, field.name)
            for field in item._meta.fields
            if field.name not in {"id", "section"}
          }
          SectionItem.objects.create(section=new_section, **item_data)

      created += 1
    self.message_user(request, f"Duplicated {created} page(s). Duplicates are saved as drafts.")

  duplicate_pages.short_description = "Duplicate selected pages as drafts"


@admin.register(PageSection)
class PageSectionAdmin(admin.ModelAdmin):
  form = PageSectionAdminForm
  list_display = ("page", "admin_label", "section_type", "visible", "sort_order", "updated_at")
  list_filter = ("section_type", "visible", "page")
  search_fields = ("name", "heading", "intro", "body", "page__title")
  ordering = ("page", "sort_order", "id")

  item_section_types = {
    SectionType.CARD_GRID,
    SectionType.BENEFIT_LIST,
    SectionType.TESTIMONIALS,
    SectionType.FAQ,
    SectionType.LINK_CARDS,
    SectionType.GALLERY,
  }

  setup_fieldset = ("Section setup", {
    "fields": ("page", "section_type", "name", "sort_order", "visible"),
    "description": "Choose the component type, then save. The edit form narrows to the fields that component uses.",
  })
  copy_fieldset = ("Copy", {
    "fields": ("eyebrow", "heading", "intro", "body"),
  })
  image_fieldset = ("Image", {
    "fields": ("image_url", "image_alt", "image_position", "is_full_height"),
  })
  buttons_fieldset = ("Buttons", {
    "fields": (
      "primary_cta_label",
      "primary_cta_page",
      "primary_cta_url",
      "secondary_cta_label",
      "secondary_cta_page",
      "secondary_cta_url",
    ),
  })

  def get_inlines(self, request, obj=None):
    if obj and obj.section_type in self.item_section_types:
      return [SectionItemInline]
    return []

  def get_fieldsets(self, request, obj=None):
    if not obj:
      return (
        self.setup_fieldset,
        self.copy_fieldset,
        self.image_fieldset,
        self.buttons_fieldset,
        ("Reusable CTA", {"fields": ("reusable_cta",)}),
      )

    if obj.section_type == SectionType.HERO:
      return (
        self.setup_fieldset,
        ("Hero copy", {"fields": ("eyebrow", "heading", "intro", "body")}),
        ("Hero image", {"fields": ("image_url", "image_alt", "is_full_height")}),
        self.buttons_fieldset,
      )

    if obj.section_type == SectionType.RICH_TEXT:
      return (
        self.setup_fieldset,
        self.copy_fieldset,
      )

    if obj.section_type in {SectionType.CARD_GRID, SectionType.BENEFIT_LIST, SectionType.TESTIMONIALS, SectionType.FAQ, SectionType.LINK_CARDS}:
      return (
        self.setup_fieldset,
        ("Section intro", {"fields": ("eyebrow", "heading", "intro")}),
      )

    if obj.section_type == SectionType.CTA:
      return (
        self.setup_fieldset,
        ("Local CTA copy", {"fields": ("eyebrow", "heading", "body")}),
        ("Reusable CTA", {"fields": ("reusable_cta",)}),
        self.buttons_fieldset,
      )

    if obj.section_type == SectionType.QUOTE:
      return (
        self.setup_fieldset,
        ("Quote", {"fields": ("eyebrow", "body", "heading")}),
      )

    if obj.section_type == SectionType.IMAGE_TEXT:
      return (
        self.setup_fieldset,
        self.copy_fieldset,
        ("Image", {"fields": ("image_url", "image_alt", "image_position")}),
        self.buttons_fieldset,
      )

    if obj.section_type == SectionType.GALLERY:
      return (
        self.setup_fieldset,
        ("Section intro", {"fields": ("eyebrow", "heading", "intro")}),
        ("Lead image", {"fields": ("image_url", "image_alt")}),
      )

    return (
      self.setup_fieldset,
      self.copy_fieldset,
      self.image_fieldset,
      self.buttons_fieldset,
      ("Reusable CTA", {"fields": ("reusable_cta",)}),
    )

  def admin_label(self, obj):
    return obj.name or obj.heading or obj.get_section_type_display()

  admin_label.short_description = "Section"


@admin.register(SectionItem)
class SectionItemAdmin(admin.ModelAdmin):
  form = SectionItemAdminForm
  list_display = ("section", "title", "visible", "sort_order")
  list_filter = ("visible", "section__section_type")
  search_fields = ("title", "subtitle", "body", "section__page__title")
  ordering = ("section", "sort_order", "id")


@admin.register(CallToAction)
class CallToActionAdmin(admin.ModelAdmin):
  form = CallToActionAdminForm
  list_display = ("name", "heading", "visible")
  list_filter = ("visible",)
  search_fields = ("name", "heading", "body")
  fieldsets = (
    ("CTA", {
      "fields": ("name", "visible", "heading", "body"),
    }),
    ("Buttons", {
      "fields": ("primary_label", "primary_page", "primary_url", "secondary_label", "secondary_page", "secondary_url"),
    }),
  )


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
  inlines = [NavigationItemInline]
  fieldsets = (
    ("Brand", {
      "fields": ("site_name", "logo_url", "logo_alt"),
    }),
    ("Contact", {
      "fields": ("contact_email", "contact_phone", "contact_address"),
    }),
    ("Social links", {
      "fields": ("instagram_url", "facebook_url", "linkedin_url", "youtube_url"),
    }),
    ("Default SEO", {
      "fields": ("default_meta_title", "default_meta_description", "default_social_image_url"),
    }),
  )

  def has_add_permission(self, request):
    return not SiteSettings.objects.exists()

  def has_delete_permission(self, request, obj=None):
    return False


@admin.register(ContentSchema)
class ContentSchemaAdmin(admin.ModelAdmin):
  list_display = ("name", "version", "active", "updated_at")
  list_filter = ("active", "version")
  search_fields = ("name", "description")
  readonly_fields = ("created_at", "updated_at")
  fieldsets = (
    ("Schema", {
      "fields": ("name", "version", "description", "active", "schema"),
      "description": "This schema constrains OpenAI output. Keep it aligned with the CMS page and section models.",
    }),
    ("System", {
      "classes": ("collapse",),
      "fields": ("created_at", "updated_at"),
    }),
  )


@admin.register(ContentGenerationJob)
class ContentGenerationJobAdmin(admin.ModelAdmin):
  list_display = ("name", "model", "status", "content_schema", "generated_at", "applied_at")
  list_filter = ("status", "model", "content_schema")
  search_fields = ("name", "brief", "error_message")
  readonly_fields = ("generated_at", "applied_at", "created_at", "updated_at", "error_message")
  actions = ["apply_selected_generated_content"]
  fieldsets = (
    ("Generation brief", {
      "fields": ("name", "content_schema", "model", "brief"),
      "description": "Create the job here, then run the generation management command. Generated pages remain drafts for editor review.",
    }),
    ("Apply behavior", {
      "fields": ("replace_existing_sections", "replace_navigation"),
    }),
    ("Generated output", {
      "fields": ("status", "generated_content", "error_message"),
    }),
    ("System", {
      "classes": ("collapse",),
      "fields": ("generated_at", "applied_at", "created_at", "updated_at"),
    }),
  )

  def apply_selected_generated_content(self, request, queryset):
    applied = 0
    for job in queryset:
      if not job.generated_content:
        self.message_user(request, f"Skipped '{job}': no generated content.", level="warning")
        continue
      apply_generated_content(
        job.generated_content,
        replace_sections=job.replace_existing_sections,
        replace_navigation=job.replace_navigation,
      )
      job.status = ContentGenerationStatus.APPLIED
      job.applied_at = timezone.now()
      job.save(update_fields=["status", "applied_at", "updated_at"])
      applied += 1
    self.message_user(request, f"Applied {applied} generated content job(s) to draft pages.")

  apply_selected_generated_content.short_description = "Apply generated content to draft pages"


class ArticleAdminForm(forms.ModelForm):
  class Meta:
    model = Article
    fields = "__all__"
    widgets = {
      "content": TinyMCE(attrs={"rows": 30}),
      "tags": forms.TextInput(attrs={"placeholder": "e.g. yoga, wellbeing, classes"}),
    }

  def clean_tags(self):
    raw = self.cleaned_data.get("tags", "") or ""
    parts = [part.strip() for part in raw.split(",")]
    parts = [part for part in parts if part]
    return ", ".join(dict.fromkeys(parts))


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
  form = ArticleAdminForm
  prepopulated_fields = {"slug": ("title",)}
  list_display = ("title", "published", "published_at", "updated_at")
  list_filter = ("published", "published_at", "updated_at", "created_at")
  search_fields = ("title", "content", "tags")
  date_hierarchy = "published_at"
  readonly_fields = ("created_at", "updated_at", "published_at")
  actions = ["publish_selected", "unpublish_selected"]
  fieldsets = (
    (None, {
      "fields": ("title", "slug", "content", "published"),
    }),
    ("Meta", {
      "fields": ("meta_description", "tags", "published_at", "created_at", "updated_at"),
      "description": "Basic SEO fields and timestamps.",
    }),
  )

  def save_model(self, request, obj, form, change):
    if obj.published and not obj.published_at:
      obj.published_at = timezone.now()
    super().save_model(request, obj, form, change)

  def publish_selected(self, request, queryset):
    now = timezone.now()
    updated = queryset.update(published=True, published_at=now)
    self.message_user(request, f"Published {updated} article(s).")

  publish_selected.short_description = "Publish selected articles"

  def unpublish_selected(self, request, queryset):
    updated = queryset.update(published=False)
    self.message_user(request, f"Unpublished {updated} article(s).")

  unpublish_selected.short_description = "Unpublish selected articles"
