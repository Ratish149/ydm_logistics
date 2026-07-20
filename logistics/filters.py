import django_filters

from logistics.models import Order


class OrderFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    recipient_phone = django_filters.CharFilter(
        field_name="recipient_phone", lookup_expr="iexact"
    )
    external_order_code = django_filters.CharFilter(
        field_name="external_order_code", lookup_expr="iexact"
    )
    recipient_city = django_filters.CharFilter(
        field_name="recipient_city", lookup_expr="iexact"
    )
    recipient_district = django_filters.CharFilter(
        field_name="recipient_district", lookup_expr="iexact"
    )
    start_date = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )
    end_date = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )
    delivery_location_type = django_filters.CharFilter(
        field_name="delivery_location_type", lookup_expr="iexact"
    )
    tracking_number = django_filters.CharFilter(
        field_name="tracking_number", lookup_expr="icontains"
    )
    recipient_name = django_filters.CharFilter(
        field_name="recipient_name", lookup_expr="icontains"
    )
    is_assigned = django_filters.BooleanFilter(method="filter_is_assigned")

    def filter_is_assigned(self, queryset, name, value):
        if value is True:
            return queryset.filter(assigned_rider__isnull=False)
        elif value is False:
            return queryset.filter(assigned_rider__isnull=True)
        return queryset

    class Meta:
        model = Order
        fields = [
            "status",
            "recipient_phone",
            "external_order_code",
            "recipient_city",
            "recipient_district",
            "created_at",
            "delivery_location_type",
            "tracking_number",
            "recipient_name",
            "is_assigned",
        ]
