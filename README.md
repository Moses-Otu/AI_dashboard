# 🚘 Shuttlers AI Analytics Dashboard

**Empowering teams through the democratization of data**

[👉 Launch the App](https://aidashboard-mosesotu.streamlit.app/)

---

## 📌 Overview

This interactive AI dashboard makes it easy for any member of the team—technical or not—to explore and analyze Shuttlers’ operational and user data using natural language.

Ask questions like “Which route has the highest number of rides this month?” and get instant answers—complete with the underlying SQL query and tabular results.

---

## 🌍 Democratization of Data

Making data accessible to everyone across the organization empowers faster, smarter decisions. 

The AI Assistant in this app allows all teams—from operations to marketing—to:

- Ask questions in plain English
- Run safe and secure queries
- Visualize and export results
- Gain insights independently

---

## 🔐 Secured by Databricks

This dashboard is backed by **Databricks** with enterprise-grade security:

- Unity Catalog for fine-grained access control
- Token-based authentication
- SQL Warehouses with scalable compute
- Role-based access for sensitive tables

---

## 🤖 How AI is Used

Using **Meta Llama 3.3 (70B Instruct)** via Databricks' `ai_query` function, the app translates natural language questions into Spark SQL. This makes it possible for everyone—even those without SQL skills—to get value from data instantly.

---

## 🧠 Tables Available

The AI assistant has access to the following tables from the `agent.shuttler` schema:

| Table                  | Sample Columns |
|------------------------|----------------|
| `ride_bookings`        | RideID, UserID, RouteID, VehicleID, ScheduledTime, Fare |
| `ride_users`           | UserID, Name, Gender, Age, SubscriptionType |
| `vehicles`             | VehicleID, LicensePlate, Capacity, AssignedDriverID |
| `drivers`              | DriverID, Name, Rating, EmploymentType |
| `routes`               | RouteID, RouteName, Stops, AvgDurationMin |
| `companies`            | CompanyID, CompanyName, StaffCount |
| `company_users`        | CompanyID, UserID, SubsidyPercent |
| `feedback`             | FeedbackID, RideID, Rating, Comment |
| `incidents`            | IncidentID, RideID, Type, Status |
| `payments`             | PaymentID, UserID, Amount, PaymentMethod |
| `subscriptions`        | SubscriptionID, UserID, Type, StartDate |

---

## 💡 Sample Questions You Can Ask

Here are some example questions you can ask the assistant:

1. Total number of distinct users?
2. Bin users age by generations?
3. Which vehicle has been used the most and who is the assigned driver?
4. What is the total payment amount for each user with active subscriptions?

---

## 🧰 Tech Stack

- **Streamlit** – Frontend app
- **Databricks SQL** – Backend query engine
- **Meta Llama 3.3 70B** – AI natural language to SQL
- **Pandas** – Result handling
- **Plotly Express** – Visualizations
- **Python & .env** – App logic and config

---

## ⚙️ Running Locally

### 1. Clone this repository

```bash
git clone https://github.com/Moses-Otu/AI_dashboard.git
cd AI_dashboard
