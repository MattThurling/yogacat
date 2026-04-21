from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone

from .content_schema import SCHEMA_DESCRIPTION, SCHEMA_NAME, SCHEMA_VERSION, default_content_schema
from .models import (
  CallToAction,
  ContentGenerationStatus,
  ContentSchema,
  ImagePosition,
  NavArea,
  NavigationItem,
  Page,
  PageSection,
  PageTemplate,
  SectionItem,
  SectionType,
  SiteSettings,
)


PAGE_FIELDS = {
  "title",
  "slug",
  "template",
  "h1",
  "intro",
  "seo_title",
  "meta_description",
  "social_image_url",
  "canonical_url",
  "noindex",
  "is_homepage",
  "show_navigation",
  "show_footer",
  "sort_order",
}

SECTION_FIELDS = {
  "section_type",
  "name",
  "eyebrow",
  "heading",
  "intro",
  "body",
  "image_url",
  "image_alt",
  "image_position",
  "is_full_height",
  "primary_cta_label",
  "primary_cta_url",
  "secondary_cta_label",
  "secondary_cta_url",
  "visible",
  "sort_order",
}

SECTION_ITEM_FIELDS = {
  "title",
  "subtitle",
  "body",
  "icon",
  "image_url",
  "image_alt",
  "link_label",
  "link_url",
  "visible",
  "sort_order",
}

CTA_FIELDS = {
  "name",
  "heading",
  "body",
  "primary_label",
  "primary_url",
  "secondary_label",
  "secondary_url",
  "visible",
}

SITE_SETTINGS_FIELDS = {
  "site_name",
  "logo_url",
  "logo_alt",
  "contact_email",
  "contact_phone",
  "contact_address",
  "instagram_url",
  "facebook_url",
  "linkedin_url",
  "youtube_url",
  "default_meta_title",
  "default_meta_description",
  "default_social_image_url",
}


def sync_default_content_schema():
  schema, _ = ContentSchema.objects.update_or_create(
    name=SCHEMA_NAME,
    defaults={
      "version": SCHEMA_VERSION,
      "description": SCHEMA_DESCRIPTION,
      "schema": default_content_schema(),
      "active": True,
    },
  )
  return schema


def get_active_content_schema():
  schema = ContentSchema.objects.filter(name=SCHEMA_NAME, active=True).order_by("-updated_at").first()
  return schema or sync_default_content_schema()


@transaction.atomic
def apply_generated_content(payload, replace_sections=True, replace_navigation=True, force_draft=True):
  validate_payload(payload)
  summary = {
    "site_settings": 0,
    "pages_created": 0,
    "pages_updated": 0,
    "ctas_created": 0,
    "ctas_updated": 0,
    "sections_created": 0,
    "items_created": 0,
    "navigation_created": 0,
    "navigation_replaced": 0,
  }

  site_settings = apply_site_settings(payload["site_settings"], summary)
  pages_by_slug = apply_pages(payload["pages"], summary, force_draft=force_draft)
  ctas_by_name = apply_ctas(payload["ctas"], pages_by_slug, summary)
  apply_navigation(payload["navigation"], site_settings, pages_by_slug, summary, replace_navigation)

  if replace_sections:
    for page_data in payload["pages"]:
      page = pages_by_slug[page_data["slug"]]
      page.sections.all().delete()
      apply_sections(page, page_data["sections"], pages_by_slug, ctas_by_name, summary)

  return summary


def mark_job_failed(job, message):
  job.status = ContentGenerationStatus.FAILED
  job.error_message = message
  job.save(update_fields=["status", "error_message", "updated_at"])


def mark_job_generated(job, content):
  job.generated_content = content
  job.status = ContentGenerationStatus.GENERATED
  job.generated_at = timezone.now()
  job.error_message = ""
  job.save(update_fields=["generated_content", "status", "generated_at", "error_message", "updated_at"])


def mark_job_applied(job):
  job.status = ContentGenerationStatus.APPLIED
  job.applied_at = timezone.now()
  job.save(update_fields=["status", "applied_at", "updated_at"])


def validate_payload(payload):
  if not isinstance(payload, dict):
    raise CommandError("Generated content must be a JSON object.")
  for key in ("site_settings", "ctas", "navigation", "pages"):
    if key not in payload:
      raise CommandError(f"Generated content is missing '{key}'.")
  if not isinstance(payload["pages"], list) or not payload["pages"]:
    raise CommandError("Generated content must contain at least one page.")


def apply_site_settings(settings_data, summary):
  settings = SiteSettings.load()
  for field, value in filter_fields(settings_data, SITE_SETTINGS_FIELDS).items():
    setattr(settings, field, value)
  settings.save()
  summary["site_settings"] = 1
  return settings


def apply_pages(pages_data, summary, force_draft=True):
  pages_by_slug = {}
  valid_templates = {choice.value for choice in PageTemplate}

  for index, page_data in enumerate(pages_data):
    slug = page_data.get("slug")
    if not slug:
      raise CommandError(f"Page #{index + 1} is missing 'slug'.")

    template = page_data.get("template")
    if template not in valid_templates:
      raise CommandError(f"Page '{slug}' has invalid template '{template}'.")

    defaults = filter_fields(page_data, PAGE_FIELDS)
    defaults["template"] = template
    if force_draft:
      defaults["published"] = False
      defaults["published_at"] = None

    page, created = Page.objects.update_or_create(slug=slug, defaults=defaults)
    pages_by_slug[slug] = page
    summary["pages_created" if created else "pages_updated"] += 1

  return pages_by_slug


def apply_ctas(ctas_data, pages_by_slug, summary):
  ctas_by_name = {}
  for index, cta_data in enumerate(ctas_data):
    name = cta_data.get("name")
    if not name:
      raise CommandError(f"CTA #{index + 1} is missing 'name'.")

    defaults = filter_fields(cta_data, CTA_FIELDS)
    defaults["primary_page"] = resolve_page(cta_data.get("primary_page_slug"), pages_by_slug, f"CTA '{name}'")
    defaults["secondary_page"] = resolve_page(cta_data.get("secondary_page_slug"), pages_by_slug, f"CTA '{name}'")
    cta, created = CallToAction.objects.update_or_create(name=name, defaults=defaults)
    ctas_by_name[name] = cta
    summary["ctas_created" if created else "ctas_updated"] += 1
  return ctas_by_name


def apply_navigation(navigation_data, site_settings, pages_by_slug, summary, replace_navigation):
  if replace_navigation:
    summary["navigation_replaced"] = site_settings.navigation_items.count()
    site_settings.navigation_items.all().delete()

  valid_nav_areas = {choice.value for choice in NavArea}
  for index, item_data in enumerate(navigation_data):
    nav_area = item_data.get("nav_area")
    if nav_area not in valid_nav_areas:
      raise CommandError(f"Navigation item #{index + 1} has invalid nav_area '{nav_area}'.")

    label = item_data.get("label")
    if not label:
      raise CommandError(f"Navigation item #{index + 1} is missing 'label'.")

    NavigationItem.objects.create(
      site_settings=site_settings,
      nav_area=nav_area,
      label=label,
      page=resolve_page(item_data.get("page_slug"), pages_by_slug, f"navigation item '{label}'"),
      url=item_data.get("url", ""),
      opens_new_tab=item_data.get("opens_new_tab", False),
      visible=item_data.get("visible", True),
      sort_order=item_data.get("sort_order", index),
    )
    summary["navigation_created"] += 1


def apply_sections(page, sections_data, pages_by_slug, ctas_by_name, summary):
  valid_section_types = {choice.value for choice in SectionType}
  valid_image_positions = {choice.value for choice in ImagePosition}

  for index, section_data in enumerate(sections_data):
    section_type = section_data.get("section_type")
    if section_type not in valid_section_types:
      raise CommandError(f"Page '{page.slug}' section #{index + 1} has invalid section_type '{section_type}'.")

    image_position = section_data.get("image_position")
    if image_position not in valid_image_positions:
      raise CommandError(f"Page '{page.slug}' section #{index + 1} has invalid image_position '{image_position}'.")

    section_values = filter_fields(section_data, SECTION_FIELDS)
    section_values["sort_order"] = section_values.get("sort_order", index)
    section_values["primary_cta_page"] = resolve_page(
      section_data.get("primary_cta_page_slug"),
      pages_by_slug,
      f"page '{page.slug}' section '{section_values.get('name', index)}'",
    )
    section_values["secondary_cta_page"] = resolve_page(
      section_data.get("secondary_cta_page_slug"),
      pages_by_slug,
      f"page '{page.slug}' section '{section_values.get('name', index)}'",
    )
    section_values["reusable_cta"] = resolve_cta(
      section_data.get("reusable_cta_name"),
      ctas_by_name,
      f"page '{page.slug}' section '{section_values.get('name', index)}'",
    )

    section = PageSection.objects.create(page=page, **section_values)
    summary["sections_created"] += 1
    apply_section_items(section, section_data["items"], pages_by_slug, summary)


def apply_section_items(section, items_data, pages_by_slug, summary):
  for index, item_data in enumerate(items_data):
    item_values = filter_fields(item_data, SECTION_ITEM_FIELDS)
    item_values["sort_order"] = item_values.get("sort_order", index)
    item_values["link_page"] = resolve_page(
      item_data.get("link_page_slug"),
      pages_by_slug,
      f"section item '{item_values.get('title', index)}'",
    )
    SectionItem.objects.create(section=section, **item_values)
    summary["items_created"] += 1


def resolve_page(slug, pages_by_slug, context):
  if not slug:
    return None
  if slug in pages_by_slug:
    return pages_by_slug[slug]
  try:
    return Page.objects.get(slug=slug)
  except Page.DoesNotExist as exc:
    raise CommandError(f"{context} references unknown page slug '{slug}'.") from exc


def resolve_cta(name, ctas_by_name, context):
  if not name:
    return None
  if name in ctas_by_name:
    return ctas_by_name[name]
  try:
    return CallToAction.objects.get(name=name)
  except CallToAction.DoesNotExist as exc:
    raise CommandError(f"{context} references unknown reusable CTA '{name}'.") from exc


def filter_fields(data, allowed_fields):
  return {field: data[field] for field in allowed_fields if field in data}
