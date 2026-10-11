# 🏨 Hotel Management System (HMS) — Odoo 18

A modular, full-featured Hotel Management System built for **Odoo 18**, following Odoo core guidelines and best practices.

---

## 🚀 Key Features & Modules

### 1. 🚪 Rooms Catalogue (`hotel.room`)
- **Room Types**: Single, Double, Suite, Premium.
- **Flexible Pricing**: Nightly Rate & Hourly Rate with minimum hourly duration enforcement.
- **Status Sync**: Dynamic room availability tracking (`Available` / `Occupied`).
- **Views**: Kanban (card layout), List (badges), Form (avatar & statusbar), and Search view.

### 2. 👤 Guest Profile Management (`hotel.guest`)
- **Profile Details**: Name, Phone, Gender, National ID / Passport No., Nationality.
- **VIP Classification**: Normal, VIP, Corporate status badges.
- **Chatter Integration**: Integrated `<chatter/>` for audit logging & activity tracking.
- **Guest Folio Integration**: Aggregation of guest billing history, folio count, and total spend.
- **Views**: Kanban (grouped by VIP status), List, Form (avatar), Search.

### 3. 📅 Booking Management (`hotel.booking`)
- **Auto Sequence**: Reference generator (`BK-00001`).
- **Flexible Booking Types**:
  - **Nightly / Daily**: Calculates duration in days based on nightly rate.
  - **Hourly**: Calculates duration in hours with minimum hour validation.
- **Automated Workflows**:
  - `Check-In` ➔ Sets booking state to `Checked-In` & updates room to `Occupied`.
  - `Check-Out` ➔ Sets booking state to `Checked-Out`, updates room to `Available`, and auto-generates Housekeeping cleaning task.
  - `Cancel` ➔ Frees room availability.
- **Double-Booking Validation**: Prevents overlapping bookings for the same room.
- **Overdue Detection**: Visual warning banner for checked-in guests past scheduled check-out.
- **Views**: Calendar, Kanban, List, Form (with chatter & overdue banner), Search.

### 4. 📈 Seasonal Rate Plans & Dynamic Pricing (`hotel.rate.plan`)
- **Prioritization**: Priority sequence for overlapping seasonal dates.
- **Date Validity**: Configurable active start and end date ranges.
- **Scope**: Applied to all rooms or targeted by room type.
- **Computation Modes**:
  - Fixed Price Override
  - Percentage Increase (+) for Peak/High Season
  - Percentage Discount (-) for Low Season

### 5. 🏷️ Promo Codes & Special Discounts (`hotel.promo.code`)
- **Promo Codes**: Case-insensitive unique promo code matching (e.g., `SUMMER2026`).
- **Discount Types**: Percentage (%) discount or Fixed cash amount.
- **Redemption & Usage Limits**: Max total redemptions with automated usage counter tracking.
- **Exclusive Pricing Rule**: Applying a Promo Code cleanly overrides standard seasonal rate plans.

### 6. 🧹 Housekeeping & Maintenance (`hotel.housekeeping.task`)
- **Automatic Task Trigger**: Auto-creates cleaning tasks upon guest Check-Out.
- **Room Hygiene Tracking**: Clean, Dirty, and Inspecting room statuses.
- **Staff Assignment**: Task assignment to housekeeping personnel with priority management.

### 7. ☕ Extra Services Catalog (`hotel.service`)
- **Service Catalog**: Minibar, Laundry, Room Service, Spa, Transport, etc.
- **Folio Addition**: Auto price and description lookup on guest billing lines.

### 8. 💳 Billing & Invoice System (`hotel.bill` & `hotel.bill.line`)
- **Auto Sequence**: Reference generator (`INV-00001`).
- **One-Click Bill Generation**: "Create Bill" action on Booking auto-populates room charges.
- **Itemized Charges**: Multi-line item support (Room Charge, Minibar, Laundry, Room Service, Other).
- **Tax & Discount Calculation**: Automated tax calculation and promo code discount deductions.
- **Payment Workflow**: `Draft` ➔ `Confirmed` ➔ `Paid` ➔ `Cancelled`.
- **Payment Methods**: Cash, Credit/Debit Card, Bank Transfer, Other.
- **Smart Button Integration**: Direct link & count between Booking and Bills (`💳 Bills`).
- **QWeb PDF Invoicing**: Printable professional PDF invoice / bill report template.
- **Analytics Dashboards**: Pivot and Graph analysis for bookings and revenue.

---

## 📁 Module File Structure

```
odoo_hms/
├── __manifest__.py           ← Module manifest file
├── __init__.py               ← Root init
├── models/
│   ├── __init__.py
│   ├── hotel_room.py         ← Room catalogue
│   ├── hotel_guest.py        ← Guest profiles & folio
│   ├── hotel_booking.py      ← Booking & reservation logic
│   ├── hotel_rate_plan.py   ← Seasonal rates & promo codes
│   ├── hotel_housekeeping.py ← Housekeeping & cleaning tasks
│   ├── hotel_service.py      ← Extra services catalog
│   └── hotel_bill.py         ← Billing & line items
├── security/
│   ├── hotel_security.xml    ← Security groups (Receptionist, Admin)
│   └── ir.model.access.csv   ← Access control list (ACL)
├── data/
│   ├── ir_sequence_data.xml  ← BK-00001 sequence
│   └── ir_sequence_bill.xml  ← INV-00001 sequence
├── views/
│   ├── menu.xml              ← Root & sub-menus
│   ├── room_views.xml        ← Room views
│   ├── guest_views.xml       ← Guest views
│   ├── booking_views.xml     ← Booking views
│   ├── rate_plan_views.xml   ← Dynamic rate plan & promo code views
│   ├── housekeeping_views.xml← Housekeeping views
│   ├── service_views.xml     ← Extra service views
│   └── bill_views.xml        ← Bill views
├── reports/
│   ├── reports.xml           ← QWeb PDF report actions
│   └── bill_report_templates.xml
└── docs/
    └── hms_workflow_diagrams.drawio ← Architectural workflow diagram
```

---

## 🔒 Security Groups

| Group | Category | Permissions |
|---|---|---|
| **Receptionist** (`group_hotel_receptionist`) | Hotel Management | Manage bookings, check-in/out, guests, view rooms & rate plans |
| **Manager / Admin** (`group_hotel_admin`) | Hotel Management | Full CRUD & Unlink access on rooms, rate plans, promo codes, guests, bookings, bills |

---

## 🛠️ Installation & Setup

1. Place `odoo_hms` in your Odoo 18 custom addons directory.
2. Start Odoo server and update module list:
   ```bash
   python3 odoo-bin -c odoo.conf -d your_database -u odoo_hms --stop-after-init
   ```
3. Open Odoo web interface and navigate to **Hotel Management** menu.

---

## 📄 License

LGPL-3 (Odoo Community License)
