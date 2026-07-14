from django_filters import rest_framework as django_filters

from logistics.models import Order


class RiderOrderFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status", lookup_expr="exact")
    city = django_filters.CharFilter(
        field_name="recipient_city", lookup_expr="icontains"
    )
    payment_type = django_filters.CharFilter(
        field_name="payment_type", lookup_expr="exact"
    )
    start_date = django_filters.DateFilter(
        field_name="created_at__date", lookup_expr="gte"
    )
    end_date = django_filters.DateFilter(
        field_name="created_at__date", lookup_expr="lte"
    )

    class Meta:
        model = Order
        fields = [
            "status",
            "start_date",
            "end_date",
            "city",
            "payment_type",
        ]
