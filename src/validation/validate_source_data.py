from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
SOURCE_DIR = BASE_DIR / "data" / "source"


class ValidationError(Exception):
    """Raised when one or more source data validations fail."""


def load_csv(filename: str) -> pd.DataFrame:
    file_path = SOURCE_DIR / filename

    if not file_path.exists():
        raise ValidationError(f"Missing required file: {filename}")

    return pd.read_csv(file_path)


def assert_no_nulls(df: pd.DataFrame, column_name: str, table_name: str) -> None:
    null_count = df[column_name].isna().sum()
    if null_count > 0:
        raise ValidationError(
            f"{table_name}.{column_name} contains {null_count} null values"
        )


def assert_unique(df: pd.DataFrame, column_name: str, table_name: str) -> None:
    duplicate_count = df[column_name].duplicated().sum()
    if duplicate_count > 0:
        raise ValidationError(
            f"{table_name}.{column_name} contains {duplicate_count} duplicate values"
        )


def assert_fk_exists(
    child_df: pd.DataFrame,
    child_column: str,
    parent_df: pd.DataFrame,
    parent_column: str,
    child_table_name: str,
    parent_table_name: str,
) -> None:
    invalid_values = set(child_df[child_column]) - set(parent_df[parent_column])

    if invalid_values:
        sample = sorted(list(invalid_values))[:5]
        raise ValidationError(
            f"Invalid FK values in {child_table_name}.{child_column} "
            f"referencing {parent_table_name}.{parent_column}. "
            f"Sample invalid values: {sample}"
        )


def assert_positive_row_count(df: pd.DataFrame, table_name: str) -> None:
    if df.empty:
        raise ValidationError(f"{table_name} is empty")


def assert_line_amounts(order_items_df: pd.DataFrame) -> None:
    expected = (order_items_df["quantity"] * order_items_df["unit_price"]).round(2)
    actual = order_items_df["line_amount"].round(2)

    invalid_rows = order_items_df.loc[expected != actual]

    if not invalid_rows.empty:
        raise ValidationError(
            f"order_items.line_amount mismatch found in {len(invalid_rows)} rows"
        )


def assert_order_totals(
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
) -> None:
    calculated = (
        order_items_df.groupby("order_id", as_index=False)["line_amount"]
        .sum()
        .rename(columns={"line_amount": "calculated_total_amount"})
    )

    merged = orders_df.merge(
        calculated,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    merged["calculated_total_amount"] = merged["calculated_total_amount"].fillna(0).round(2)
    merged["total_amount"] = merged["total_amount"].round(2)

    invalid_rows = merged.loc[
        merged["total_amount"] != merged["calculated_total_amount"]
    ]

    if not invalid_rows.empty:
        raise ValidationError(
            f"orders.total_amount mismatch found in {len(invalid_rows)} rows"
        )


def assert_every_order_has_items(
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
) -> None:
    orders_with_items = set(order_items_df["order_id"])
    missing_orders = set(orders_df["order_id"]) - orders_with_items

    if missing_orders:
        sample = sorted(list(missing_orders))[:5]
        raise ValidationError(
            f"Orders without items found. Sample order_id values: {sample}"
        )


def assert_email_uniqueness(customers_df: pd.DataFrame) -> None:
    duplicate_count = customers_df["email"].str.lower().duplicated().sum()
    if duplicate_count > 0:
        raise ValidationError(
            f"customers.email contains {duplicate_count} duplicate values"
        )


def validate_source_data() -> None:
    customers_df = load_csv("customers.csv")
    products_df = load_csv("products.csv")
    orders_df = load_csv("orders.csv")
    order_items_df = load_csv("order_items.csv")
    payments_df = load_csv("payments.csv")

    # Row-level sanity checks
    assert_positive_row_count(customers_df, "customers")
    assert_positive_row_count(products_df, "products")
    assert_positive_row_count(orders_df, "orders")
    assert_positive_row_count(order_items_df, "order_items")
    assert_positive_row_count(payments_df, "payments")

    # Primary key checks
    assert_no_nulls(customers_df, "customer_id", "customers")
    assert_no_nulls(products_df, "product_id", "products")
    assert_no_nulls(orders_df, "order_id", "orders")
    assert_no_nulls(order_items_df, "order_item_id", "order_items")
    assert_no_nulls(payments_df, "payment_id", "payments")

    assert_unique(customers_df, "customer_id", "customers")
    assert_unique(products_df, "product_id", "products")
    assert_unique(orders_df, "order_id", "orders")
    assert_unique(order_items_df, "order_item_id", "order_items")
    assert_unique(payments_df, "payment_id", "payments")

    # Natural/business checks
    assert_email_uniqueness(customers_df)

    # Foreign key checks
    assert_fk_exists(
        orders_df,
        "customer_id",
        customers_df,
        "customer_id",
        "orders",
        "customers",
    )
    assert_fk_exists(
        order_items_df,
        "order_id",
        orders_df,
        "order_id",
        "order_items",
        "orders",
    )
    assert_fk_exists(
        order_items_df,
        "product_id",
        products_df,
        "product_id",
        "order_items",
        "products",
    )
    assert_fk_exists(
        payments_df,
        "order_id",
        orders_df,
        "order_id",
        "payments",
        "orders",
    )

    # Business logic checks
    assert_every_order_has_items(orders_df, order_items_df)
    assert_line_amounts(order_items_df)
    assert_order_totals(orders_df, order_items_df)

    print("All source data validations passed successfully.")


def main() -> None:
    try:
        validate_source_data()
    except ValidationError as exc:
        print(f"VALIDATION FAILED: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()