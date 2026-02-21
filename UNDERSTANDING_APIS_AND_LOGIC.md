# 🎓 Foundations: How APIs and "The Engine" Actually Work

If you've been clicking "Try it Out" and "Execute" but feeling like you're just pressing random buttons, this guide is for you. We are going to explain the **technical words** and the **internal logic** so you can explain it to a client or a CEO with confidence.

---

## 1. What is an "API"? (The Restaurant Analogy)

Imagine you are at a restaurant:
*   **You (The User):** You are sitting at the table with the menu.
*   **The Kitchen (The Database):** This is where the food (the data) is stored and cooked.
*   **The Waiter (The API):** The waiter takes your order to the kitchen and brings the food back to you.

The **API Playground** is simply a digital "Menu." Each "endpoint" (the colored boxes) is a different order you can give the waiter.

### Common "Orders" (The Action Words):
*   🟢 **GET (Request Information):** This is like asking the waiter, *"What's on the menu?"* or *"Can I see my bill?"* You aren't changing anything; you are just **looking** at data.
*   🔵 **POST (Create Something New):** This is like saying, *"I want to order a Cheeseburger."* You are **adding** a new record to the kitchen's list.
*   🟠 **PUT/PATCH (Modify):** This is like saying, *"Actually, put extra cheese on that burger."* You are **changing** an existing record.
*   🔴 **DELETE (Remove):** This is like saying, *"Cancel my order."*

---

## 2. Breaking Down the Playground Sections

When you look at [http://localhost:8000/playground](http://localhost:8000/playground), you see different headers. Here is what they represent in our "Business Story":

### 🏢 Section 1: CRM Simulator (The "Sales" Book)
This is where the Sales Team records their work.
*   **`GET /contacts`**: "Show me my list of customers."
*   **`POST /orders`**: "I just closed a new sale! Add it to the list."

### 💰 Section 2: Finance System (The "Accounting" Book)
This is where the Accountants record the bills they sent.
*   **`GET /invoices`**: "Show me all the bills we sent out."
*   **`POST /payments`**: "The customer just paid us! Record the money."

### 🧠 Section 3: Validation & Risk Scoring (The "Detective")
This is the "Smart" part of your project. It doesn't belong to Sales or Finance; it sits **above** both of them to check for lies or mistakes.
*   **`POST /run-full-scan`**: This is the most important button. It tells the Detective: *"Go grab the Sales Book and the Accounting Book, compare them line-by-line, and tell me where the money is missing."*

---

## 3. How the Logic Works (The "Behind-the-Scenes" Loop)

When you click **"Execute"** on a `run-full-scan`, here is what happens in the code (in milliseconds):

1.  **Data Fetching:** The system looks at your `generated_data/` folder (the CSV/JSON files).
2.  **Matching:** It looks for a "Social Security Number" for the transaction (we call this a **Correlation ID**). It finds a Sale in the CRM and tries to find the match in Finance.
3.  **Rule Check:** It runs the **12 Rules**.
    *   *Rule 1:* Does the price match?
    *   *Rule 2:* Is it a duplicate?
    *   *Rule 3:* Is the status correct?
4.  **Risk Math:** If a rule fails, it looks at the **Weight**. A $10,000 mistake is weighted much heavier than a $1 mistake.
5.  **Audit Trail:** It writes a "Diary Entry" in the `logs/` folder so you have proof of the mistake.
6.  **The Answer:** It sends back the list you see on your screen.

---

## 4. How to Practically Use & Explain It

If you were showing this to someone else, here is how you should narrate your actions:

**Action 1: Generate Data**
> *"First, I'm going to simulate a month of business. I'm creating 1,000 transactions. Most are perfect, but some have human errors hidden inside."*

**Action 2: Show the API Playground**
> *"Now, I'm opening the 'Bridge' between our departments. Notice we have a CRM department and a Finance department. Usually, these two don't talk to each other well."*

**Action 3: Execute a Full Scan**
> *"Watch this. I'm going to run a 'Full Scan.' The system is now comparing the Sales records to the Bank records. In 1 second, it just successfully audited a month of work."*

**Action 4: Show the Result**
> *"See this 'Price Drift' error? The salesperson promised one price, but the bill was sent for another. We just caught a $200 leak that a human would have missed."*

---

### 🧩 Key Terms Summary for You:

*   **Endpoint:** A specific "box" or URL in the playground.
*   **Request:** When you click Execute (you asking the question).
*   **Response:** The text that appears below (the system answering you).
*   **Payload:** Information you send **to** the system (like an Order ID).
*   **Schema:** The "Structure" of the data (like saying an Order must have a name, date, and price).

*This guide should help you feel like the "Master" of the engine! You aren't just clicking buttons; you are directing an automated financial audit.*
