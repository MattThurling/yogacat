from .models import ImagePosition, NavArea, PageTemplate, SectionType


SCHEMA_NAME = "brochure_site_content"
SCHEMA_VERSION = "1.0"
SCHEMA_DESCRIPTION = (
  "Structured brochure-site content for Django admin CMS pages, sections, CTAs, "
  "navigation, and site settings. Text fields must be plain text, not HTML."
)


def enum_values(enum_class):
  return [choice.value for choice in enum_class]


def string_field(description):
  return {
    "type": "string",
    "description": description,
  }


def int_field(description):
  return {
    "type": "integer",
    "description": description,
  }


def bool_field(description):
  return {
    "type": "boolean",
    "description": description,
  }


def site_settings_schema():
  properties = {
    "site_name": string_field("Public site/client name."),
    "logo_url": string_field("Logo image URL, or empty string."),
    "logo_alt": string_field("Logo alt text, or empty string."),
    "contact_email": string_field("Contact email address, or empty string."),
    "contact_phone": string_field("Contact phone number, or empty string."),
    "contact_address": string_field("Plain text postal/contact address, or empty string."),
    "instagram_url": string_field("Instagram URL, or empty string."),
    "facebook_url": string_field("Facebook URL, or empty string."),
    "linkedin_url": string_field("LinkedIn URL, or empty string."),
    "youtube_url": string_field("YouTube URL, or empty string."),
    "default_meta_title": string_field("Default SEO title."),
    "default_meta_description": string_field("Default SEO meta description, maximum 160 characters."),
    "default_social_image_url": string_field("Default social sharing image URL, or empty string."),
  }
  return object_schema(properties)


def cta_schema():
  properties = {
    "name": string_field("Stable admin name for the reusable CTA."),
    "heading": string_field("CTA heading."),
    "body": string_field("Plain text CTA body. No HTML or Markdown."),
    "primary_label": string_field("Primary button label, or empty string."),
    "primary_url": string_field("Primary button URL/path, or empty string if primary_page_slug is used."),
    "primary_page_slug": string_field("Slug of an internal page for the primary button, or empty string."),
    "secondary_label": string_field("Secondary button label, or empty string."),
    "secondary_url": string_field("Secondary button URL/path, or empty string if secondary_page_slug is used."),
    "secondary_page_slug": string_field("Slug of an internal page for the secondary button, or empty string."),
    "visible": bool_field("Whether this CTA is visible/usable."),
  }
  return object_schema(properties)


def navigation_item_schema():
  properties = {
    "nav_area": {
      "type": "string",
      "enum": enum_values(NavArea),
      "description": "Navigation area.",
    },
    "label": string_field("Navigation label."),
    "page_slug": string_field("Internal page slug, or empty string if url is used."),
    "url": string_field("External URL/local path, or empty string if page_slug is used."),
    "opens_new_tab": bool_field("Whether this link opens in a new tab."),
    "visible": bool_field("Whether this navigation item should show."),
    "sort_order": int_field("Display order, starting at 0."),
  }
  return object_schema(properties)


def section_item_schema():
  properties = {
    "title": string_field("Item title/question/name, or empty string."),
    "subtitle": string_field("Item subtitle/kicker/source, or empty string."),
    "body": string_field("Plain text item body/answer/description. No HTML or Markdown."),
    "icon": string_field("Short icon label/name, or empty string."),
    "image_url": string_field("Image URL, or empty string."),
    "image_alt": string_field("Image alt text, or empty string."),
    "link_label": string_field("Link label, or empty string."),
    "link_url": string_field("External URL/local path, or empty string if link_page_slug is used."),
    "link_page_slug": string_field("Internal page slug for link, or empty string."),
    "visible": bool_field("Whether this item should show."),
    "sort_order": int_field("Display order, starting at 0."),
  }
  return object_schema(properties)


def section_schema():
  properties = {
    "section_type": {
      "type": "string",
      "enum": enum_values(SectionType),
      "description": "CMS section component type.",
    },
    "name": string_field("Stable admin-only section label."),
    "eyebrow": string_field("Small uppercase/kicker text, or empty string."),
    "heading": string_field("Section heading, or empty string."),
    "intro": string_field("Short plain text intro, or empty string."),
    "body": string_field("Plain text section body. Use blank lines for paragraph breaks. No HTML or Markdown."),
    "image_url": string_field("Image URL, or empty string."),
    "image_alt": string_field("Image alt text, or empty string."),
    "image_position": {
      "type": "string",
      "enum": enum_values(ImagePosition),
      "description": "Image placement for split-image sections.",
    },
    "is_full_height": bool_field("Whether the hero should fill the viewport."),
    "primary_cta_label": string_field("Primary button label, or empty string."),
    "primary_cta_url": string_field("Primary button URL/path, or empty string if primary_cta_page_slug is used."),
    "primary_cta_page_slug": string_field("Internal page slug for the primary CTA, or empty string."),
    "secondary_cta_label": string_field("Secondary button label, or empty string."),
    "secondary_cta_url": string_field("Secondary button URL/path, or empty string if secondary_cta_page_slug is used."),
    "secondary_cta_page_slug": string_field("Internal page slug for the secondary CTA, or empty string."),
    "reusable_cta_name": string_field("Reusable CTA name, or empty string."),
    "visible": bool_field("Whether this section should show."),
    "sort_order": int_field("Display order, starting at 0."),
    "items": {
      "type": "array",
      "description": "Repeatable items for cards, benefits, testimonials, FAQ, link cards, and gallery sections.",
      "items": section_item_schema(),
    },
  }
  return object_schema(properties)


def page_schema():
  properties = {
    "title": string_field("Admin page title."),
    "slug": string_field("URL slug without slashes, for example 'about' or 'yoga-classes'. Use 'home' for homepage."),
    "template": {
      "type": "string",
      "enum": enum_values(PageTemplate),
      "description": "Page layout template.",
    },
    "h1": string_field("Page-level H1, or empty string if hero owns the H1."),
    "intro": string_field("Short page intro for templates that use it, or empty string."),
    "seo_title": string_field("SEO meta title."),
    "meta_description": string_field("SEO meta description, maximum 160 characters."),
    "social_image_url": string_field("Social image URL, or empty string."),
    "canonical_url": string_field("Canonical URL override, or empty string."),
    "noindex": bool_field("Whether this page should be noindexed."),
    "is_homepage": bool_field("Whether this page should serve at /."),
    "show_navigation": bool_field("Whether to show global navigation on this page."),
    "show_footer": bool_field("Whether to show the global footer on this page."),
    "sort_order": int_field("Page sort order."),
    "sections": {
      "type": "array",
      "description": "Ordered structured content sections for the page.",
      "items": section_schema(),
    },
  }
  return object_schema(properties)


def default_content_schema():
  properties = {
    "site_settings": site_settings_schema(),
    "ctas": {
      "type": "array",
      "description": "Reusable CTA snippets.",
      "items": cta_schema(),
    },
    "navigation": {
      "type": "array",
      "description": "Primary and footer navigation.",
      "items": navigation_item_schema(),
    },
    "pages": {
      "type": "array",
      "description": "Generated CMS pages. Pages are imported as drafts for editor review.",
      "items": page_schema(),
    },
  }
  return object_schema(properties)


def object_schema(properties):
  return {
    "type": "object",
    "properties": properties,
    "required": list(properties.keys()),
    "additionalProperties": False,
  }
