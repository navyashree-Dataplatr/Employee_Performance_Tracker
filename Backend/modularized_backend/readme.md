# Employee Performance Analytics System

## Overview

This project is a **backend analytics engine for employee performance tracking and HR insights**, designed to transform raw daily work-report data into **actionable insights, comparisons, and visual-ready analytics**. The system combines **rule-based analytics** with **LLM-powered natural language insights** (Google Gemini) and is built to support **individual analysis, team-level analysis, employee comparisons, and dynamic chart generation**.

The core idea is simple:

* Employees submit daily work reports (tasks completed, time spent).
* HR or managers ask natural-language questions.
* The system intelligently routes the query.
* Structured metrics + AI-generated insights + chart-ready JSON are returned.

This backend is UI-agnostic and can be connected to **React, Streamlit, dashboards, or chat-based interfaces**.

---

## Key Capabilities

* Employee master data cleaning and normalization
* Robust email and name matching (handles aliases and variants)
* Daily submission discipline tracking
* Productivity and workload analysis
* Individual employee performance reports
* Team-wide analytics and distributions
* Employee-to-employee comparisons
* LLM-generated managerial insights (Gemini)
* **Dynamic chart JSON generation (no hardcoded charts)**
* Fallback logic when LLM output is invalid or unavailable

---

## High-Level Architecture

```
CSV Inputs
 ├── employees.csv
 └── GOOGLE SHEET
        ↓
BaseDataProcessor
        ↓
IndividualAnalyzer  ←→  TeamAnalyzer
        ↓
ChartGenerator
        ↓
DataProcessor (Orchestrator + Gemini Integration)
        ↓
Frontend / API / Chat UI
```

Each layer has a **single responsibility**, making the system modular, testable, and extensible.

---

## Tech Stack

* **Language:** Python
* **Data Processing:** Pandas
* **AI Model:** Google Gemini (gemini-2.5-flash)
* **Input Format:** CSV
* **Output Format:** JSON (text + chart-ready data)

---

## File-by-File Detailed Explanation

---

## 1. `base_processor.py`

### Purpose

This file is the **foundation of the entire system**. It is responsible for:

* Loading raw CSV files
* Cleaning and normalizing employee data
* Parsing dates, hours, and tasks
* Mapping multiple email aliases to a single employee
* Calculating working days and submission history

Every other module depends on the correctness of this layer.

### Key Responsibilities

#### Employee Data Processing

* Extracts names and emails from mixed formats like:

  * `John Doe <john@company.com>`
  * `john@company.com`
* Supports **multiple email aliases per employee**
* Chooses one primary email per employee

#### Work Report Processing

* Normalizes email casing and spacing
* Converts textual time formats into numeric hours

  * `8 hrs`, `7.5 hr`, `30 min`, etc.
* Extracts task counts from free-text task descriptions

#### Submission Tracking

* Calculates:

  * Total working days
  * Submission dates per employee
  * Min and max analysis date

#### Output Data Structures

* `master_df`: Clean employee master table
* `work_df`: Normalized work reports
* `employee_all_emails`: Maps primary email → all aliases
* `submissions`: Tracks submitted dates per employee

This class ensures **dirty real-world data becomes analytics-ready**.

---

## 2. `individual_analyzer.py`

### Purpose

This module computes **deep, employee-level performance metrics** using data prepared by `BaseDataProcessor`.

### Metrics Calculated

#### Submission Discipline

* Days submitted vs total days
* Days missed
* Submission rate (%)
* Maximum consecutive gap (discipline risk indicator)

#### Productivity & Workload

* Average daily working hours
* Average tasks completed per day
* Completion ratio (tasks vs reports)
* Task diversity (repetitiveness vs variety)

#### Recent Activity

* Submissions in last 7 days
* Submissions in last 30 days

#### Workload Balance

* Underutilized days (< 8 hrs)
* Overloaded days (> 10 hrs)

#### Performance Status Classification

Each employee is categorized into:

* Excellent
* Good
* Inconsistent
* Poor
* Very Poor
* Non-Reporter

This classification is later used heavily in **team analytics and charts**.

---

## 3. `team_analyzer.py`

### Purpose

This module aggregates **all individual metrics** to generate **team-wide intelligence**.

### Team-Level Insights

* Status distribution (Excellent, Good, Poor, etc.)
* Consistent reporters vs defaulters
* Average submission rate
* Average daily hours
* Average tasks per day
* Employees with consecutive gaps
* Workload imbalance percentages

### Advanced Outputs

* **Top Performers** (highest submission rates)
* **Bottom Performers** (lowest submission rates)
* **High Performers / Multi-taskers** (tasks per day > threshold)

This layer answers leadership-level questions like:

> “How healthy is the team overall?”

---

## 4. `chart_generator.py`

### Purpose

This module converts analytics into **chart-ready structured data**, without hardcoding any chart logic.

### What It Does

* Extracts key metrics from team and individual analyzers
* Prepares datasets for:

  * Status distribution
  * Top submitters
  * Average daily hours
* Sorts and limits data (Top 10, etc.)

### Output Format

The output is **pure JSON**, designed to be consumed directly by chart libraries like:

* Chart.js
* Recharts
* ECharts

No UI assumptions are made at this layer.

---

## 5. `data_processor.py`

### Purpose

This is the **brain of the system**.

It acts as:

* Orchestrator
* Query router
* Gemini LLM integrator
* Final response formatter

### Key Responsibilities

#### Query Routing Logic

Based on user input, the query is routed to:

* Individual analysis
* Team insights
* Comparison analysis
* General guidance

#### Natural Language Intelligence

Uses **Google Gemini** to:

* Generate professional, manager-friendly explanations
* Interpret metrics in real-world terms
* Produce structured chart JSON dynamically

#### Chart + Text in One Response

Each response contains:

* Narrative insights (text)
* `chartData` object (JSON)

#### Fallback Logic

If:

* Gemini fails
* JSON parsing fails

The system:

* Automatically generates rule-based chart data
* Ensures the UI always receives valid output

This guarantees **high reliability even with free or rate-limited APIs**.

---

## Input Data Requirements

### Employees CSV

Required columns (order matters):

* Name_Email
* Mobile_Number
* Emergency_Contact_Number
* Emergency_Contact_Name

### Work Reports CSV

Required columns:

* Timestamp
* Email_Address
* Name
* Date
* Tasks_Completed
* Time_Spent

---

## Example Queries Supported

* "How is Navya performing?"
* "Compare Alice and Bob"
* "Who are the top performers?"
* "Which employees need attention?"
* "Give me overall team performance"
* "Show workload distribution"

---

## Output Structure (Standard)

```json
{
  "response": "Textual insights for managers",
  "type": "individual | team | comparison | general",
  "metrics": { },
  "chartData": {
    "chartType": "bar | pie | line | radar",
    "labels": [],
    "datasets": [],
    "options": {}
  }
}
```

---

## Design Principles

* Separation of concerns
* No hardcoded business logic in UI
* LLM-assisted but not LLM-dependent
* Deterministic fallbacks
* Scalable for future data sources


