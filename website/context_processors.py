from django.db import OperationalError, ProgrammingError

from .models import NavArea, SiteSettings


def site_settings(request):
  try:
    settings = SiteSettings.load()
    navigation = settings.navigation_items.filter(visible=True).select_related("page").order_by("nav_area", "sort_order", "label")
  except (OperationalError, ProgrammingError):
    return {
      "site_settings": None,
      "primary_navigation": [],
      "footer_navigation": [],
    }

  return {
    "site_settings": settings,
    "primary_navigation": [item for item in navigation if item.nav_area == NavArea.PRIMARY],
    "footer_navigation": [item for item in navigation if item.nav_area == NavArea.FOOTER],
  }
