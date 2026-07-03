import django_filters as filters

from .models import Business, SiteObject


class BusinessFilter(filters.FilterSet):
    class Meta:
        model = Business
        fields = ["kind", "is_active"]


class SiteObjectFilter(filters.FilterSet):
    class Meta:
        model = SiteObject
        fields = ["business", "city", "is_active"]
