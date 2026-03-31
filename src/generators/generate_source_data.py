from __future__ import annotations

import random
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import List

import pandas as pd
from faker import Faker


SEED = 42
faker = Faker()
Faker.seed(SEED)
random.seed(SEED)


BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "data" / "source"


def q2(value: float | Decimal) -> float:
    """Round to 2 decimals using financial-style rounding."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class Config:
    num_customers: int = 1000
    num_products: int = 200
    num_orders: int = 5000
    min_items_per_order: int = 1
    max_items_per_order: int = 4


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_customers(config: Config) -> pd.DataFrame:
    rows = []
    used_emails = set()

    for customer_id in range(1, config.num_customers + 1):
        first_name = faker.first_name()
        last_name = faker.last_name()

        email = faker.unique.email()
        while email in used_emails:
            email = faker.unique.email()
        used_emails.add(email)

        rows.append(
            {
                "customer_id": customer_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email.lower(),
                "signup_date": faker.date_between(start_date="-3y", end_date="-30d"),
                "country_code": random.choice(["MX", "US", "CO", "AR", "CL"]),
                "is_active": random.random() < 0.92,
            }
        )

    return pd.DataFrame(rows)


def generate_products(config: Config) -> pd.DataFrame:
    categories = ["electronics", "home", "sports", "fashion", "books", "beauty"]
    adjectives = ["Premium", "Smart", "Portable", "Classic", "Essential", "Eco"]
    product_types = ["Headphones", "Bottle", "Backpack", "Lamp", "Notebook", "Shoes", "Watch"]

    rows = []

    for product_id in range(1, config.num_products + 1):
        product_name = f"{random.choice(adjectives)} {random.choice(product_types)}"
        rows.append(
            {
                "product_id": product_id,
                "product_name": product_name,
                "category": random.choice(categories),
                "unit_price": q2(random.uniform(5, 500)),
                "is_active": random.random() < 0.95,
                "created_at": faker.date_time_between(start_date="-2y", end_date="-60d"),
            }
        )

    return pd.DataFrame(rows)


def generate_orders(
    config: Config,
    customers_df: pd.DataFrame,
) -> pd.DataFrame:
    statuses = ["created", "paid", "cancelled"]
    rows = []

    customer_ids = customers_df["customer_id"].tolist()

    for order_id in range(1, config.num_orders + 1):
        order_status = random.choices(
            population=statuses,
            weights=[0.10, 0.82, 0.08],
            k=1,
        )[0]

        rows.append(
            {
                "order_id": order_id,
                "customer_id": random.choice(customer_ids),
                "order_date": faker.date_time_between(start_date="-18m", end_date="now"),
                "order_status": order_status,
                "currency": "USD",
                "total_amount": 0.0,  # placeholder, updated after order_items generation
            }
        )

    return pd.DataFrame(rows)


def generate_order_items(
    config: Config,
    orders_df: pd.DataFrame,
    products_df: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    order_item_id = 1

    active_products = products_df[products_df["is_active"] == True]["product_id"].tolist()
    product_prices = products_df.set_index("product_id")["unit_price"].to_dict()

    for order_id in orders_df["order_id"].tolist():
        num_items = random.randint(config.min_items_per_order, config.max_items_per_order)
        selected_products = random.sample(active_products, k=num_items)

        for product_id in selected_products:
            quantity = random.randint(1, 3)
            current_price = product_prices[product_id]

            # small price variation to simulate historical purchase price
            purchase_unit_price = q2(current_price * random.uniform(0.90, 1.10))
            line_amount = q2(quantity * purchase_unit_price)

            rows.append(
                {
                    "order_item_id": order_item_id,
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": purchase_unit_price,
                    "line_amount": line_amount,
                }
            )
            order_item_id += 1

    return pd.DataFrame(rows)


def update_order_totals(
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
) -> pd.DataFrame:
    totals = (
        order_items_df.groupby("order_id", as_index=False)["line_amount"]
        .sum()
        .rename(columns={"line_amount": "calculated_total_amount"})
    )

    merged = orders_df.merge(totals, on="order_id", how="left")
    merged["total_amount"] = merged["calculated_total_amount"].fillna(0).map(q2)
    merged = merged.drop(columns=["calculated_total_amount"])

    return merged


def generate_payments(orders_df: pd.DataFrame) -> pd.DataFrame:
    payment_methods = ["credit_card", "debit_card", "paypal", "cash"]
    rows = []
    payment_id = 1

    for row in orders_df.itertuples(index=False):
        if row.order_status == "paid":
            payment_status = "succeeded"
            payment_amount = q2(row.total_amount)
        elif row.order_status == "cancelled":
            payment_status = random.choice(["failed", "cancelled"])
            payment_amount = 0.0
        else:
            payment_status = random.choice(["pending", "failed"])
            payment_amount = 0.0 if payment_status == "failed" else q2(row.total_amount)

        rows.append(
            {
                "payment_id": payment_id,
                "order_id": row.order_id,
                "payment_date": row.order_date,
                "payment_method": random.choice(payment_methods),
                "payment_status": payment_status,
                "payment_amount": payment_amount,
            }
        )
        payment_id += 1

    return pd.DataFrame(rows)


def save_csv(dataframe: pd.DataFrame, filename: str) -> None:
    output_path = OUTPUT_DIR / filename
    dataframe.to_csv(output_path, index=False)


def main() -> None:
    config = Config()
    ensure_output_dir()

    customers_df = generate_customers(config)
    products_df = generate_products(config)
    orders_df = generate_orders(config, customers_df)
    order_items_df = generate_order_items(config, orders_df, products_df)
    orders_df = update_order_totals(orders_df, order_items_df)
    payments_df = generate_payments(orders_df)

    save_csv(customers_df, "customers.csv")
    save_csv(products_df, "products.csv")
    save_csv(orders_df, "orders.csv")
    save_csv(order_items_df, "order_items.csv")
    save_csv(payments_df, "payments.csv")

    print("Source datasets generated successfully:")
    print(f"- customers: {len(customers_df)}")
    print(f"- products: {len(products_df)}")
    print(f"- orders: {len(orders_df)}")
    print(f"- order_items: {len(order_items_df)}")
    print(f"- payments: {len(payments_df)}")


if __name__ == "__main__":
    main()