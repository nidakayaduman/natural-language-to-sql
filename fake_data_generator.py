import pandas as pd
import numpy as np
import random
from faker import Faker
from datetime import datetime
import os

# Ortam ayarları
fake = Faker("tr_TR")
np.random.seed(42)
random.seed(42)

# Veri klasörü
DATA_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# -----------------------
# 1. CUSTOMERS.csv üretimi
# -----------------------
num_customers = 70000
cities = ['Istanbul', 'Ankara', 'Izmir', 'Bursa', 'Adana', 'Antalya', 'Konya']
segments = ['Bireysel', 'KOBI', 'Kurumsal']
credit_tiers = [1, 2, 3, 4, 5]

customers = []

for i in range(1, num_customers + 1):
    customer = {
        "customer_id": i,
        "city": random.choice(cities),
        "segment": random.choice(segments),
        "credit_tier": random.choices(credit_tiers, weights=[1, 2, 3, 2, 1])[0],
        "income": max(0, int(np.random.normal(loc=100000, scale=25000)))  
    }
    customers.append(customer)

df_customers = pd.DataFrame(customers)
df_customers.to_csv(os.path.join(DATA_DIR, "customers.csv"), index=False)
print("customers.csv olusturuldu.")

# -----------------------
# 2. SALES.csv üretimi
# -----------------------
sales = []
months = pd.date_range("2023-01-01", "2024-12-01", freq="MS").strftime("%Y-%m").tolist()

for customer in df_customers.itertuples():
    num_months = random.randint(5, 10)  # Her müşteri için 5–10 ay arası satış
    sampled_months = random.sample(months, num_months)

    for month in sampled_months:
        purchases = random.randint(1, 5)
        sales.append({
            "customer_id": customer.customer_id,
            "month": month,
            "purchases": random.randint(1, 5),
            "amount": round(purchases * random.uniform(100, 250), 2)
        })

df_sales = pd.DataFrame(sales)
df_sales.to_csv(os.path.join(DATA_DIR, "sales.csv"), index=False)
print("sales.csv olusturuldu.")
