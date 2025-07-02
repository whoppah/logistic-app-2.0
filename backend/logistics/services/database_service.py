#backend/logistics/services/database_service.py
import time
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError
from django.conf import settings


class DatabaseService:
    def __init__(self):
        self.engine = self._build_engine()

    def _build_engine(self):
        """
        Use Django's DATABASES['external'] settings to configure the SQLAlchemy engine
        """
        db = settings.DATABASES["external"]

        db_url = URL.create(
            drivername="postgresql+psycopg2",
            username=db["USER"],
            password=db["PASSWORD"],
            host=db["HOST"],
            port=db["PORT"],
            database=db["NAME"]
        )
        return create_engine(db_url, pool_pre_ping=True)

    def execute_query_with_retries(self, query, max_retries=5, delay=15):
        attempt = 0
        while attempt < max_retries:
            try:
                with self.engine.connect() as connection:
                    result = connection.execute(text(query))
                    return pd.DataFrame(result.fetchall(), columns=result.keys())
            except OperationalError as e:
                print(f"⛔ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                else:
                    print("❌ Max retries reached. Query failed.")
            attempt += 1
        return pd.DataFrame()

    def get_orders_dataframe(self, partner_value: str) -> pd.DataFrame:
        """Query and return a DataFrame of recent orders related to a logistics partner."""
        query = """
        SELECT 
            CAST(sales_order.state AS TEXT) AS status,
            CAST(sales_order.id AS TEXT) AS order_id,
            DATE(sales_order.created AT TIME ZONE 'CET') AS order_creation_date,
            CAST(brenger_brengershipment.tracking_id AS TEXT) AS tracking_id,
            catalog_product.title AS product_name,
            CAST(sales_order.product_id AS TEXT) AS product_id,
            catalog_product.weight,
            CASE
                WHEN external_shipping_method_id IS NOT NULL THEN 'brenger'
                WHEN outsource_shipping_method IS NOT NULL THEN outsource_shipping_method
                WHEN external_shipping_method_id IS NULL AND sales_order.delivery_method='pickup' THEN 'pickup'
                WHEN sales_order.delivery_method='delivery' AND sales_order.shipping_method_id='aa1bd039-164f-4e96-a8dd-29fde48d2006' THEN 'Whoppah-Courier'
                WHEN sales_order.delivery_method='delivery' AND sales_order.shipping_method_id IN 
                    ('3414d1f9-a8d5-4aa5-8925-31bac05704ad','a8af2c5d-9299-4abd-a32c-8c8780815da9','e0523a1c-e78c-4574-a6e8-23755398885f')
                    THEN 'Postal Delivery'
                WHEN sales_order.delivery_method='delivery' AND sales_order.shipping_method_id='219c6f0f-5ed6-45cc-aeaf-7539a79e8b02' THEN 'Custom'
            END AS external_courier_provider,
            CASE
                WHEN category_level_0='furniture' THEN category_level_1
                ELSE category_level_0
            END AS cat_level_1_and_2,
            CASE
                WHEN category_level_0='furniture' THEN category_level_2
                ELSE category_level_1
            END AS cat_level_2_and_3,
            catalog_product.number_of_items,
            sales_order.shipping_excl_vat,
            CAST(buyer_info.id AS TEXT) AS buyer_id,
            buyer_info.postal_code AS buyer_post_code,
            CAST(shipment_id AS TEXT) AS shipment_id,
            buyer_info.country AS buyer_country,
            seller_info.country AS seller_country,
            height, width, depth,
            seller_info.postal_code AS seller_post_code
        FROM sales_order
        LEFT JOIN catalog_product ON sales_order.product_id = catalog_product.id
        LEFT JOIN info_users buyer_info ON buyer_info.id = sales_order.buyer_id
        LEFT JOIN info_users seller_info ON seller_info.id = sales_order.merchant_id
        LEFT JOIN whoppah_sale_services ON whoppah_sale_services.product_id = sales_order.product_id
        LEFT JOIN category_level_and_brand ON category_level_and_brand.product_id = sales_order.product_id
        LEFT JOIN brenger_brengerappointment ON brenger_brengerappointment.order_id = sales_order.id
        LEFT JOIN brenger_brengershipment ON brenger_brengershipment.brenger_appointment_id = brenger_brengerappointment.id
        WHERE sales_order.state NOT IN ('expired', 'canceled')
        AND sales_order.created >= NOW() - INTERVAL '6 months'
        AND whoppah_sale_services.product_id IS NULL
        ORDER BY order_creation_date DESC;
        """

        df = self.execute_query_with_retries(query)
        if not df.empty:
            df.rename(columns={"order_id": "Order ID"}, inplace=True)
            df['order_creation_date'] = pd.to_datetime(df['order_creation_date'], errors='coerce')
            df[['height', 'width', 'depth']] = df[['height', 'width', 'depth']].fillna(0)
            df["weight"] = df["weight"].astype(float).apply(lambda x: format(x, '.2f'))
            df["buyer_country-seller_country"] = df["buyer_country"].fillna("") + "-" + df["seller_country"].fillna("")
        return df
