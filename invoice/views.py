from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, serializers
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.authentication import APIKeyAuthentication
from invoice.filters import InvoiceFilter, InvoiceReportFilter
from invoice.selectors.invoice_selector import (
    get_invoice_reports_queryset,
    get_invoices_queryset,
)
from invoice.serializers import InvoiceSerializer, ReportInvoiceSerializer
from invoice.services.invoice_service import (
    create_invoice,
    create_report,
    update_invoice_approval,
)
from ydm.utils.pagination import CustomPagination


class InvoiceListCreateView(generics.ListCreateAPIView):
    queryset = get_invoices_queryset()
    serializer_class = InvoiceSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = InvoiceFilter
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("User authentication is required")

        user_id = self.request.query_params.get("user_id")
        if not user_id:
            try:
                user_id = self.request.data.get("user_id")
            except Exception:
                pass

        if user_id:
            return self.queryset.filter(user_id=user_id)

        if user.role == "vendor":
            return self.queryset.filter(user=user)
        if user.role == "ydm":
            return self.queryset
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("User authentication is required")

        if user.role != "ydm":
            raise serializers.ValidationError(
                "User is not authorized to create invoices"
            )

        user_id = self.request.data.get("user_id") or self.request.query_params.get(
            "user_id"
        )
        if user_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            target_user = User.objects.filter(id=user_id).first()
            if not target_user:
                raise serializers.ValidationError("Target user not found")
        else:
            target_user = serializer.validated_data.get("user") or user

        validated_data = serializer.validated_data.copy()
        validated_data["user"] = target_user

        # Use create_invoice service
        create_invoice(created_by=user, **validated_data)


class InvoiceRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = get_invoices_queryset()
    serializer_class = InvoiceSerializer
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]

    def perform_update(self, serializer):
        instance = serializer.instance
        user = self.request.user
        new_is_approved = serializer.validated_data.get(
            "is_approved", instance.is_approved
        )
        # Use update_invoice_approval service
        update_invoice_approval(instance, new_is_approved, user)


class InvoiceReportListCreateView(generics.ListCreateAPIView):
    queryset = get_invoice_reports_queryset()
    serializer_class = ReportInvoiceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = InvoiceReportFilter
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]

    def perform_create(self, serializer):
        user = self.request.user
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("User authentication is required")

        # Use create_report service
        create_report(
            reported_by=user,
            invoice=serializer.validated_data["invoice"],
            comment=serializer.validated_data.get("comment", ""),
        )


class InvoiceReportRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = get_invoice_reports_queryset()
    serializer_class = ReportInvoiceSerializer
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
