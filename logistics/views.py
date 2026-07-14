import io

from django.http import HttpResponse
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.authentication import APIKeyAuthentication
from account.permissions import HasValidAPIKey
from logistics.filters import OrderFilter
from logistics.selectors import order_selector
from logistics.serializers import (
    OrderCommentSerializer,
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderStatusUpdateSerializer,
)


class OrderListCreateAPI(ListCreateAPIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [HasValidAPIKey]
    filterset_class = OrderFilter

    def _resolve_target_user(self):
        """
        Returns the user whose orders should be listed.
        - ydm role: can pass ?user_id=<id> to see any user's orders.
          If no user_id is given, returns all orders (no user filter).
        - Everyone else: always scoped to their own authenticated user.
        """
        request = self.request
        if request.user.role == "ydm":
            user_id = request.query_params.get("user_id")
            if user_id:
                return user_id  # numeric id string — resolved in selector
            return None  # ydm with no filter → all orders
        return request.user

    def get_queryset(self):
        target = self._resolve_target_user()
        return order_selector.get_orders_for_client(target)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        response_serializer = OrderDetailSerializer(
            order, context=self.get_serializer_context()
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailAPI(RetrieveUpdateDestroyAPIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [HasValidAPIKey]
    serializer_class = OrderDetailSerializer
    lookup_field = "tracking_number"
    lookup_url_kwarg = "tracking_number"

    def get_queryset(self):
        return order_selector.get_orders_for_client(self.request.user)


class OrderStatusUpdateAPI(APIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [HasValidAPIKey]

    def post(self, request, tracking_number):
        order = order_selector.get_order_by_tracking(
            user=request.user, tracking_number=tracking_number
        )
        if not order:
            return Response(
                {"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # request.auth is the APIKey object when authenticated via APIKeyAuthentication
        api_key_obj = request.auth if hasattr(request.auth, "webhook_url") else None
        webhook_url = api_key_obj.webhook_url if api_key_obj else None

        serializer = OrderStatusUpdateSerializer(
            data=request.data,
            context={"webhook_url": webhook_url, "user": request.user},
        )
        if serializer.is_valid():
            updated_order = serializer.update(order, serializer.validated_data)
            response_serializer = OrderDetailSerializer(updated_order)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WebhookConfigAPI(APIView):
    """
    Manage the webhook URL tied to the authenticated API key.

    GET    api/ydm/webhook/  — Return the currently registered webhook URL.
    POST   api/ydm/webhook/  — Register or update the webhook URL.
                               Body: { "webhook_url": "https://example.com/hook" }
    DELETE api/ydm/webhook/  — Remove the webhook URL.
    """

    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [HasValidAPIKey]

    def _get_api_key(self, request):
        """Return the APIKey instance when authenticated via API key, else None."""
        return request.auth if hasattr(request.auth, "webhook_url") else None

    def get(self, request):
        api_key = self._get_api_key(request)
        if not api_key:
            return Response(
                {"detail": "Webhook management requires API key authentication."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(
            {
                "webhook_url": api_key.webhook_url,
                "message": (
                    "No webhook URL registered."
                    if not api_key.webhook_url
                    else "Webhook is active."
                ),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        api_key = self._get_api_key(request)
        if not api_key:
            return Response(
                {"detail": "Webhook management requires API key authentication."},
                status=status.HTTP_403_FORBIDDEN,
            )

        webhook_url = request.data.get("webhook_url", "").strip()
        if not webhook_url:
            return Response(
                {"detail": "webhook_url is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (
            webhook_url.startswith("http://") or webhook_url.startswith("https://")
        ):
            return Response(
                {"detail": "webhook_url must start with http:// or https://."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        api_key.webhook_url = webhook_url
        api_key.save(update_fields=["webhook_url"])

        return Response(
            {
                "webhook_url": api_key.webhook_url,
                "message": "Webhook URL registered successfully.",
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        api_key = self._get_api_key(request)
        if not api_key:
            return Response(
                {"detail": "Webhook management requires API key authentication."},
                status=status.HTTP_403_FORBIDDEN,
            )

        api_key.webhook_url = None
        api_key.save(update_fields=["webhook_url"])

        return Response(
            {"message": "Webhook URL removed successfully."},
            status=status.HTTP_200_OK,
        )


class OrderCommentListCreateAPI(APIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [HasValidAPIKey]

    def get(self, request, tracking_number):
        order = order_selector.get_order_by_tracking(
            user=request.user, tracking_number=tracking_number
        )
        if not order:
            return Response(
                {"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND
            )

        comments = order.comments.all()
        serializer = OrderCommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, tracking_number):
        order = order_selector.get_order_by_tracking(
            user=request.user, tracking_number=tracking_number
        )
        if not order:
            return Response(
                {"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = OrderCommentSerializer(data=request.data)
        if serializer.is_valid():
            from logistics.services.order_service import create_order_comment

            comment = create_order_comment(
                order=order,
                commented_by=request.user,
                message=serializer.validated_data["message"],
                comment_type=serializer.validated_data.get("comment_type", "GENERAL"),
            )
            response_serializer = OrderCommentSerializer(comment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Template columns exposed to the vendor. Sender fields are derived from the
# authenticated user so they are intentionally excluded from the template.
# ---------------------------------------------------------------------------
_TEMPLATE_COLUMNS = [
    "external_order_code",
    "recipient_name",
    "recipient_phone",
    "recipient_email",
    "recipient_address",
    "recipient_city",
    "recipient_district",
    "cod_amount",
    "delivery_charge",
    "payment_type",
    "product",
    "special_instructions",
    "remarks",
]

_SAMPLE_ROW = [
    "ORD-001",
    "John Doe",
    "9800000000",
    "john@example.com",
    "123 Main Street, Kathmandu",
    "Kathmandu",
    "Kathmandu",
    "500.00",
    "100.00",
    "COD",
    "",
    "Handle with care",
    "Sample order",
]


class OrderTemplateDownloadAPI(APIView):
    """
    GET  /api/orders/template/
    Returns an Excel (.xlsx) file pre-populated with the required column
    headers and one sample data row.  Sender details are NOT included
    because they are automatically derived from the authenticated user.
    """

    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [HasValidAPIKey]

    def get(self, request):
        import openpyxl
        from openpyxl.styles import Font, PatternFill

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Orders"

        # Header row
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="1F4E79")
        for col_idx, col_name in enumerate(_TEMPLATE_COLUMNS, start=1):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.font = header_font
            cell.fill = header_fill
            ws.column_dimensions[cell.column_letter].width = max(len(col_name) + 4, 16)

        # Sample data row
        for col_idx, value in enumerate(_SAMPLE_ROW, start=1):
            ws.cell(row=2, column=col_idx, value=value)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="orders_template.xlsx"'
        return response


class OrderImportAPI(APIView):
    """
    POST  /api/orders/import/
    Accepts a multipart/form-data upload with key ``file`` containing an
    Excel (.xlsx) file that matches the template produced by
    ``OrderTemplateDownloadAPI``.

    Sender details (name, phone, address, e-mail) are taken from the
    authenticated user rather than from the spreadsheet.

    Returns a summary:
        {
            "created": <int>,
            "errors":  [ {"row": <int>, "detail": <str>}, … ]
        }
    """

    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = [HasValidAPIKey]
    parser_classes = [MultiPartParser]

    def post(self, request):
        import openpyxl

        uploaded = request.FILES.get("file")
        if not uploaded:
            return Response(
                {"detail": "No file provided. Send the Excel file as 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not uploaded.name.endswith(".xlsx"):
            return Response(
                {"detail": "Only .xlsx files are supported."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            wb = openpyxl.load_workbook(uploaded, data_only=True)
        except Exception:
            return Response(
                {
                    "detail": "Could not parse the uploaded file. Ensure it is a valid .xlsx."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ws = wb.active
        headers = [cell.value for cell in ws[1]]

        # Validate headers
        missing = [c for c in _TEMPLATE_COLUMNS if c not in headers]
        if missing:
            return Response(
                {"detail": f"Missing columns: {', '.join(missing)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        col_index = {name: idx for idx, name in enumerate(headers)}

        from logistics.services.order_service import create_order

        user = request.user
        created_count = 0
        row_errors = []

        for row_num, row in enumerate(
            ws.iter_rows(min_row=2, values_only=True), start=2
        ):
            # Skip completely blank rows
            if all(v is None or str(v).strip() == "" for v in row):
                continue

            def cell(col_name):
                idx = col_index.get(col_name)
                if idx is None:
                    return None
                val = row[idx]
                return str(val).strip() if val is not None else None

            recipient_name = cell("recipient_name")
            recipient_phone = cell("recipient_phone")
            recipient_address = cell("recipient_address")

            if not recipient_name or not recipient_phone or not recipient_address:
                row_errors.append({
                    "row": row_num,
                    "detail": "recipient_name, recipient_phone, and recipient_address are required.",
                })
                continue

            # Safely coerce numeric columns
            def decimal_or_zero(col_name):
                val = cell(col_name)
                try:
                    return float(val) if val else 0.0
                except (ValueError, TypeError):
                    return 0.0

            try:
                create_order(
                    user=user,
                    recipient_name=recipient_name,
                    recipient_phone=recipient_phone,
                    recipient_address=recipient_address,
                    recipient_email=cell("recipient_email"),
                    recipient_city=cell("recipient_city"),
                    recipient_district=cell("recipient_district"),
                    external_order_code=cell("external_order_code"),
                    cod_amount=decimal_or_zero("cod_amount"),
                    delivery_charge=decimal_or_zero("delivery_charge"),
                    payment_type=cell("payment_type") or "COD",
                    special_instructions=cell("special_instructions"),
                    remarks=cell("remarks"),
                )
                created_count += 1
            except Exception as exc:  # noqa: BLE001
                row_errors.append({"row": row_num, "detail": str(exc)})

        return Response(
            {"created": created_count, "errors": row_errors},
            status=status.HTTP_201_CREATED
            if created_count
            else status.HTTP_400_BAD_REQUEST,
        )
