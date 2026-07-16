from rest_framework import serializers

from account.serializers import UserListSerializer
from invoice.models import Invoice, ReportInvoice


from django.contrib.auth import get_user_model

User = get_user_model()


class InvoiceSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    user_detail = UserListSerializer(source="user", read_only=True)
    created_by_detail = UserListSerializer(source="created_by", read_only=True)
    approved_by_detail = UserListSerializer(source="approved_by", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "user",
            "user_detail",
            "created_by",
            "created_by_detail",
            "invoice_code",
            "total_amount",
            "paid_amount",
            "due_amount",
            "payment_type",
            "status",
            "approved_by",
            "approved_by_detail",
            "approved_at",
            "is_approved",
            "signature",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_by",
            "approved_by",
            "approved_at",
        ]


class ReportInvoiceSerializer(serializers.ModelSerializer):
    reported_by_detail = UserListSerializer(source="reported_by", read_only=True)
    invoice_detail = InvoiceSerializer(source="invoice", read_only=True)

    class Meta:
        model = ReportInvoice
        fields = [
            "id",
            "invoice",
            "invoice_detail",
            "reported_by",
            "reported_by_detail",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["reported_by"]
