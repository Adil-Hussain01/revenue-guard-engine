# 🗺️ The User Journey: How to Use Revenue Guard

If you're looking at the code or the local interface and wondering, *"Who is doing what?"* and *"What do I click first?"*, this is the guide for you.

---

## 1. The Cast of Characters (Who is doing what?)

Think of this project as a story with three people working in a company:

1.  **"Sam" (The Salesperson):** Sam uses a tool called the **CRM**. Sam records sales like, *"I just sold a $100 widget to Bob."*
2.  **"Fiona" (The Finance Person):** Fiona uses a tool called the **Accounting System**. Fiona sends the bills. She says, *"I just billed Bob $100 for a widget."*
3.  **"The Engine" (Your Project):** This is the automated auditor. It watches both Sam and Fiona. If Sam says "Sold for $100" but Fiona sends a bill for "$80", the Engine screams: **"LEAKAGE DETECTED!"** 🚩

---

## 2. The Step-by-Step "User Journey"

When you use this project on your computer, you are acting as the **Manager** who wants to find the leakage.

### Step A: The Setup (Generating the World)
Before you can find mistakes, you need data.
*   **What to do:** Run `python generate_data.py` in your terminal.
*   **Why?** This "creates the world." It populates the CRM with sales and the Finance system with bills. It intentionally sprinkles "mistakes" in there so you have something to find.

### Step B: The Investigation (The API Playground)
Now you want to see the "notebooks" (the CRM and Finance data) and run the audit.
*   **Where to go:** [http://localhost:8000/playground](http://localhost:8000/playground)
*   **What to look for:** This is the "Technical Interface." It’s a list of everything the system can do.
*   **How to use it:**
    1.  Click **"CRM Simulator"** -> `GET /api/v1/crm/orders`. Click "Try it out" and "Execute." You are now looking at Sam's sales notebook.
    2.  Click **"Finance System"** -> `GET /api/v1/finance/invoices`. Click "Try it out" and "Execute." You are now looking at Fiona's billing records.
    3.  **THE MAGIC BUTTON:** Click **"Validation & Risk Scoring Engine"** -> `POST /run-full-scan`. Click "Try it out" and "Execute."
        *   *What happened?* The Engine just compared the sales notebook to the billing records and found every single mismatch.

### Step C: The Management Review (The Dashboard)
Raw data is hard to read. You want to see the charts.
*   **Where to go:** [http://localhost:8001](http://localhost:8001) (After running the dashboard command in your terminal).
*   **What to do:** 
    1.  Look at the **"Total Leakage Found"** number. This is the real money you just saved.
    2.  Check the **"High Risk Transactions"** table. These are the specific "Sam vs Fiona" mismatches that need your attention.
    3.  Click the **"Refresh"** button to re-run the detective sync.

---

## 3. Real Example of "Leakage" in this System

While you are using the interface, you might see a result like this:

*   **Order ID:** `ORD-12345`
*   **Message:** *"Price drift of 15% detected."*
*   **What it means:** Sam (Sales) promised the customer a price of $1,000, but Fiona (Finance) only sent a bill for $850. 
*   **The Result:** Your business just "leaked" $150. The Engine found it so you can go fix the invoice before the customer pays the wrong amount.

---

## 4. Summary of the Goal

**Why are we building this?**
In a small business, a manager can check these things manually. In a big business with 10,000 sales a month, a human cannot do it. 

**This project creates a "Smart Assistant" that:**
1.  **Simulates** a busy business environment.
2.  **Identifies** financial holes automatically.
3.  **Visualizes** the danger zones for the business owner.

---

### 🚀 Next Step for You:
1.  Go to [http://localhost:8000/playground](http://localhost:8000/playground).
2.  Run the **`POST /run-full-scan`** command.
3.  Look at the list of errors it gives back—that is the "Engine" doing its job!
