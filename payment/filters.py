import django_filters

from payment.models import CodPayment


class CodPaymentFilter(django_filters.FilterSet):
    user_id = django_filters.NumberFilter(field_name="user__id")
    status = django_filters.CharFilter(field_name="status")
    start_date = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = CodPayment
        fields = ["user_id", "status", "start_date", "end_date"]


class CodPaymentOrderFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="cod_payments__status")
    order_status = django_filters.CharFilter(field_name="status")
    start_date = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        from logistics.models import Order

        model = Order
        fields = ["status", "order_status", "start_date", "end_date"]
