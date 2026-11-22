"""Generates ~55 synthetic enterprise documents.
Run from the project root:  python data/generate_docs.py"""
import csv
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document as Docx
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

OUT = Path(__file__).parent / "documents"
OUT.mkdir(parents=True, exist_ok=True)

# category: (warranty_months, return_window_days)  -- MUST match the products table
CAT = {"Electronics": (12, 10), "Appliances": (24, 7), "Fashion": (0, 30),
       "Home": (6, 15), "Beauty": (0, 7), "Books": (0, 10)}
V6 = {c: v[1] for c, v in CAT.items()}
V4 = {"Electronics": 7, "Appliances": 7, "Fashion": 15, "Home": 10, "Beauty": 7, "Books": 7}

DOCS = []


def L(*lines):
    return "\n".join(lines)


def add(file, doc_type, policy, sections=None, table=None, version="1", eff="2025-06-01",
        active=True, category="all", region="all", customer_type="all", seller="all",
        warehouse="all", order_status="all"):
    DOCS.append(dict(file=file, doc_type=doc_type, policy=policy, sections=sections or [], table=table,
                     version=version, eff=eff, active=active, category=category, region=region,
                     customer_type=customer_type, seller=seller, warehouse=warehouse,
                     order_status=order_status))


def win(d):
    return "\n".join(f"- {c}: {n} days from delivery" for c, n in d.items())


# =====================================================================
# 1. RETURN POLICY (v4 old, v6 current)
# =====================================================================
def return_secs(ver, w, refund_days, attempts):
    return [
        ("Purpose and Scope", f"This Return Policy (Version {ver}) explains when and how a customer can return a product bought on the marketplace. It applies to all orders delivered on or after the effective date."),
        ("Return Eligibility Window", L("The return window starts on the date of delivery. Windows by product category:", win(w),
                                        "Requests raised after the window closes are rejected, except for items that were defective or damaged on arrival.")),
        ("Product-Specific Examples", L(f"- Product X (Electronics): {w['Electronics']}-day return window.",
                                        f"- Product ABC (Appliances): {w['Appliances']}-day return window.")),
        ("Non-Returnable Items", "Innerwear, opened beauty and personal care items, digital goods, gift cards, and products with a missing serial number or tampered seal cannot be returned."),
        ("How to Request a Return", L("1. The customer opens the order and selects Return.",
                                      "2. The customer selects a reason: Defective, Wrong item, Size issue, Changed mind or Damaged in transit.",
                                      "3. The system checks the return window and creates a return request.",
                                      "4. A support agent can raise the request on the customer's behalf after verifying the order.")),
        ("Pickup and Quality Check", f"The delivery partner makes up to {attempts} pickup attempt(s). After pickup, the warehouse performs a quality check (QC). Returns that fail QC are rejected and the item is sent back to the customer."),
        ("Refund Timeline", f"After the return passes QC, the refund is initiated and completed within {refund_days} business days to the original payment method."),
        ("Defective or Damaged Items", "Items reported defective or damaged within 48 hours of delivery qualify for free pickup and a full refund or replacement, regardless of the category window."),
    ]


add("return_policy_v4.pdf", "Return Policy", "Return Policy",
    return_secs(4, V4, 10, 1) + [("Status", "This version was superseded by Version 6 on 2025-06-01 and is kept for audit and comparison.")],
    version="4", eff="2024-01-01", active=False)
add("return_policy_v6.pdf", "Return Policy", "Return Policy",
    return_secs(6, V6, 7, 3) + [("Changes from Version 4", L(
        "- Return windows extended: Electronics 7 to 10 days, Fashion 15 to 30 days, Home 10 to 15 days, Books 7 to 10 days.",
        "- Appliances (7 days) and Beauty (7 days) are unchanged.",
        "- Refund completion time reduced from 10 to 7 business days.",
        "- Pickup attempts increased from 1 to 3."))],
    version="6", eff="2025-06-01", active=True)


# =====================================================================
# 2. REFUND POLICY (v1 old, v2 current)
# =====================================================================
def refund_secs(ver, days, cod_days, esc_days):
    return [
        ("Purpose", f"This Refund Policy (Version {ver}) describes how refunds are issued for cancelled orders and approved returns."),
        ("Refund Timelines", L(f"- UPI, Card, NetBanking and Wallet: within {days} business days after return QC is passed or the cancellation is confirmed.",
                               f"- Cash on Delivery: within {cod_days} business days, after the customer's bank details are verified.")),
        ("Refund Status Definitions", L("- initiated: refund request created and sent for processing.", "- pending: refund not yet completed within the normal timeline.",
                                        "- processed: money has been sent to the customer.", "- failed: the payment gateway or bank rejected the refund.")),
        ("Common Reasons for Refund Delay", L(
            "- Bank processing delay: the refund was sent but the bank has not posted it. Share the refund reference and ask the customer to wait up to 3 business days; if still missing, raise a bank trace.",
            "- Return QC pending: the warehouse has not finished the quality check. The Warehouse Manager must complete QC within 24 hours of escalation.",
            "- Payment gateway failure: the refund failed at the gateway. The Refunds team re-initiates it manually and the status returns to initiated.")),
        ("Escalation of Delayed Refunds", f"If a refund stays pending for more than {esc_days} business days, escalate to the Team Lead. If it is still unresolved after 15 calendar days, escalate to the Operations Manager."),
        ("Refund Modes", "Refunds go to the original payment method. A store wallet credit is available only when the customer asks for it."),
    ]


add("refund_policy_v1.docx", "Refund Policy", "Refund Policy", refund_secs(1, 10, 14, 14), version="1", eff="2024-01-01", active=False)
add("refund_policy_v2.pdf", "Refund Policy", "Refund Policy", refund_secs(2, 7, 10, 7), version="2", eff="2025-06-01")


# =====================================================================
# 3. WARRANTY DOCUMENTS
# =====================================================================
def warranty_secs(cat, months, note):
    return [
        ("Warranty Period", f"{cat} products carry a manufacturer warranty of {months} months from the date of delivery."),
        ("What Is Covered", "Manufacturing defects and component failures under normal use. Repair or replacement is at the discretion of the authorized service center."),
        ("What Is Not Covered", "Physical or liquid damage, unauthorized repairs, misuse, normal wear and tear, and damage caused by power surges."),
        ("How to Claim Warranty", L("1. Keep the invoice and the order ID.", "2. Raise a support ticket with the subject Warranty claim.",
                                    "3. The agent verifies the delivery date and warranty period in the order record.",
                                    "4. The customer is directed to an authorized service center or a replacement is arranged.")),
        ("Product-Specific Notes", note),
        ("Warranty vs Return", f"Warranty is separate from the return window. The return window for {cat} is {CAT[cat][1]} days from delivery; after that, only warranty claims apply."),
    ]


add("warranty_electronics.docx", "Warranty Document", "Electronics Warranty Policy",
    warranty_secs("Electronics", 12, "Product X (Electronics) has a 12-month warranty."), category="Electronics")
add("warranty_appliances.pdf", "Warranty Document", "Appliances Warranty Policy",
    warranty_secs("Appliances", 24, "Product ABC (Appliances) has a 24-month warranty."), category="Appliances")
add("warranty_home.txt", "Warranty Document", "Home Products Warranty Policy",
    warranty_secs("Home", 6, "Home products carry a 6-month warranty. Cosmetic wear is excluded."), category="Home")
add("warranty_matrix.xlsx", "Warranty Document", "Warranty and Return Window Matrix",
    table=(["item", "type", "warranty_months", "return_window_days", "notes"],
           [[c, "category", w, r, "No manufacturer warranty; return window only" if w == 0 else "Manufacturer warranty applies"]
            for c, (w, r) in CAT.items()] +
           [["Product ABC", "product", 24, 7, "Appliances category"], ["Product X", "product", 12, 10, "Electronics category"]]))

# =====================================================================
# 4. SHIPPING GUIDELINES
# =====================================================================
add("shipping_guidelines.pdf", "Shipping Guidelines", "Shipping and Delivery Guidelines", [
    ("Dispatch Timelines", "Sellers must hand over orders to the delivery partner within 48 hours of order approval."),
    ("Delivery SLA", "Standard delivery is 3 to 5 days in metro cities and 5 to 7 days elsewhere. Regional SLAs are in the Regional Delivery SLA sheet."),
    ("Shipment Tracking", "Every shipment has a tracking number. Agents look up the status, the courier partner and the expected delivery date in the shipment record."),
    ("Delayed Shipments", "A shipment is delayed when the expected delivery date has passed and the order is not delivered. Common reasons: weather disruption, hub congestion, address issue, vehicle breakdown."),
    ("Failed Delivery Attempts", "The courier makes up to 3 delivery attempts. After the third failed attempt the shipment returns to the warehouse."),
    ("Address Changes", "Address changes are allowed only before the shipment is handed to the courier."),
])
add("shipping_regional_sla.csv", "Shipping Guidelines", "Regional Delivery SLA",
    table=(["region", "metro_sla_days", "non_metro_sla_days", "main_hubs", "notes"], [
        ["North", 3, 5, "Delhi Hub, Chandigarh Hub", "Fog delays possible in winter"],
        ["South", 3, 6, "Bengaluru Hub, Chennai Hub, Hyderabad Hub", "Higher congestion in monsoon; proactive delay alerts enabled"],
        ["East", 4, 6, "Kolkata Hub, Bhubaneswar Hub", "Cyclone season delays possible"],
        ["West", 3, 5, "Mumbai Hub, Pune Hub, Ahmedabad Hub", "Heavy rain delays possible"]]), region="all")
add("courier_partners.xlsx", "Shipping Guidelines", "Courier Partner Directory",
    table=(["partner_id", "partner", "coverage", "avg_delivery_days", "escalation_contact"], [
        ["DP-1", "Delhivery", "Pan-India", 4, "escalations.delhivery@partners.example.com"],
        ["DP-2", "BlueDart", "Pan-India, premium", 3, "escalations.bluedart@partners.example.com"],
        ["DP-3", "Ecom Express", "Pan-India", 5, "escalations.ecom@partners.example.com"],
        ["DP-4", "XpressBees", "Metro and tier-2", 4, "escalations.xpressbees@partners.example.com"],
        ["DP-5", "India Post", "Rural and remote", 7, "escalations.indiapost@partners.example.com"]]))
add("shipping_delay_handling.txt", "Shipping Guidelines", "Delayed Shipment Handling Guide", [
    ("When a Shipment Is Delayed", "Status delayed means the expected date has passed. Check the delay reason in the shipment record."),
    ("Agent Actions", L("1. Tell the customer the reason and the new expected date.", "2. Contact the courier escalation contact if the delay exceeds 3 days.",
                        "3. Raise a ticket for the Order Management Executive.")),
    ("Goodwill Rules", L("- 3 or more days past the expected date: offer a goodwill coupon of Rs 100.",
                         "- 7 or more days past the expected date: offer cancellation with a full refund.")),
    ("Region South Note", "South region has the highest delay rate. Hub congestion is the most common reason. Use the proactive delay message template."),
], region="South", order_status="shipped")

# =====================================================================
# 5. PRODUCT MANUALS
# =====================================================================
add("manual_product_abc.pdf", "Product Manual", "Product ABC User Manual", [
    ("Product Overview", "Product ABC is a smart air purifier in the Appliances category. List price Rs 18,999. Seller: SEL-001."),
    ("Specifications", L("- Coverage area: 450 sq ft", "- Filter: HEPA H13, replace every 6 months", "- Power: 55 W", "- Noise: below 45 dB on sleep mode")),
    ("Setup", "Place the unit 30 cm away from walls. Insert the filter, plug in, and press the power button. Pair with the mobile app using Wi-Fi."),
    ("Safety", "Keep away from water. Unplug before replacing the filter. Do not cover the air outlet."),
    ("Warranty and Returns", "Product ABC has a 24-month manufacturer warranty. The return window is 7 days from delivery."),
    ("Troubleshooting Basics", "No power: check the socket and the cable. Low airflow: replace the filter. App not connecting: reset Wi-Fi by holding the Wi-Fi button for 5 seconds."),
], category="Appliances", seller="SEL-001")
add("manual_product_x.pdf", "Product Manual", "Product X User Manual", [
    ("Product Overview", "Product X is a portable Bluetooth speaker in the Electronics category. List price Rs 7,499. Seller: SEL-002."),
    ("Specifications", L("- Bluetooth 5.3", "- Battery life: 20 hours", "- Water resistance: IPX5", "- Charging: USB-C, about 3 hours")),
    ("Setup", "Charge fully before first use. Hold the power button for 3 seconds. Select Product X in the Bluetooth list on your phone."),
    ("Safety", "Do not submerge in water. Do not use a damaged charging cable."),
    ("Warranty and Returns", "Product X has a 12-month manufacturer warranty. The return window is 10 days from delivery."),
    ("Troubleshooting Basics", "Will not turn on: charge for 30 minutes with the original cable, then hold the power button for 10 seconds to reset. Not pairing: forget the device on your phone and pair again."),
], category="Electronics", seller="SEL-002")
for cat, fmt, text in [("Electronics", "docx", "Keep devices away from heat and moisture. Use the original charger. Update firmware through the manufacturer app."),
                       ("Appliances", "docx", "Install on a level surface with ventilation. Clean filters on schedule. Only authorized technicians may open the unit."),
                       ("Home", "docx", "Follow the assembly guide. Check all screws after the first week. Clean with a damp cloth only."),
                       ("Fashion", "docx", "Wash as per the label. Check the size chart before ordering. Tags must stay attached for a return.")]:
    w, r = CAT[cat]
    add(f"manual_{cat.lower()}_care_guide.{fmt}", "Product Manual", f"{cat} Category Care and Usage Guide", [
        ("Overview", f"General usage and care guidance for products in the {cat} category."),
        ("Usage and Care", text),
        ("Warranty and Returns", (f"Manufacturer warranty: {w} months. " if w else "No manufacturer warranty. ") + f"Return window: {r} days from delivery."),
        ("Getting Help", "Contact customer support with the order ID. Support agents can arrange pickups and warranty claims."),
    ], category=cat)

# =====================================================================
# 6. PRODUCT FAQS
# =====================================================================
def faqs(cat):
    w, r = CAT[cat]
    return [
        (f"What is the warranty period for {cat} products?", f"{w} months from delivery." if w else "There is no manufacturer warranty. Only the return window applies."),
        (f"How many days do I have to return a {cat} product?", f"{r} days from delivery under Return Policy Version 6."),
        ("How do I claim warranty or raise a return?", "Raise a support ticket with the order ID. The agent verifies delivery date and eligibility."),
        ("How long does a refund take?", "Within 7 business days after the returned item passes quality check."),
        ("Can I exchange instead of returning?", "Exchange is available for Defective and Size issue reasons, subject to stock."),
    ]


for cat, fmt in [("Electronics", "txt"), ("Appliances", "txt"), ("Fashion", "txt"), ("Home", "csv"), ("Beauty", "csv"), ("Books", "xlsx")]:
    if fmt == "txt":
        add(f"faq_{cat.lower()}.txt", "Product FAQ", f"{cat} Product FAQ", [(q, a) for q, a in faqs(cat)], category=cat)
    else:
        add(f"faq_{cat.lower()}.{fmt}", "Product FAQ", f"{cat} Product FAQ",
            table=(["category", "question", "answer"], [[cat, q, a] for q, a in faqs(cat)]), category=cat)

# =====================================================================
# 7. SELLER GUIDELINES
# =====================================================================
add("seller_onboarding.docx", "Seller Guidelines", "Seller Onboarding Guide", [
    ("Eligibility", "Sellers need a registered business, a valid GST number and a bank account."),
    ("KYC Documents", "PAN card, GST certificate, cancelled cheque and address proof."),
    ("Account Approval", "New sellers have approval status pending until KYC is verified. Pending sellers cannot receive orders."),
    ("Seller Ratings", "Ratings range from 1 to 5. Sellers below 3.5 are placed under review."),
])
add("seller_listing_standards.pdf", "Seller Guidelines", "Seller Listing Standards", [
    ("Titles and Images", "Titles must be accurate. At least 3 clear images are required for each product."),
    ("Pricing", "Prices must include taxes. Misleading discounts are not allowed."),
    ("Stock Accuracy", "Sellers must keep stock updated. Repeated cancellations due to no stock lead to penalties."),
    ("Warranty and Returns Information", "Listings must show the correct warranty and the marketplace return window for the category."),
])
add("seller_payouts_penalties.txt", "Seller Guidelines", "Seller Payouts and Penalties", [
    ("Payout Cycle", "Payouts are made 7 days after successful delivery."),
    ("Deductions", "Commission, shipping fees and refund amounts for returns are deducted from payouts."),
    ("Penalties", L("- Late dispatch beyond 48 hours: Rs 50 per order.", "- Seller cancellation: Rs 100 per order.", "- Counterfeit product: account suspension.")),
])
add("seller_order_approval_workflow.docx", "Seller Guidelines", "Seller Order Approval Workflow", [
    ("Pending Seller Approval", "Some orders have status pending_seller_approval until the seller accepts them."),
    ("Seller Deadlines", "The seller must accept within 24 hours. A reminder is sent at 12 hours."),
    ("Seller Support Follow-up", "The Seller Support Executive contacts sellers who have not responded after 24 hours."),
    ("Auto-Cancellation", "Orders not accepted within 48 hours are cancelled automatically and the customer is refunded in full."),
], order_status="pending_seller_approval")

# =====================================================================
# 8. MARKETPLACE POLICIES
# =====================================================================
add("marketplace_prohibited_items.txt", "Marketplace Policy", "Prohibited Items Policy", [
    ("Prohibited Items", "Weapons, drugs, counterfeit goods, stolen goods and hazardous chemicals are banned."),
    ("Restricted Items", "Prescription medicines and imported electronics need documents before listing."),
    ("Action", "Violating listings are removed and the seller may be suspended."),
])
add("marketplace_counterfeit_policy.pdf", "Marketplace Policy", "Counterfeit and Brand Protection Policy", [
    ("Definition", "A counterfeit is an imitation product sold as a genuine brand product."),
    ("Reporting", "Customers or brands can report counterfeits through support. The listing is frozen within 24 hours."),
    ("Customer Remedy", "Customers who received a counterfeit get a full refund, and the return pickup is free."),
])
add("marketplace_review_policy.docx", "Marketplace Policy", "Reviews and Ratings Policy", [
    ("Genuine Reviews", "Only verified buyers can post reviews."),
    ("Prohibited Behaviour", "Paid reviews, fake reviews and review exchange are not allowed."),
    ("Removal", "Reviews with abuse or personal data are removed."),
])
add("marketplace_fair_pricing.txt", "Marketplace Policy", "Fair Pricing Policy", [
    ("Price Accuracy", "The price shown at checkout is the final price. Hidden fees are not allowed."),
    ("Price Errors", "If a listing price is clearly a mistake, the seller can cancel affected orders and the customer is refunded in full."),
])

# =====================================================================
# 9. PAYMENT POLICIES
# =====================================================================
add("payment_failure_reversal.pdf", "Payment Policy", "Payment Failure and Reversal Policy", [
    ("Failed Payments", "If money is deducted but the order is not placed, the amount is reversed automatically."),
    ("Reversal Timeline", "Automatic reversals complete within 5 to 7 business days."),
    ("Double Charges", "If the customer was charged twice, the extra amount is refunded after verification with the payment gateway."),
    ("Agent Steps", L("1. Ask for the payment reference and the date.", "2. Check the payment status in the order record.", "3. If more than 7 business days have passed, escalate to the Team Lead.")),
])
add("payment_cod_policy.txt", "Payment Policy", "Cash on Delivery Policy", [
    ("COD Availability", "COD is available for orders up to Rs 50,000 in serviceable pin codes."),
    ("Refunds for COD", "COD refunds are paid to a verified bank account within 10 business days of QC."),
    ("COD Fraud Prevention", "Customers with 3 or more refused COD deliveries lose COD access."),
])

# =====================================================================
# 10. ESCALATION PROCEDURES
# =====================================================================
add("escalation_matrix.xlsx", "Escalation Procedure", "Escalation Matrix",
    table=(["level", "trigger", "owner_role", "response_sla", "next_level"], [
        ["L1", "Standard customer query", "Customer Support Executive", "15 minutes", "L2"],
        ["L2", "Refund pending more than 7 business days", "Team Lead", "4 hours", "L3"],
        ["L2", "Shipment delayed more than 3 days past expected date", "Order Management Executive", "4 hours", "L3"],
        ["L2", "Seller has not accepted order within 24 hours", "Seller Support Executive", "4 hours", "L3"],
        ["L2", "Stock or QC issue at warehouse", "Warehouse Manager", "4 hours", "L3"],
        ["L3", "Unresolved after 24 hours or high severity complaint", "Operations Manager", "2 hours", "L4"],
        ["L4", "Policy exception or system failure", "Administrator", "1 hour", "none"]]))
add("escalation_sla_breach.pdf", "Escalation Procedure", "SLA Breach Escalation Procedure", [
    ("Purpose", "Defines what to do when a support SLA is about to be breached or has been breached."),
    ("Detection", "Tickets open for more than 24 hours are flagged. High priority tickets are flagged after 4 hours."),
    ("Steps", L("1. The agent adds a note and informs the customer.", "2. The Team Lead reviews the ticket.", "3. If unresolved after 24 hours, the Operations Manager takes ownership.")),
])
add("escalation_refund_procedure.txt", "Escalation Procedure", "Refund Escalation Procedure", [
    ("Trigger", "A refund is pending for more than 7 business days."),
    ("Actions", L("1. Check the refund delay reason: Bank processing delay, Return QC pending or Payment gateway failure.",
                  "2. For Return QC pending, ask the Warehouse Manager to complete QC in 24 hours.",
                  "3. For Payment gateway failure, ask the Refunds team to re-initiate the refund.",
                  "4. If still unresolved after 15 calendar days, escalate to the Operations Manager.")),
])

# =====================================================================
# 11. TROUBLESHOOTING GUIDES
# =====================================================================
add("troubleshoot_not_powering_on.txt", "Troubleshooting Guide", "Product Not Powering On", [
    ("Customer Steps", L("1. Charge the device for 30 minutes using the original cable.", "2. Hold the power button for 10 seconds to reset.", "3. Try a different socket or cable.")),
    ("If It Still Fails", "Within the return window, raise a return with reason Defective. After the return window, raise a warranty claim."),
    ("Example", "Product X: 10-day return window, 12-month warranty."),
], category="Electronics")
add("troubleshoot_delivery_stuck.pdf", "Troubleshooting Guide", "Delivery Stuck in Transit", [
    ("Check", "Look up the shipment status, the courier partner and the delay reason."),
    ("Actions", L("1. Share the reason and the new expected date with the customer.", "2. Contact the courier if the delay is more than 3 days.", "3. Offer the goodwill options from the Delayed Shipment Handling Guide.")),
    ("Escalate", "Escalate to the Order Management Executive if the shipment has not moved for 5 days."),
], order_status="shipped")
add("troubleshoot_refund_not_received.docx", "Troubleshooting Guide", "Refund Not Received", [
    ("Check the Refund Record", "Look up the refund status: initiated, pending, processed or failed."),
    ("If Processed", "Share the refund date. Ask the customer to check with their bank after 3 business days."),
    ("If Pending", "Check the delay reason. Bank processing delay, Return QC pending and Payment gateway failure each have their own action in the Refund Policy."),
    ("If Failed", "Ask the Refunds team to re-initiate the refund."),
])
add("troubleshoot_payment_deducted.txt", "Troubleshooting Guide", "Payment Deducted but Order Not Placed", [
    ("Check", "Confirm the payment status in the order record."),
    ("Action", "Tell the customer the amount is reversed automatically in 5 to 7 business days."),
    ("Escalate", "If more than 7 business days have passed, escalate to the Team Lead."),
])
add("troubleshoot_wrong_damaged_item.pdf", "Troubleshooting Guide", "Wrong or Damaged Item Received", [
    ("Collect Details", "Ask for the order ID and photos of the item and the packaging."),
    ("Raise Return", "Create a return with reason Wrong item or Damaged in transit. Pickup is free."),
    ("Resolution", "Offer a replacement or a full refund. Refund completes within 7 business days after QC."),
])
add("troubleshoot_product_abc.docx", "Troubleshooting Guide", "Product ABC Performance Issues", [
    ("Low Airflow", "Replace the HEPA filter. Filters should be replaced every 6 months."),
    ("App Not Connecting", "Hold the Wi-Fi button for 5 seconds and pair again."),
    ("Warranty", "Product ABC has a 24-month warranty. After the 7-day return window, use a warranty claim."),
], category="Appliances")

# =====================================================================
# 12. CUSTOMER COMMUNICATION TEMPLATES
# =====================================================================
add("templates_email_chat.xlsx", "Communication Template", "Customer Communication Templates",
    table=(["template_id", "scenario", "channel", "subject", "body"], [
        ["T-01", "Delayed shipment", "email", "Update on your order {order_id}", "Hi {customer_name}, your order {order_id} is delayed due to {delay_reason}. The new expected date is {new_date}. We are sorry for the inconvenience."],
        ["T-02", "Refund initiated", "email", "Refund started for {order_id}", "Hi {customer_name}, your refund of Rs {amount} has been initiated and will reach you within 7 business days."],
        ["T-03", "Refund delayed", "email", "About your refund for {order_id}", "Hi {customer_name}, your refund is taking longer because of {delay_reason}. We have escalated it and will update you within 24 hours."],
        ["T-04", "Return approved", "chat", "", "Your return for {order_id} is approved. Our partner will pick up the item within 3 attempts."],
        ["T-05", "Return not eligible", "chat", "", "Sorry, the return window for this product has closed. If the product is faulty, we can help with a warranty claim."],
        ["T-06", "Warranty claim", "email", "Your warranty claim", "Hi {customer_name}, please share the invoice and photos. We will guide you to the nearest service center."]]))
add("templates_apology_letters.docx", "Communication Template", "Apology and Escalation Letters", [
    ("Apology Letter", "Dear {customer_name}, we are sorry for the trouble with order {order_id}. We have taken ownership and will resolve it within {resolution_time}."),
    ("Escalation Notice", "Dear {customer_name}, your case has been escalated to a senior team member who will contact you within 4 hours."),
    ("Resolution Confirmation", "Dear {customer_name}, your issue is resolved. Please reply if you need anything else."),
])
add("templates_quick_replies.txt", "Communication Template", "Chat Quick Replies", [
    ("Greeting", "Hello, thanks for contacting support. May I have your order ID?"),
    ("Please Wait", "Thanks. I am checking this now and will respond in a minute."),
    ("Closing", "Is there anything else I can help you with today?"),
])

# =====================================================================
# 13. CUSTOMER SUPPORT SOPs
# =====================================================================
add("sop_order_tracking.docx", "Customer Support SOP", "SOP: Order Tracking and Status Lookup", [
    ("Purpose", "Standard steps for answering where is my order questions."),
    ("Steps", L("1. Verify the customer using the order ID and registered email.", "2. Check the order status.", "3. If shipped, check the shipment status, courier and expected date.", "4. Share the information with the customer.")),
    ("Order Statuses", "placed, pending_seller_approval, shipped, delivered, cancelled, returned."),
])
add("sop_return_processing.pdf", "Customer Support SOP", "SOP: Return Processing", [
    ("Purpose", "Standard steps for handling a return request."),
    ("Eligibility Check", "Find the delivery date and the product category. Compare with the return window in Return Policy Version 6."),
    ("Steps", L("1. If eligible, create the return with the correct reason.", "2. Confirm pickup details.", "3. After QC, the refund is initiated.", "4. If not eligible and the item is faulty, offer a warranty claim.")),
])
add("sop_refund_investigation.txt", "Customer Support SOP", "SOP: Refund Investigation", [
    ("Purpose", "Steps for customers whose refund is late."),
    ("Steps", L("1. Look up the refund record and status.", "2. Read the delay reason.", "3. Follow the action for that reason in the Refund Policy.", "4. Escalate if pending for more than 7 business days.")),
])
add("sop_complaint_handling.docx", "Customer Support SOP", "SOP: Complaint Handling", [
    ("Purpose", "Standard steps for handling a customer complaint."),
    ("Steps", L("1. Record the complaint category and severity.", "2. Link the complaint to the order.", "3. Resolve or escalate according to the Escalation Matrix.", "4. Send a resolution message.")),
    ("Severity", "High severity complaints go to the Operations Manager within 24 hours."),
])

# =====================================================================
# 14. INTERNAL KNOWLEDGE BASE
# =====================================================================
add("kb_south_region_delays.txt", "Knowledge Base Article", "KB: Delayed Shipments in the South Region", [
    ("Summary", "South region shows the highest share of delayed shipments."),
    ("Main Causes", "Hub congestion, weather disruption (monsoon) and address issues."),
    ("What Agents Should Do", "Use the proactive delay template and follow the Delayed Shipment Handling Guide."),
], region="South")
add("kb_refund_delay_quick_reference.docx", "Knowledge Base Article", "KB: Refund Delay Quick Reference", [
    ("Bank Processing Delay", "Share the refund reference. Ask the customer to wait up to 3 business days. Raise a bank trace if needed."),
    ("Return QC Pending", "Ask the Warehouse Manager to finish QC within 24 hours."),
    ("Payment Gateway Failure", "Ask the Refunds team to re-initiate the refund."),
])
add("kb_warranty_vs_return.txt", "Knowledge Base Article", "KB: Warranty vs Return - Which Applies?", [
    ("Rule", "Use the return window first. After it closes, use warranty if the product has warranty."),
    ("Examples", L("- Product X: 10-day return window, 12-month warranty.", "- Product ABC: 7-day return window, 24-month warranty.")),
])

# =====================================================================
# 15. TRAINING MANUALS
# =====================================================================
add("training_new_agent.pdf", "Training Manual", "New Support Agent Training Manual", [
    ("Welcome", "This manual helps new Customer Support Executives become productive in their first two weeks."),
    ("Tools", "You will use the support assistant, the order lookup tool and the ticket dashboard."),
    ("Key Policies", "Learn Return Policy Version 6, Refund Policy Version 2, the warranty matrix and shipping guidelines."),
    ("Quality Standards", "Be polite, verify the customer, cite the policy and record every action in the ticket."),
])
add("training_advanced_escalation.docx", "Training Manual", "Advanced Support and Escalation Training", [
    ("Goal", "Prepare Team Leads and senior agents for complex cases."),
    ("Escalation Levels", "Learn the L1 to L4 levels and the owner roles in the Escalation Matrix."),
    ("Handling Angry Customers", "Acknowledge, apologise, give a clear next step and a time."),
    ("Reports", "Use daily support performance reports to track first contact resolution and handle time."),
])


# =====================================================================
# WRITERS
# =====================================================================
def title_of(d):
    return d["policy"] + (f" - Version {d['version']}" if d["version"] != "1" else "")


def meta_of(d):
    status = "Active" if d["active"] else "Superseded"
    return (f"Document Type: {d['doc_type']} | Policy Name: {d['policy']} | Version: {d['version']} | "
            f"Effective Date: {d['eff']} | Status: {status}")


def write_txt(d, p):
    lines = [title_of(d).upper(), "", f"Policy Name: {d['policy']}", f"Version: {d['version']}",
             f"Effective Date: {d['eff']}", f"Document Type: {d['doc_type']}", ""]
    for i, (h, b) in enumerate(d["sections"], 1):
        lines += [f"{i}. {h}", b, ""]
    p.write_text("\n".join(lines), encoding="utf-8")


def write_docx(d, p):
    doc = Docx()
    doc.add_heading(title_of(d), 0)
    doc.add_paragraph(meta_of(d))
    for i, (h, b) in enumerate(d["sections"], 1):
        doc.add_heading(f"{i}. {h}", 2)
        doc.add_paragraph(b)
    doc.save(str(p))


def write_pdf(d, p):
    ss = getSampleStyleSheet()

    def footer(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.drawString(40, 25, f"{d['policy']} (v{d['version']})")
        canvas.drawRightString(555, 25, f"Page {doc.page}")

    story = [Paragraph(escape(title_of(d)), ss["Title"]), Paragraph(escape(meta_of(d)), ss["Italic"]), Spacer(1, 12)]
    n = len(d["sections"])
    for i, (h, b) in enumerate(d["sections"], 1):
        story += [Paragraph(escape(f"{i}. {h}"), ss["Heading2"]),
                  Paragraph(escape(b).replace("\n", "<br/>"), ss["BodyText"]), Spacer(1, 8)]
        if i % 3 == 0 and i < n:
            story.append(PageBreak())
    SimpleDocTemplate(str(p), pagesize=A4).build(story, onFirstPage=footer, onLaterPages=footer)


def write_csv(d, p):
    headers, rows = d["table"]
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


def write_xlsx(d, p):
    headers, rows = d["table"]
    wb = Workbook()
    ws = wb.active
    ws.title = "Data"
    ws.append(headers)
    for r in rows:
        ws.append(r)
    about = wb.create_sheet("About")
    for k, v in [("Policy Name", d["policy"]), ("Document Type", d["doc_type"]),
                 ("Version", d["version"]), ("Effective Date", d["eff"])]:
        about.append([k, v])
    wb.save(str(p))


WRITERS = {"txt": write_txt, "docx": write_docx, "pdf": write_pdf, "csv": write_csv, "xlsx": write_xlsx}

if __name__ == "__main__":
    for d in DOCS:
        p = OUT / d["file"]
        WRITERS[p.suffix[1:]](d, p)
    with open(OUT / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "format", "doc_type", "policy_name", "version", "effective_date", "is_active",
                    "product_category", "region", "customer_type", "seller", "warehouse", "order_status"])
        for d in DOCS:
            w.writerow([d["file"], d["file"].split(".")[-1], d["doc_type"], d["policy"], d["version"], d["eff"],
                        d["active"], d["category"], d["region"], d["customer_type"], d["seller"],
                        d["warehouse"], d["order_status"]])
    print(f"Generated {len(DOCS)} documents in {OUT}")
    print("By format:", dict(Counter(d["file"].split(".")[-1] for d in DOCS)))
    print("By type:", dict(Counter(d["doc_type"] for d in DOCS)))
    