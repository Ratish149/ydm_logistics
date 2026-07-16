import io

import openpyxl
from openpyxl.styles import Font, PatternFill

from logistics.filters import OrderFilter
from logistics.selectors import order_selector


def export_orders_to_excel(
    user,
    target_user_id=None,
    order_ids_input=None,
    filter_params=None,
) -> io.BytesIO:
    """
    Business service to filter client orders and build a formatted Excel spreadsheet.
    """
    # 1. Resolve target user & get base queryset
    if user and user.role == "ydm":
        target = target_user_id if target_user_id else None
    else:
        target = user

    queryset = order_selector.get_orders_for_client(target)

    # 2. Extract and filter by order_ids
    if order_ids_input:
        if isinstance(order_ids_input, str):
            order_ids = [
                int(x.strip()) for x in order_ids_input.split(",") if x.strip()
            ]
        elif isinstance(order_ids_input, list):
            order_ids = [int(x) for x in order_ids_input]
        else:
            raise ValueError(
                "Invalid order_ids format. Must be a list or a comma-separated list of integers."
            )
        queryset = queryset.filter(id__in=order_ids)

    # 3. Apply standard filters using OrderFilter
    if filter_params:
        filter_set = OrderFilter(filter_params, queryset=queryset)
        if not filter_set.is_valid():
            # We raise ValidationError or ValueError, views will catch/display
            raise ValueError(filter_set.errors)
        queryset = filter_set.qs

    # 4. Generate openpyxl workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orders"

    columns = [
        "ID",
        "Tracking Number",
        "External Order Code",
        "Sender Name",
        "Sender Phone",
        "Recipient Name",
        "Recipient Phone",
        "Recipient Email",
        "Recipient Address",
        "Recipient City",
        "Recipient District",
        "COD Amount",
        "Delivery Charge",
        "YDM Delivery Charge",
        "YDM Cancelled Charge",
        "Payment Type",
        "Status",
        "Is Rider Verified",
        "Delivery Location Type",
        "Created At",
    ]

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F4E79")
    for col_idx, col_name in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.font = header_font
        cell.fill = header_fill
        ws.column_dimensions[cell.column_letter].width = max(len(col_name) + 4, 16)

    for row_idx, order in enumerate(queryset, start=2):
        ws.cell(row=row_idx, column=1, value=order.id)
        ws.cell(row=row_idx, column=2, value=order.tracking_number)
        ws.cell(row=row_idx, column=3, value=order.external_order_code or "")
        ws.cell(row=row_idx, column=4, value=order.sender_name or "")
        ws.cell(row=row_idx, column=5, value=order.sender_phone or "")
        ws.cell(row=row_idx, column=6, value=order.recipient_name)
        ws.cell(row=row_idx, column=7, value=order.recipient_phone)
        ws.cell(row=row_idx, column=8, value=order.recipient_email or "")
        ws.cell(row=row_idx, column=9, value=order.recipient_address)
        ws.cell(row=row_idx, column=10, value=order.recipient_city or "")
        ws.cell(row=row_idx, column=11, value=order.recipient_district or "")
        ws.cell(row=row_idx, column=12, value=float(order.cod_amount))
        ws.cell(row=row_idx, column=13, value=float(order.delivery_charge))
        ws.cell(
            row=row_idx,
            column=14,
            value=float(order.ydm_delivery_charge)
            if order.ydm_delivery_charge is not None
            else "",
        )
        ws.cell(
            row=row_idx,
            column=15,
            value=float(order.ydm_cancelled_charge)
            if order.ydm_cancelled_charge is not None
            else "",
        )
        ws.cell(row=row_idx, column=16, value=order.payment_type)
        ws.cell(row=row_idx, column=17, value=order.get_status_display())
        ws.cell(
            row=row_idx, column=18, value="Yes" if order.is_rider_verified else "No"
        )
        ws.cell(row=row_idx, column=19, value=order.delivery_location_type or "")
        ws.cell(
            row=row_idx,
            column=20,
            value=order.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if order.created_at
            else "",
        )

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
