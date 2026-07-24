from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.authentication import APIKeyAuthentication
from payment.filters import (
    CodPaymentFilter,
    CodPaymentOrderFilter,
    DeliveryBillPaymentFilter,
    DeliveryBillPaymentOrderFilter,
)
from payment.selectors.cod_payment_selector import (
    get_cod_payment_orders_selector,
    get_cod_payments_selector,
    get_unpaid_cod_orders_selector,
)
from payment.selectors.delivery_bill_selector import (
    get_delivery_bill_orders_selector,
    get_delivery_bills_selector,
    get_unpaid_delivery_bill_orders_selector,
)
from payment.serializers import (
    CodPaymentListSerializer,
    CodPaymentOrderListSerializer,
    CodPaymentSerializer,
    DeliveryBillPaymentListSerializer,
    DeliveryBillPaymentSerializer,
)
from payment.services.cod_payment_service import create_cod_payment_service
from payment.services.delivery_bill_service import create_delivery_bill_service
from ydm.utils.pagination import CustomPagination


class CodPaymentListCreateAPIView(ListCreateAPIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CodPaymentSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CodPaymentFilter
    search_fields = ["payment_number", "user__username"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CodPaymentListSerializer
        return CodPaymentSerializer

    def get_queryset(self):
        user = self.request.user
        user_id = self.request.query_params.get("user_id")
        return get_cod_payments_selector(user=user, user_id=user_id)

    def perform_create(self, serializer):
        user = self.request.user
        orders = serializer.validated_data.get("orders", [])
        delivery_amount = serializer.validated_data.get("delivery_amount", 0.00)
        total_amount = serializer.validated_data.get("total_amount", 0.00)
        status_val = serializer.validated_data.get("status", "Pending")
        target_user = serializer.validated_data.get("user") or user

        cod_payment = create_cod_payment_service(
            user=target_user,
            created_by=user,
            orders=orders,
            delivery_amount=delivery_amount,
            total_amount=total_amount,
            status=status_val,
        )
        serializer.instance = cod_payment


class CodPaymentRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CodPaymentSerializer
    lookup_field = "pk"

    def get_queryset(self):
        user = self.request.user
        return get_cod_payments_selector(user=user)


class CodPaymentOrdersListAPIView(ListCreateAPIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CodPaymentOrderListSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CodPaymentOrderFilter
    search_fields = ["tracking_number", "recipient_name", "recipient_phone"]

    def get_queryset(self):
        user = self.request.user
        user_id = self.request.query_params.get("user_id")
        return get_cod_payment_orders_selector(user=user, user_id=user_id)


class UnpaidCodOrdersListAPIView(ListCreateAPIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CodPaymentOrderListSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CodPaymentOrderFilter
    search_fields = ["tracking_number", "recipient_name", "recipient_phone"]

    def get_queryset(self):
        user = self.request.user
        user_id = self.request.query_params.get("user_id")
        return get_unpaid_cod_orders_selector(user=user, user_id=user_id)


class DeliveryBillPaymentListCreateAPIView(ListCreateAPIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DeliveryBillPaymentSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = DeliveryBillPaymentFilter
    search_fields = ["bill_number", "user__username"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return DeliveryBillPaymentListSerializer
        return DeliveryBillPaymentSerializer

    def get_queryset(self):
        user = self.request.user
        user_id = self.request.query_params.get("user_id")
        return get_delivery_bills_selector(user=user, user_id=user_id)

    def perform_create(self, serializer):
        user = self.request.user
        orders = serializer.validated_data.get("orders", [])
        delivery_amount = serializer.validated_data.get("delivery_amount", 0.00)
        status_val = serializer.validated_data.get("status", "Pending")
        target_user = serializer.validated_data.get("user") or user

        delivery_bill = create_delivery_bill_service(
            user=target_user,
            created_by=user,
            orders=orders,
            delivery_amount=delivery_amount,
            status=status_val,
        )
        serializer.instance = delivery_bill


class DeliveryBillPaymentRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DeliveryBillPaymentSerializer
    lookup_field = "pk"

    def get_queryset(self):
        user = self.request.user
        return get_delivery_bills_selector(user=user)


class DeliveryBillPaymentOrdersListAPIView(ListCreateAPIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CodPaymentOrderListSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = DeliveryBillPaymentOrderFilter
    search_fields = ["tracking_number", "recipient_name", "recipient_phone"]

    def get_queryset(self):
        user = self.request.user
        user_id = self.request.query_params.get("user_id")
        return get_delivery_bill_orders_selector(user=user, user_id=user_id)


class UnpaidDeliveryBillOrdersListAPIView(ListCreateAPIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CodPaymentOrderListSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = DeliveryBillPaymentOrderFilter
    search_fields = ["tracking_number", "recipient_name", "recipient_phone"]

    def get_queryset(self):
        user = self.request.user
        user_id = self.request.query_params.get("user_id")
        return get_unpaid_delivery_bill_orders_selector(user=user, user_id=user_id)
