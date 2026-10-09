from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from backend.repositories import create_shipment, get_shipment
from backend.schemas import ShipmentImportResponse


COLUMN_ALIASES = {
    "shipment_id": [
        "shipment_id",
        "shipment id",
        "shipment",
        "order_id",
        "order id",
        "order",
        "id",
    ],
    "tracking_number": [
        "tracking_number",
        "tracking number",
        "tracking",
    ],
    "carrier": [
        "carrier",
        "shipping carrier",
    ],
    "origin": [
        "origin",
        "origin address",
        "origin location",
        "source",
    ],
    "destination": [
        "destination",
        "destination address",
        "destination location",
        "delivery location",
    ],
    "estimated_arrival": [
        "estimated_arrival",
        "estimated arrival",
        "eta",
        "expected delivery",
        "expected arrival",
    ],
    "current_status": [
        "current_status",
        "current status",
        "status",
        "shipment status",
        "delivery status",
    ],
    "shipping_mode": [
        "shipping_mode",
        "shipping mode",
        "shipping_method",
        "shipping method",
        "service level",
    ],
    "origin_latitude": [
        "origin_latitude",
        "origin latitude",
        "origin_lat",
    ],
    "origin_longitude": [
        "origin_longitude",
        "origin longitude",
        "origin_lon",
        "origin lng",
    ],
    "destination_latitude": [
        "destination_latitude",
        "destination latitude",
        "destination_lat",
    ],
    "destination_longitude": [
        "destination_longitude",
        "destination longitude",
        "destination_lon",
        "destination lng",
    ],
}


MODEL_FEATURE_ALIASES = {
    "scheduled_days": [
        "scheduled_days",
        "scheduled days",
        "scheduled_shipping_days",
        "days for shipment scheduled",
    ],
    "market": [
        "market",
    ],
    "order_region": [
        "order_region",
        "order region",
        "region",
    ],
    "order_country": [
        "order_country",
        "order country",
        "country",
    ],
    "item_count": [
        "item_count",
        "item count",
        "number of items",
    ],
    "total_quantity": [
        "total_quantity",
        "total quantity",
        "quantity",
    ],
    "avg_product_price": [
        "avg_product_price",
        "average product price",
        "avg product price",
    ],
    "total_sales": [
        "total_sales",
        "total sales",
        "sales",
    ],
    "avg_discount_rate": [
        "avg_discount_rate",
        "average discount rate",
        "avg discount rate",
    ],
    "customer_segment": [
        "customer_segment",
        "customer segment",
        "segment",
    ],
}


def _normalize_column_name(value: str) -> str:
    return (
        str(value)
        .strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
    )


def _metadata_key(value: str) -> str:
    return (
        str(value)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def _find_column(
    columns: list[str],
    aliases: list[str],
) -> str | None:
    normalized = {
        _normalize_column_name(column): column
        for column in columns
    }

    for alias in aliases:
        match = normalized.get(_normalize_column_name(alias))

        if match is not None:
            return match

    return None


def _build_column_mapping(
    columns: list[str],
) -> dict[str, str]:
    mapping: dict[str, str] = {}

    aliases = {
        **COLUMN_ALIASES,
        **MODEL_FEATURE_ALIASES,
    }

    for canonical_name, field_aliases in aliases.items():
        source_column = _find_column(
            columns,
            field_aliases,
        )

        if source_column is not None:
            mapping[canonical_name] = source_column

    return mapping


def _clean_value(value) -> str | None:
    if pd.isna(value):
        return None

    value = str(value).strip()

    return value if value else None


def _clean_metadata_value(value) -> Any:
    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, datetime):
        return value.isoformat()

    if hasattr(value, "item"):
        try:
            value = value.item()
        except (ValueError, TypeError):
            pass

    if isinstance(value, float) and value.is_integer():
        return int(value)

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


def _parse_datetime(value) -> datetime | None:
    if pd.isna(value) or value is None:
        return None

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return None

    return parsed.to_pydatetime()


def _parse_coordinate(value) -> float | None:
    if pd.isna(value) or value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_file(
    file_bytes: bytes,
    filename: str,
) -> pd.DataFrame:
    extension = filename.lower().rsplit(".", 1)[-1]

    if extension == "csv":
        return pd.read_csv(
            BytesIO(file_bytes),
            encoding="utf-8",
        )

    if extension == "xlsx":
        return pd.read_excel(
            BytesIO(file_bytes),
            engine="openpyxl",
        )

    raise ValueError(
        "Unsupported file type. Upload a CSV or XLSX file."
    )


def _build_metadata(
    row: pd.Series,
    columns: list[str],
    mapping: dict[str, str],
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}

    for column in columns:
        value = _clean_metadata_value(row[column])

        if value is not None:
            metadata[_metadata_key(column)] = value

    for canonical_name in MODEL_FEATURE_ALIASES:
        source_column = mapping.get(canonical_name)

        if source_column is not None:
            value = _clean_metadata_value(row[source_column])

            if value is not None:
                metadata[canonical_name] = value

    return metadata


def import_shipments(
    db: Session,
    company_id: int,
    file_bytes: bytes,
    filename: str,
) -> ShipmentImportResponse:
    dataframe = _read_file(file_bytes, filename)

    if dataframe.empty:
        raise ValueError(
            "The uploaded file contains no shipment rows."
        )

    columns = [str(column) for column in dataframe.columns]

    mapping = _build_column_mapping(columns)

    if "shipment_id" not in mapping:
        raise ValueError(
            "Could not identify a shipment ID column. "
            "Expected a column such as shipment_id, shipment id, "
            "order_id, or order id."
        )

    imported = 0
    skipped = 0
    errors: list[str] = []

    for row_number, (_, row) in enumerate(
        dataframe.iterrows(),
        start=2,
    ):
        try:
            shipment_id = _clean_value(
                row[mapping["shipment_id"]]
            )

            if not shipment_id:
                skipped += 1
                errors.append(
                    f"Row {row_number}: missing shipment ID."
                )
                continue

            if get_shipment(
                db,
                company_id,
                shipment_id,
            ):
                skipped += 1
                continue

            def value(field: str) -> str | None:
                column = mapping.get(field)

                if column is None:
                    return None

                return _clean_value(row[column])

            origin_latitude = _parse_coordinate(
                row[mapping["origin_latitude"]]
            ) if "origin_latitude" in mapping else None

            origin_longitude = _parse_coordinate(
                row[mapping["origin_longitude"]]
            ) if "origin_longitude" in mapping else None

            destination_latitude = _parse_coordinate(
                row[mapping["destination_latitude"]]
            ) if "destination_latitude" in mapping else None

            destination_longitude = _parse_coordinate(
                row[mapping["destination_longitude"]]
            ) if "destination_longitude" in mapping else None

            origin_coordinates = None

            if (
                origin_latitude is not None
                and origin_longitude is not None
            ):
                origin_coordinates = {
                    "latitude": origin_latitude,
                    "longitude": origin_longitude,
                }

            destination_coordinates = None

            if (
                destination_latitude is not None
                and destination_longitude is not None
            ):
                destination_coordinates = {
                    "latitude": destination_latitude,
                    "longitude": destination_longitude,
                }

            metadata = _build_metadata(
                row=row,
                columns=columns,
                mapping=mapping,
            )

            create_shipment(
                db=db,
                company_id=company_id,
                shipment_id=shipment_id,
                tracking_number=value("tracking_number"),
                carrier=value("carrier"),
                origin=value("origin"),
                destination=value("destination"),
                origin_coordinates=origin_coordinates,
                destination_coordinates=destination_coordinates,
                estimated_arrival=(
                    _parse_datetime(
                        row[mapping["estimated_arrival"]]
                    )
                    if "estimated_arrival" in mapping
                    else None
                ),
                current_status=value("current_status"),
                shipping_mode=value("shipping_mode"),
                metadata_json=metadata,
            )

            imported += 1

        except Exception as exc:
            db.rollback()
            errors.append(
                f"Row {row_number}: {exc}"
            )

    return ShipmentImportResponse(
        imported=imported,
        skipped=skipped,
        errors=errors,
    )