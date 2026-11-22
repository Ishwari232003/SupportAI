import random
from datetime import date, datetime, timedelta
from faker import Faker
from passlib.context import CryptContext
from app.db.models import *

random.seed(42)
Faker.seed(42)
fake = Faker("en_IN")
pwd = CryptContext(schemes=["bcrypt"])
TODAY = date.today()
REGIONS = ["North", "South", "East", "West"]
CITIES = {"North": ["Delhi", "Chandigarh"], "South": ["Bengaluru", "Chennai", "Hyderabad"],
          "East": ["Kolkata", "Bhubaneswar"], "West": ["Mumbai", "Pune", "Ahmedabad"]}
# category: (warranty_months, return_window_days)
CATS = {"Electronics": (12, 10), "Appliances": (24, 7), "Fashion": (0, 30),
        "Home": (6, 15), "Beauty": (0, 7), "Books": (0, 10)}

s = SessionLocal()
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

# ---------------- master data ----------------
customers = []
for i in range(1, 301):
    r = random.choice(REGIONS)
    customers.append(Customer(
        id=f"CUST-{i:04d}", name=fake.name(), email=fake.email(), phone=fake.phone_number(),
        region=r, city=random.choice(CITIES[r]),
        customer_type=random.choices(["Regular", "Premium", "Business"], [70, 20, 10])[0]))

sellers = [Seller(id=f"SEL-{i:03d}", name=fake.company(), rating=round(random.uniform(3.0, 5.0), 1),
                  approval_status=random.choices(["approved", "pending"], [85, 15])[0])
           for i in range(1, 21)]
warehouses = [Warehouse(id=f"WH-{i}", name=f"{REGIONS[(i - 1) % 4]} Hub {i}", region=REGIONS[(i - 1) % 4])
              for i in range(1, 7)]
partners = [DeliveryPartner(id=f"DP-{i}", name=n) for i, n in
            enumerate(["Delhivery", "BlueDart", "Ecom Express", "XpressBees", "India Post"], 1)]
agents = [Agent(id=f"AGT-{i:02d}", name=fake.name(), team=random.choice(["Orders", "Refunds", "Shipping", "Seller"]))
          for i in range(1, 11)]

products = []
for i in range(1, 39):
    cat = random.choice(list(CATS))
    w, r = CATS[cat]
    products.append(Product(id=f"PROD-{i:03d}", name=f"{fake.word().title()} {cat} {i}", category=cat,
                            price=round(random.uniform(299, 49999), 2), warranty_months=w,
                            return_window_days=r, seller_id=random.choice(sellers).id))
# Demo products named in the brief. Reuse these exact facts in your documents!
products.append(Product(id="PROD-ABC", name="Product ABC", category="Appliances", price=18999,
                        warranty_months=24, return_window_days=7, seller_id="SEL-001"))
products.append(Product(id="PROD-X", name="Product X", category="Electronics", price=7499,
                        warranty_months=12, return_window_days=10, seller_id="SEL-002"))

# FIX: save sellers (and other parents) BEFORE products
s.add_all(customers + sellers + warehouses + partners + agents)
s.commit()
s.add_all(products)
s.commit()
s.add_all([Inventory(product_id=p.id, warehouse_id=w.id, quantity=random.randint(0, 200))
           for p in products for w in random.sample(warehouses, 2)])
s.commit()

# ---------------- transactional data ----------------
cnt = {"ship": 0, "pay": 0, "ret": 0, "ref": 0}


def nid(k, prefix):
    cnt[k] += 1
    return f"{prefix}-{cnt[k]:05d}"


cust_by_id = {c.id: c for c in customers}
orders, items, ships, pays, rets, refs = [], [], [], [], [], []


def make_order(oid, status=None, cust=None, prods=None, days_ago=None, ship_status=None, delay_reason=None):
    c = cust_by_id[cust] if cust else random.choice(customers)
    status = status or random.choices(
        ["placed", "pending_seller_approval", "shipped", "delivered", "cancelled", "returned"],
        [8, 8, 17, 50, 7, 10])[0]
    prods = prods or random.sample(products, random.randint(1, 3))
    od = TODAY - timedelta(days=days_ago if days_ago is not None else random.randint(2, 120))
    total = sum(p.price for p in prods)
    wh = random.choice(warehouses)
    orders.append(Order(id=oid, customer_id=c.id, order_date=od, status=status, total_amount=total,
                        seller_id=prods[0].seller_id, warehouse_id=wh.id))
    items.extend(OrderItem(order_id=oid, product_id=p.id, quantity=1, price=p.price) for p in prods)
    pay_status = "refunded" if status == "cancelled" else "success"
    pays.append(Payment(id=nid("pay", "PAY"), order_id=oid,
                        method=random.choice(["UPI", "Card", "NetBanking", "COD"]),
                        status=pay_status, amount=total,
                        paid_at=datetime.combine(od, datetime.min.time())))

    if status in ("shipped", "delivered", "returned"):
        sd = od + timedelta(days=random.randint(1, 3))
        exp = sd + timedelta(days=random.randint(3, 6))
        if status == "shipped":
            p_delay = 0.35 if c.region == "South" else 0.08
            st = ship_status or ("delayed" if random.random() < p_delay
                                 else random.choice(["in_transit", "out_for_delivery"]))
            sd = TODAY - timedelta(days=random.randint(2, 8))
            exp = sd + timedelta(days=5)
            dd = None
            dr = None
            if st == "delayed":
                exp = TODAY - timedelta(days=random.randint(1, 5))
                dr = delay_reason or random.choice(
                    ["Weather disruption", "Hub congestion", "Address issue", "Vehicle breakdown"])
        else:
            st, dd, dr = "delivered", min(exp, TODAY - timedelta(days=1)), None
        ships.append(Shipment(id=nid("ship", "SHP"), order_id=oid, partner_id=random.choice(partners).id,
                              tracking_no=f"TRK{random.randint(10**9, 10**10 - 1)}", status=st,
                              region=c.region, shipped_date=sd, expected_date=exp,
                              delivered_date=dd, delay_reason=dr))

    # keep the demo order ORD-102345 free of returns so it stays "eligible"
    if status == "returned" or (status == "delivered" and oid != "ORD-102345" and random.random() < 0.08):
        p = prods[0]
        rid = nid("ret", "RET")
        rs = "received" if status == "returned" else random.choice(["approved", "picked_up", "received", "rejected"])
        rets.append(Return(id=rid, order_id=oid, product_id=p.id, status=rs,
                           requested_at=TODAY - timedelta(days=random.randint(3, 25)),
                           reason=random.choice(["Defective", "Wrong item", "Size issue",
                                                 "Changed mind", "Damaged in transit"])))
        if rs == "received":
            old = random.random() < 0.3  # ~30% of refunds are delayed
            ini = TODAY - timedelta(days=random.randint(11, 20) if old else random.randint(1, 8))
            rst = "pending" if old else random.choice(["initiated", "processed", "processed"])
            refs.append(Refund(id=nid("ref", "REF"), order_id=oid, return_id=rid, amount=p.price,
                               status=rst, initiated_at=ini,
                               processed_at=ini + timedelta(days=4) if rst == "processed" else None,
                               delay_reason=random.choice(["Bank processing delay", "Return QC pending",
                                                           "Payment gateway failure"]) if old else None))
    if status == "cancelled":
        refs.append(Refund(id=nid("ref", "REF"), order_id=oid, amount=total, status="processed",
                           initiated_at=od + timedelta(days=1), processed_at=od + timedelta(days=4)))


# ---------------- demo cases from the brief ----------------
# ORD-500231: delayed shipment in the South region
make_order("ORD-500231", "shipped", cust=next(c.id for c in customers if c.region == "South"),
           prods=[products[0]], days_ago=9, ship_status="delayed", delay_reason="Hub congestion")

for i in range(1500):
    oid = f"ORD-{101000 + i}"
    if oid == "ORD-102345":
        # Product X (10-day return window), delivered recently => eligible for return
        make_order(oid, "delivered", prods=[products[-1]], days_ago=7)
    else:
        make_order(oid)

s.add_all(orders)
s.commit()
s.add_all(items + ships + pays + rets)
s.commit()
s.add_all(refs)
s.commit()

# ---------------- complaints, tickets, users ----------------
CATS_C = ["Late delivery", "Refund delay", "Damaged product", "Wrong item", "Payment failure", "Poor support"]
for i in range(1, 201):
    o = random.choice(orders)
    s.add(Complaint(id=f"CMP-{i:04d}", customer_id=o.customer_id, order_id=o.id,
                    category=random.choice(CATS_C), description=fake.paragraph(2),
                    severity=random.choice(["low", "medium", "high"]),
                    created_at=TODAY - timedelta(days=random.randint(0, 60))))

for i in range(1, 401):
    o = random.choice(orders)
    st = random.choices(["open", "in_progress", "resolved", "escalated"], [20, 20, 50, 10])[0]
    ca = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
    s.add(SupportTicket(id=f"TKT-{i:05d}", customer_id=o.customer_id, order_id=o.id,
                        agent_id=random.choice(agents).id,
                        subject=random.choice(["Where is my order", "Refund not received", "Return request",
                                               "Warranty claim", "Payment deducted"]),
                        status=st, priority=random.choice(["low", "medium", "high"]), created_at=ca,
                        resolved_at=ca + timedelta(hours=random.randint(1, 72)) if st == "resolved" else None,
                        first_contact_resolved=(st == "resolved" and random.random() < 0.65)))

for u, r in [("support1", "support_executive"), ("lead1", "team_lead"),
             ("orders1", "order_mgmt_executive"), ("warehouse1", "warehouse_manager"),
             ("seller1", "seller_support_executive"), ("ops1", "operations_manager"),
             ("admin", "admin")]:
    s.add(User(username=u, password_hash=pwd.hash("Passw0rd!"), role=r))
s.commit()

print("Seed complete.", {"orders": len(orders), "shipments": len(ships),
                         "returns": len(rets), "refunds": len(refs)})