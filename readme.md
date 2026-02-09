# Employee Performance & Project Billing Analytics Platform

---

## **Project Overview**

This is a **full-stack web application** designed for **employee performance tracking** and **project billing analysis**.

The system consists of:
- A **Flask (Python) backend**
- A **React (TypeScript) frontend**

The backend is responsible for processing employee data and work reports, performing analytics, and integrating with **Google Sheets** and **Google Gemini AI** for **natural language querying** and **chart generation**.

The frontend provides a rich user interface for interacting with the system, including:
- A conversational **chat interface**
- **Employee listing** and analysis
- **Advanced filtering** options
- **Dynamic chart visualizations**

---

## **Detailed Component Breakdown**

---

## **Backend (Python / Flask)**

---

### **1. Base Data Processor (`base_processor.py`)**

#### **Purpose**
Acts as the **central data handling and preprocessing layer** of the application.

#### **Responsibilities**
- Loads employee data from a **CSV file**
- Loads work report data from **Google Sheets**
- Cleans, normalizes, and processes all incoming data
- Builds internal mappings and summary statistics used by all other analyzers

#### **Key Methods**

##### **`__init__`**
- Initializes the processor with:
  - Employee CSV file path
  - Google Sheet URL
- Automatically calls **`load_data()`** during initialization

##### **`load_data`**
- Loads employee data from the CSV file
- Extracts employee names and email addresses
- Loads work reports from Google Sheets  
  - If Google Sheets data is unavailable, an empty DataFrame is used
- Performs extensive data cleaning:
  - Normalizes project names
  - Parses date fields
  - Calculates hours worked per day
  - Calculates task counts
- Builds mappings between:
  - Employee emails
  - Employee names
- Computes submission statistics for each employee

##### **`get_work_data_for_billing`**
- Returns a processed DataFrame
- Data is formatted specifically for **billing analysis and SOW enforcement**

##### **`find_employee_by_name`**
- Performs **partial name matching**
- Returns the corresponding employee email

##### **`get_employees_list`**
- Returns a list of employees with:
  - Employee ID
  - Name
  - Email address

##### **`get_employee_summary`**
- Returns high-level statistics including:
  - Total number of employees
  - Employees who submitted today
  - Employees who did not submit today

---

### **2. Individual Analyzer (`individual_analyzer.py`)**

#### **Purpose**
Provides **detailed performance analytics for a single employee**.

#### **Key Method**

##### **`get_employee_detailed_metrics`**

Calculates a comprehensive set of employee-level metrics, including:

- Submission rate
- Number of days submitted
- Number of days missed
- Maximum gap between submissions
- Average daily working hours
- Average tasks completed per day
- Task completion ratio
- Task diversity score
- Recent activity:
  - Last 7 days submissions
  - Last 30 days submissions
- Identification of:
  - Underutilized days
  - Overloaded days
- Project-wise work distribution
- Task category breakdown
- Primary project focus
- Total hours spent across projects

---

### **3. Team Analyzer (`team_analyzer.py`)**

#### **Purpose**
Provides **aggregate analytics at the team level**.

#### **Key Method**

##### **`get_team_overview_metrics`**

Aggregates individual employee metrics to produce team-wide insights, including:

- Overall status breakdown
- Average submission rate across the team
- Average daily working hours
- Count of:
  - Consistent reporters
  - Partial reporters
  - Frequent defaulters
- Project distribution across the team
- Identification of cross-project contributors

---

### **4. Project Billing Analyzer (`project_billing_analyzer.py`)**

#### **Purpose**
Analyzes **project billing data** while enforcing **Statement of Work (SOW)** rules.

#### **Project-Specific Rules**

##### **Lyell Project**
- **ETL** and **Reporting** categories are capped at **4 hours per day**
- Other categories such as:
  - Development
  - Testing
  - Architect
  - Other  
  have **no daily cap**

##### **DataPlatr Project**
- No category-level hour caps
- All logged hours are considered valid

#### **Key Methods**

##### **`get_project_billing_summary`**
- Returns a comprehensive billing summary for a given project, including:
  - Daily billing breakdown
  - Total billed hours
  - Category-wise breakdown
  - SOW violations (if any)

##### **`get_daily_billing_report`**
- Generates a detailed billing report for a specific day

##### **`get_all_projects_summary`**
- Returns billing summaries for all projects in the system

---

### **5. Chart Generator (`chart_generator.py`)**

#### **Purpose**
Prepares **chart-ready data** for frontend visualizations.

#### **Key Method**

##### **`get_chart_data`**
- Integrates outputs from:
  - **`TeamAnalyzer`**
  - **`IndividualAnalyzer`**
- Produces chart-formatted datasets including:
  - Status distribution
  - Top submitters based on submission rate
  - Top contributors based on average daily hours
  - Team-level averages and counts

---

### **6. Google Sheets Connector (`google_sheet_connector.py`)**

#### **Purpose**
Handles **data ingestion from Google Sheets**.

#### **Key Method**

##### **`get_work_reports`**
- Downloads work report data using Google Sheets CSV export
- Parses the CSV data into a **Pandas DataFrame**

---

### **7. Smart App (`smart_app.py`)**

#### **Purpose**
Acts as the **main Flask application** and **AI orchestration layer**.

#### **Key Features**

- **API Key Rotation**
  - Manages multiple Google Gemini API keys
  - Automatically rotates keys when quota limits are reached

- **Intent Classification**
  - Uses Gemini to identify user intent:
    - Billing queries
    - Employee performance
    - Team overview
    - Filtering requests

- **Intelligent Response Generation**
  - Generates natural language responses
  - Includes structured JSON for chart rendering

#### **API Endpoints**

- **`/health`** – Health check endpoint  
- **`/employees`** – Retrieve employee list  
- **`/employee-summary`** – High-level summary statistics  
- **`/chat`** – Main natural language chat endpoint  
- **`/employee/<email>`** – Detailed employee analytics  
- **`/project-billing/<project_name>`** – Project billing analysis  
- **`/filter-employees`** – Advanced employee filtering  
- **`/available-filters`** – Fetch filter metadata  
- **`/api-status`** – Gemini API key status  
- **`/reset-api-keys`** – Reset failed API keys  

---

## **Frontend (React / TypeScript)**

---

### **1. Main App (`App.tsx`)**

#### **Purpose**
Acts as the **root component** of the frontend.

#### **Key Features**
- Fetches employee data and summary metrics on initial load
- Manages application state:
  - Employees
  - Summary statistics
  - Chat messages
  - Loading indicators
- Sends user queries to the backend
- Handles and displays backend responses

---

### **2. Header (`Header.tsx`)**

#### **Purpose**
Displays the application header.

#### **Features**
- Logo display
- Menu toggle button

---

### **3. Sidebar (`Sidebar.tsx`)**

#### **Purpose**
Displays **team overview and employee navigation**.

#### **Key Features**
- Team summary cards
- Toggleable employee list
- Click-to-analyze individual employees

---

### **4. Chat Interface (`ChatInterface.tsx`)**

#### **Purpose**
Primary user interaction area.

#### **Key Features**
- Displays user and system messages
- Supports chart rendering inside messages
- **Smart Filters** for:
  - Project
  - Performance status
  - Date range
- Suggested questions grouped by category
- Input form for natural language queries

---

### **5. Message Bubble (`MessageBubble.tsx`)**

#### **Purpose**
Renders individual chat messages.

#### **Key Features**
- Markdown-style text formatting
- Embedded charts when chart data is present

---

### **6. Dynamic Chart (`DynamicChart.tsx`)**

#### **Purpose**
Renders charts dynamically based on backend responses.

#### **Supported Chart Types**
- Bar
- Line
- Pie
- Doughnut
- Radar
- Scatter

---

### **7. Smart Search Filters (`SmartSearchFilters.tsx`)**

#### **Purpose**
Provides advanced filtering capabilities.

#### **Key Features**
- Filter employees by:
  - Project
  - Status
  - Date range
- Quick presets:
  - Top Performers
  - Need Attention
- Active filter visualization and management

---

## **Data Flow**

---

### **Initialization**
- Backend loads employee data from CSV
- Work reports are fetched from Google Sheets
- Data is cleaned, normalized, and analyzed

### **User Interaction**
- User submits a natural language query
- Backend:
  - Classifies intent
  - Fetches relevant analytics
  - Uses Gemini AI to generate response and chart data
- Frontend renders text and charts

### **Filtering**
- User applies filters via Smart Filters UI
- Filters are converted into a natural language query
- Backend processes and returns filtered insights

---

## **Key Features**

- **AI-powered natural language analytics**
- **Dynamic chart generation**
- **SOW-enforced project billing**
- **Advanced employee filtering**
- **Real-time Google Sheets data ingestion**
- **Gemini API key rotation for quota management**

---

## **Deployment**

---

### **Backend**
- Flask application
- Can be deployed using **Gunicorn** or any WSGI server
- Runs on **port 8080** (configurable via environment variables)

### **Frontend**
- React production build
- Served via a static file server
- Typically runs on **port 3000**

---

## **Environment Variables**

- **Google Gemini API keys** (configured in `smart_app.py`)
- **Google Sheets URL**
- **Employee CSV file path**

> These values are currently hardcoded and can be externalized for production use.

---

## **Conclusion**

This platform is a **comprehensive employee performance and project billing analytics solution**.  
It combines **data engineering**, **analytics**, and **AI-driven natural language interaction** to deliver deep insights in an intuitive interface.



















# **END-TO-END APPLICATION WORKING EXPLANATION**

This section explains **how the application works from start to finish**, covering backend startup, frontend interaction, AI processing, analytics, and real-world usage scenarios.

---

## **PHASE 1: DATA LOADING & SETUP (BACKEND STARTUP)**

### **User Action**
- Starts the backend server (`smart_app.py`)

### **What Happens**

### **1. Load Employee Master Data**
- Reads employee CSV file (`Dataplatr_employees.csv`)
- Extracts employee names and emails from formats like:
  - `John Doe <john@company.com>`
- Builds a master list of **50+ employees** with normalized email IDs

### **2. Connect to Work Reports**
- Fetches work reports from **Google Sheets** (CSV export)
- Each report includes:
  - Date
  - Employee Name
  - Project
  - Tasks
  - Hours Spent

### **3. Process & Normalize Data**
- Normalize emails:
  - `John.Doe@Company.com` → `john.doe@company.com`
- Parse dates into standard format
- Convert hours:
  - `4 hr 30 min` → `4.5 hours`
- Normalize project names:
  - `Lyell Project` → `lyell`

### **4. Build Smart Indexes**
- Map multiple email variants → single employee
- Track daily submissions per employee
- Pre-calculate basic statistics for fast access

### **5. Initialize AI Engine**
- Load **5 Google Gemini API keys**
- Enable automatic **API key rotation**
- Prepare AI for intent classification and analytics

### **Result**
 Backend is fully initialized with processed data and AI readiness

---

## **PHASE 2: USER OPENS WEB APPLICATION (FRONTEND)**

### **User Action**
- Opens browser and navigates to application URL

### **What Happens**

### **1. React Application Loads**
- Displays loading screen briefly
- Renders main UI:
  - Header (App branding)
  - Sidebar (collapsed)
  - Chat interface with welcome message
  - Smart filters bar (blue gradient)

### **2. Initial API Calls**
- `GET /employees` → Fetch employee list
- `GET /employee-summary` → Fetch daily summary

Example:
```json
{
  "total_employees": 52,
  "submitted_today": 38,
  "not_submitted_today": 14
}
````

### **3. Welcome Message**

* AI introduces capabilities
* Suggests example questions
* App is ready for interaction

---

## **PHASE 3: USER ASKS FIRST QUESTION**

### **User Action**

* Types: **"How is Sarah Johnson doing?"**

### **Frontend Flow**

1. User message appears (right-aligned)
2. Typing indicator is shown
3. POST request sent to `/chat`:

```json
{ "query": "How is Sarah Johnson doing?" }
```

### **Backend Flow**

#### **Step 1: Intent Classification**

AI identifies:

```json
{
  "intent": "employee_performance",
  "employee": "Sarah Johnson",
  "timeframe": "all_time"
}
```

#### **Step 2: Employee Resolution**

* Finds primary email: `sarah.j@company.com`
* Collects all email variants

#### **Step 3: Metric Calculation**

* Days analyzed: 60
* Days submitted: 54
* Submission rate: **90%**
* Avg daily hours: **7.8**
* Tasks/day: **3.2**
* Status: **Excellent**
* Primary project: **Lyell (65%)**
* Recent activity: **6 of last 7 days**

#### **Step 4: AI Analysis**

Gemini AI:

* Explains performance
* Highlights strengths & risks
* Suggests best chart type

#### **Step 5: Response Returned**

* Cleaned AI text
* Extracted chart JSON
* Sent back to frontend

### **Frontend Display**

* AI explanation (left-aligned)
* Radar chart visualizing metrics
* Auto-scroll to latest message

---

## **PHASE 4: SMART FILTER USAGE**

### **User Action**

* Clicks **“Top Performers”** filter

### **What Happens**

1. Frontend creates query:
   **"Show top performing employees"**
2. Backend:

   * Fetches all employee metrics
   * Filters status = Excellent / Good
   * Sorts by submission rate
   * Selects top 10
3. AI analyzes patterns
4. Bar chart compares submission rates

### **User Sees**

* Ranked list of top performers
* Visual comparison chart
* AI insights on common success patterns

---

## **PHASE 5: PROJECT BILLING ANALYSIS**

### **User Action**

* Types: **"Show Lyell billing violations"**

### **Backend Billing Logic**

#### **Step-by-Step**

1. Filter work reports for **Lyell**
2. Categorize tasks:

   * ETL
   * Reporting
   * Development
3. Apply SOW rules:

   * ETL / Reporting → Max 4 hrs/day
4. Identify violations:

   * Extra hours beyond cap
5. Aggregate results:

   * Total billable hours
   * Total extra hours
   * Violation days
6. Detect patterns:

   * Most violations on Tuesdays
   * ETL is main contributor

### **AI Output**

* Compliance summary
* Risk explanation
* Optimization recommendations
* Line / bar chart visualization

---

## **PHASE 6: COMPARISON QUERY**

### **User Action**

* Types: **"Compare John and Sarah"**

### **Backend Processing**

* Fetch metrics for both employees
* Compare:

  * Submission rate
  * Hours
  * Project focus

### **AI Insights**

* Sarah more consistent
* John more versatile across projects
* Suggested role alignment

### **Frontend**

* Side-by-side comparison
* Bar chart visualization
* Clear recommendations

---

## **PHASE 7: COMPLEX FILTERED ANALYSIS**

### **User Action**

* Filters:

  * Project: Lyell
  * Status: Excellent & Good
  * Date range: Last 30 days
* Asks: **"Analyze this group"**

### **Backend**

* Applies filters
* Analyzes only matching employees
* Computes subgroup metrics
* AI generates targeted insights

### **Result**

 Highly focused analysis for specific employee segment

---

## **PHASE 8: REAL-WORLD MANAGER WORKFLOW**

### **Morning Usage Example**

**7:30 AM**

* Opens app → Team Overview
* Sees:

  * 82% submission rate
  * Top 3 performers
  * Employees needing attention

**8:00 AM**

* Clicks “Need Attention”
* AI finds:

  * Monday submission gaps
  * DataPlatr workload pattern

**9:00 AM**

* Reviews Lyell project
* Identifies ETL bottleneck
* Billing compliance insights

**10:00 AM**

* Asks: *“What should I discuss in the team meeting?”*
* AI generates meeting agenda + charts

---

## **PHASE 9: SIMPLE DATA FLOW SUMMARY**

```
Employee → Google Sheet → Backend Processing → AI Analysis → Frontend Visualization
```

Insights delivered in **under 5 seconds**.

---

## **PHASE 10: CORE BACKEND PROCESSING LOOP**

For every query:

1. Understand intent (AI)
2. Resolve employee/project
3. Filter relevant data
4. Compute metrics
5. Build AI context
6. Generate insights
7. Select chart type
8. Return response + chart

---

## **PHASE 11: WHAT MAKES THIS APP SMART**

### **1. Natural Language Understanding**

* No fixed commands
* Human-friendly queries

### **2. Multi-Dimensional Intelligence**

* Links employees, projects, hours, billing

### **3. Automated Visualization**

* No manual chart configuration
* AI-driven chart selection

### **4. Action-Oriented Insights**

* Explains *what*, *why*, and *what to do next*

---

## **PHASE 12: FINAL USER IMPACT**

### **Before This App**

* 1–2 hours daily in Excel
* Manual reports and charts
* Reactive management

### **After This App**

* 5-minute daily check-ins
* AI-powered insights
* Proactive decision-making
* Data-driven leadership

---

**END OF END-TO-END WORKFLOW**


