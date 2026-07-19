import django_filters
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(lookup_expr="icontains")
    first_name = django_filters.CharFilter(lookup_expr="icontains")
    last_name = django_filters.CharFilter(lookup_expr="icontains")
    phone_number = django_filters.CharFilter(lookup_expr="icontains")
    is_active = django_filters.BooleanFilter()
    role = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "is_active",
            "role",
        ]


class VendorFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method="filter_search", label="Search by name, email, or username"
    )
    has_new_order = django_filters.BooleanFilter(
        method="filter_has_new_order", label="Filter vendors with new orders"
    )

    class Meta:
        model = User
        fields = ["search", "has_new_order"]

    def filter_search(self, queryset, name, value):
        from django.db.models import Q

        return queryset.filter(
            Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
            | Q(email__icontains=value)
            | Q(username__icontains=value)
        )

    def filter_has_new_order(self, queryset, name, value):
        if value:
            return queryset.filter(new_order_count__gt=0)
        return queryset
