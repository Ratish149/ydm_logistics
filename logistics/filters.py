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
    start_date = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    end_date = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = Order
        fields = [
            "status",
            "recipient_phone",
            "external_order_code",
            "recipient_city",
            "recipient_district",
            "created_at",
        ]
