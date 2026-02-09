# import google.generativeai as genai
# import os
# import json
# from base_processor import BaseDataProcessor  
# from individual_analyzer import IndividualAnalyzer 
# from team_analyzer import TeamAnalyzer 
# from chart_generator import ChartGenerator 

# class DataProcessor:
#     def __init__(self, employees_csv, work_reports_csv):
#         # Initialize all modules
#         self.base = BaseDataProcessor(employees_csv, work_reports_csv)
#         self.individual = IndividualAnalyzer(self.base)
#         self.team = TeamAnalyzer(self.base, self.individual)
#         self.charts = ChartGenerator(self.base, self.individual, self.team)
        
#         # Initialize Gemini AI
#         api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyCGCSu0EKuJCVmUJW3bgJ70enJIo37PSAI')
#         genai.configure(api_key=api_key)
#         self.model = genai.GenerativeModel("gemini-2.5-flash")

import google.generativeai as genai
import os
import json
from base_processor import BaseDataProcessor  
from individual_analyzer import IndividualAnalyzer 
from team_analyzer import TeamAnalyzer 
from chart_generator import ChartGenerator 

class DataProcessor:
    def __init__(self, employees_csv, work_reports_csv=None, google_sheet_url=None):
        """
        Initialize with either work_reports_csv OR google_sheet_url
        """
        # Initialize all modules
        if google_sheet_url:
            # Use Google Sheet
            self.base = BaseDataProcessor(employees_csv, google_sheet_url)
        else:
            # Use local CSV file
            self.base = BaseDataProcessor(employees_csv, work_reports_csv)
            
        self.individual = IndividualAnalyzer(self.base)
        self.team = TeamAnalyzer(self.base, self.individual)
        self.charts = ChartGenerator(self.base, self.individual, self.team)
        
        # Initialize Gemini AI
        api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyCGCSu0EKuJCVmUJW3bgJ70enJIo37PSAI')
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        
    # Delegate methods to appropriate modules
    def get_employees_list(self):
        return self.base.get_employees_list()
    
    def get_employee_summary(self):
        return self.base.get_employee_summary()
    
    def get_employee_detailed_metrics(self, employee_email):
        return self.individual.get_employee_detailed_metrics(employee_email)
    
    def get_team_overview_metrics(self):
        return self.team.get_team_overview_metrics()
    
    def get_comparison_metrics(self, employee_emails):
        return self.individual.get_comparison_metrics(employee_emails)
    
    def get_chart_data(self):
        return self.charts.get_chart_data()
    
    def find_employee_by_name(self, name_query):
        return self.base.find_employee_by_name(name_query)
    
    def find_best_employee_match(self, query):
        """
        Find the best matching employee from the query.
        Returns a single email or None.
        Uses full name matching to avoid partial matches.
        """
        query_lower = query.lower().strip()
        
        # First, check for exact email matches
        for email in self.base.employee_all_emails.keys():
            if email.lower() in query_lower:
                return email
        
        # Then check for full name matches (case insensitive)
        best_match = None
        best_match_length = 0
        
        for idx, row in self.base.master_df.iterrows():
            employee_name = row['Name'].lower()
            
            # Check if the full employee name appears in the query
            if employee_name in query_lower:
                # Prefer longer matches (more specific)
                if len(employee_name) > best_match_length:
                    best_match = row['Email']
                    best_match_length = len(employee_name)
        
        return best_match
    
    def process_query(self, query):
        print(f"\n=== Processing Query: {query} ===")
        query_lower = query.lower()
        
        # Check if this is a comparison query (must have "compare" keyword)
        if 'compare' in query_lower:
            # For comparison, find all mentioned employees
            mentioned_emails = []
            
            # Check for email mentions
            for email in self.base.employee_all_emails.keys():
                if email.lower() in query_lower:
                    mentioned_emails.append(email)
                    print(f"Found email mention: {email}")
            
            # Check for name mentions (only for comparison queries)
            for idx, row in self.base.master_df.iterrows():
                name_lower = row['Name'].lower()
                if name_lower in query_lower and row['Email'] not in mentioned_emails:
                    mentioned_emails.append(row['Email'])
                    print(f"Found name mention: {row['Name']} -> {row['Email']}")
            
            if len(mentioned_emails) >= 2:
                print("Routing to: COMPARISON")
                return self.generate_comparison_insights(query, mentioned_emails)
        
        # Check for team-level queries
        if any(keyword in query_lower for keyword in [
            'team', 'overall', 'all employees', 'company', 'dataplatr', 
            'top performer', 'best performer', 'highest performer',
            'bottom performer', 'worst performer', 'need attention', 'struggling',
            'high performer', 'multi-task',
            'average', 'distribution', 'workload'
        ]):
            print("Routing to: TEAM INSIGHTS")
            return self.generate_team_insights(query)
        
        # For individual queries, find the best single match
        employee_email = self.find_best_employee_match(query)
        
        if employee_email:
            print(f"Routing to: INDIVIDUAL ANALYSIS for {employee_email}")
            return self.generate_individual_insights(query, employee_email)
        else:
            print("Routing to: GENERAL INSIGHTS")
            return self.generate_general_insights(query)
    
    def generate_individual_insights(self, query, employee_email):
        print(f"Generating individual insights for: {employee_email}")
        metrics = self.individual.get_employee_detailed_metrics(employee_email)
        
        if not metrics:
            return {
                'response': f"I couldn't find detailed information for {employee_email}. Please verify the employee email or name.",
                'type': 'error'
            }

        # Build context block
        context = f"""
Employee: {metrics['name']} ({metrics['email']})

SUBMISSION & DISCIPLINE:
- Status: {metrics['status']}
- Days Submitted: {metrics['days_submitted']} out of {self.base.total_days}
- Days Missed: {metrics['days_missed']}
- Submission Rate: {metrics['submission_rate']}%
- Maximum Consecutive Gap: {metrics['max_gap']} days
- Recent Activity (7 Days): {metrics['recent_7_days_submissions']} submissions
- Recent Activity (30 Days): {metrics['recent_30_days_submissions']} submissions

WORKLOAD & PRODUCTIVITY:
- Avg Daily Hours: {metrics['avg_daily_hours']} hrs/day
- Avg Tasks Per Day: {metrics['avg_tasks_per_day']}
- Completion Ratio: {metrics['completion_ratio']}
- Task Diversity Ratio: {metrics['task_diversity']}
- Underutilized Days (<8 hrs): {metrics['underutilized_days']}
- Overloaded Days (>10 hrs): {metrics['overloaded_days']}
- Total Reports Submitted: {metrics['total_reports']}

Analysis Period: {metrics['date_range']}
"""
        
        #  prompt to ask for structured chart data
        prompt = f"""
You are an advanced HR analytics assistant generating a **complete individual performance report**.

Below is the employee's performance data:

{context}

MANAGER QUESTION:
{query}

Generate **ONE single structured output** containing:

1. **Performance Summary (2–3 paragraphs)**
- Clear narrative overview
- Strengths & positive patterns
- Behavior or work trends

2. **Risk & Gap Analysis**
- Productivity concerns
- Submission discipline issues
- Workload imbalance
- Any anomalies or red flags

3. **Data Interpretation**
- Interpret every metric using only the data provided
- Explain what the numbers mean in real terms

4. **Actionable Recommendations (3–5 points)**

5. **CHART DATA STRUCTURE (JSON)**
Generate a JSON object for chart visualization that matches the key insights from your analysis.
The JSON must have this exact structure:
{{
  "chartType": "bar|line|pie|radar|scatter|doughnut",
  "chartTitle": "Descriptive title for the chart",
  "labels": ["Label1", "Label2", ...],
  "datasets": [
    {{
      "label": "Dataset label",
      "data": [value1, value2, ...],
      "backgroundColor": "color or array of colors",
      "borderColor": "border color"
    }}
  ],
  "options": {{
    "xAxisLabel": "X-axis label",
    "yAxisLabel": "Y-axis label"
  }}
}}

IMPORTANT RULES:
- The JSON must be valid and placed at the END of your response.
- Do everything in ONE response.
- Stick ONLY to the provided data.
- Tone must be professional, balanced, and manager-friendly.
- Chart type should be the most appropriate for the data being visualized.
- Use the actual metric values from the data provided.
"""

        try:
            print("Calling Gemini API...")
            response = self.model.generate_content(prompt)
            response_text = response.candidates[0].content.parts[0].text
            print(f"Got response: {response_text[:100]}...")
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                try:
                    chart_data = json.loads(json_str)
                    text_response = response_text[:json_start].strip()
                except json.JSONDecodeError:
                    print("Failed to parse JSON, using fallback")
                    chart_data = self.generate_fallback_chart(metrics, 'individual')
                    text_response = response_text
            else:
                # Fallback: Generate simple chart data from metrics
                chart_data = self.generate_fallback_chart(metrics, 'individual')
                text_response = response_text
            
            return {
                'response': text_response,
                'type': 'individual',
                'metrics': metrics,
                'chartData': chart_data
            }

        except Exception as e:
            print(f"ERROR in generate_individual_insights: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fallback with chart data
            chart_data = self.generate_fallback_chart(metrics, 'individual')
            
            # Fallback text
            fallback = f"""Based on available data for {metrics['name']}:

{metrics['name']} has submitted {metrics['days_submitted']} out of {self.base.total_days} reports ({metrics['submission_rate']}%).
They average {metrics['avg_daily_hours']} daily hours and {metrics['avg_tasks_per_day']} tasks/day with a completion ratio of {metrics['completion_ratio']}.
Recent activity includes {metrics['recent_7_days_submissions']} submissions in the last 7 days and {metrics['recent_30_days_submissions']} in the last 30 days.
The employee recorded {metrics['underutilized_days']} underutilized days (<8 hrs) and {metrics['overloaded_days']} overloaded days (>10 hrs)."""
            
            return {
                'response': fallback,
                'type': 'individual',
                'metrics': metrics,
                'chartData': chart_data
            }
    
    def generate_team_insights(self, query):
        print("Generating team insights...")
        team_metrics = self.team.get_team_overview_metrics()
        
        if not team_metrics:
            return {
                'response': "I couldn't retrieve team metrics at this time. Please ensure data is properly loaded.",
                'type': 'error'
            }
        
        query_lower = query.lower()
        
        # Check if specifically asking for top performers
        if 'top performer' in query_lower or 'best performer' in query_lower or 'highest performer' in query_lower:
            top_performers = team_metrics['top_performers']
            
            response_text = f"""**Top Performers at Dataplatr:**

Based on submission rate and task completion analysis, here are your top 5 performers:

"""
            
            for i, performer in enumerate(top_performers, 1):
                response_text += f"""

{i}. **{performer['name']}**
   - Submission Rate: {performer['submission_rate']}%
   - Average Tasks Per Day: {performer['avg_tasks_per_day']:.2f}
"""
            
            response_text += f"""

These employees demonstrate exceptional consistency in daily reporting and maintain strong productivity levels. They average {team_metrics['avg_tasks_per_day']:.2f} tasks per day compared to the team average, showing reliable engagement with their work.

Consider recognizing these top performers and understanding their work practices, as they can serve as role models for the rest of the team."""
            
            chart_data = {
                "chartType": "bar",
                "chartTitle": "Top Performers - Submission Rates",
                "labels": [p['name'] for p in top_performers],
                "datasets": [
                    {
                        "label": "Submission Rate (%)",
                        "data": [p['submission_rate'] for p in top_performers],
                        "backgroundColor": "rgba(59, 130, 246, 0.7)",
                        "borderColor": "rgb(59, 130, 246)"
                    }
                ],
                "options": {
                    "xAxisLabel": "Employees",
                    "yAxisLabel": "Submission Rate (%)"
                }
            }
            
            return {
                'response': response_text,
                'type': 'team',
                'metrics': team_metrics,
                'chartData': chart_data
            }
        
        # Check if asking for bottom performers or employees needing attention
        elif 'bottom performer' in query_lower or 'worst performer' in query_lower or 'need attention' in query_lower or 'struggling' in query_lower:
            bottom_performers = team_metrics['bottom_performers']
            
            response_text = f"""**Employees Requiring Attention:**

Based on submission patterns, here are 5 employees who may need support:

"""
            
            for i, performer in enumerate(bottom_performers, 1):
                response_text += f"""

{i}. **{performer['name']}**
   - Submission Rate: {performer['submission_rate']}%
   - Maximum Consecutive Gap: {performer['max_gap']} days
"""
            
            response_text += f"""

These employees show lower engagement in daily reporting, with an average submission rate significantly below the team average of {team_metrics['avg_submission_rate']:.1f}%. The consecutive gaps suggest they may be facing challenges with workload, unclear expectations, or other barriers.

**Recommended Actions:**
- Schedule one-on-one meetings to understand any obstacles
- Clarify reporting expectations and provide support
- Consider workload redistribution or additional training"""
            
            chart_data = {
                "chartType": "bar",
                "chartTitle": "Employees Needing Attention - Submission Rates",
                "labels": [p['name'] for p in bottom_performers],
                "datasets": [
                    {
                        "label": "Submission Rate (%)",
                        "data": [p['submission_rate'] for p in bottom_performers],
                        "backgroundColor": "rgba(239, 68, 68, 0.7)",
                        "borderColor": "rgb(239, 68, 68)"
                    }
                ],
                "options": {
                    "xAxisLabel": "Employees",
                    "yAxisLabel": "Submission Rate (%)"
                }
            }
            
            return {
                'response': response_text,
                'type': 'team',
                'metrics': team_metrics,
                'chartData': chart_data
            }
        
        # Check if asking about high performers (multi-taskers)
        elif 'high performer' in query_lower or 'multi-task' in query_lower:
            high_performers = self.team.get_high_performers(task_threshold=3)
            
            response_text = f"""**High Performers (Multi-Taskers) at Dataplatr:**

You have {len(high_performers)} employees completing more than 3 tasks per day on average:

"""
            
            for i, performer in enumerate(high_performers[:10], 1):  # Show top 10
                response_text += f"""

{i}. **{performer['name']}**
   - Average Tasks Per Day: {performer['avg_tasks_per_day']:.2f}
   - Average Daily Hours: {performer['avg_daily_hours']:.2f}
   - Submission Rate: {performer['submission_rate']}%
"""
            
            response_text += f"""

These employees demonstrate strong multi-tasking capabilities and maintain high productivity levels. The team average is {team_metrics['avg_tasks_per_day']:.2f} tasks per day, making these individuals stand out as particularly efficient contributors."""
            
            chart_data = {
                "chartType": "bar",
                "chartTitle": "High Performers - Average Tasks Per Day",
                "labels": [p['name'] for p in high_performers[:10]],
                "datasets": [
                    {
                        "label": "Average Tasks Per Day",
                        "data": [p['avg_tasks_per_day'] for p in high_performers[:10]],
                        "backgroundColor": "rgba(139, 92, 246, 0.7)",
                        "borderColor": "rgb(139, 92, 246)"
                    }
                ],
                "options": {
                    "xAxisLabel": "Employees",
                    "yAxisLabel": "Tasks Per Day"
                }
            }
            
            return {
                'response': response_text,
                'type': 'team',
                'metrics': {'high_performers': high_performers},
                'chartData': chart_data
            }
        
        # General team insights with LLM
        context = f"""
TEAM OVERVIEW - DATAPLATR:

TEAM SIZE & PERIOD:
- Total Employees: {team_metrics['total_employees']}
- Analysis Period: {team_metrics['date_range']}
- Total Working Days: {team_metrics['total_working_days']}

SUBMISSION DISCIPLINE:
- Consistent Reporters: {team_metrics['consistent_reporters']} employees
- Partial Reporters: {team_metrics['partial_reporters']} employees
- Frequent Defaulters: {team_metrics['frequent_defaulters']} employees
- Employees with Gaps (≥2 days): {team_metrics['employees_with_gaps']}

STATUS BREAKDOWN:
{team_metrics['status_breakdown']}

PRODUCTIVITY METRICS:
- Team Average Submission Rate: {team_metrics['avg_submission_rate']}%
- Team Average Daily Hours: {team_metrics['avg_daily_hours']} hours
- Team Average Tasks Per Day: {team_metrics['avg_tasks_per_day']}
- High Performers (>3 tasks/day): {team_metrics['high_performers']} employees

WORKLOAD DISTRIBUTION:
- Underutilized Days (<8 hrs): {team_metrics['underutilized_percentage']}%
- Overloaded Days (>10 hrs): {team_metrics['overloaded_percentage']}%
"""
        
        prompt = f"""You are a senior HR analytics consultant providing strategic team performance insights to leadership.

TEAM PERFORMANCE DATA:
{context}

LEADERSHIP QUESTION: {query}

INSTRUCTIONS:
- Provide comprehensive, strategic insights about overall team performance
- Identify key trends, patterns, and areas of concern
- Balance positive findings with constructive improvement areas
- Offer actionable recommendations for team management
- Use data to support every claim

5. **CHART DATA STRUCTURE (JSON)**
Generate a JSON object for chart visualization that matches the key insights from your analysis.
The JSON must have this exact structure:
{{
  "chartType": "bar|line|pie|radar|scatter|doughnut",
  "chartTitle": "Descriptive title for the chart",
  "labels": ["Label1", "Label2", ...],
  "datasets": [
    {{
      "label": "Dataset label",
      "data": [value1, value2, ...],
      "backgroundColor": "color or array of colors",
      "borderColor": "border color"
    }}
  ],
  "options": {{
    "xAxisLabel": "X-axis label",
    "yAxisLabel": "Y-axis label"
  }}
}}

- Place the JSON at the END of your response.
- Chart type should be the most appropriate for visualizing the most important team insights.
- Use the actual metric values from the data provided.
"""
        
        try:
            print("Calling Gemini API for team insights...")
            response = self.model.generate_content(prompt)
            response_text = response.candidates[0].content.parts[0].text
            print(f"Got response: {response_text[:100]}...")
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                try:
                    chart_data = json.loads(json_str)
                    text_response = response_text[:json_start].strip()
                except json.JSONDecodeError:
                    print("Failed to parse JSON, using fallback")
                    chart_data = self.generate_fallback_chart(team_metrics, 'team')
                    text_response = response_text
            else:
                # Fallback: Generate simple chart data from team metrics
                chart_data = self.generate_fallback_chart(team_metrics, 'team')
                text_response = response_text
            
            return {
                'response': text_response,
                'type': 'team',
                'metrics': team_metrics,
                'chartData': chart_data
            }
        except Exception as e:
            print(f"ERROR in generate_team_insights: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fallback with chart data
            chart_data = self.generate_fallback_chart(team_metrics, 'team')
            
            # Fallback response with actual data
            fallback = f"""**Team Performance Overview for Dataplatr:**

The team consists of {team_metrics['total_employees']} employees analyzed over {team_metrics['total_working_days']} working days ({team_metrics['date_range']}). The overall team submission rate averages {team_metrics['avg_submission_rate']}%, with employees working an average of {team_metrics['avg_daily_hours']} hours daily and completing approximately {team_metrics['avg_tasks_per_day']} tasks.

**Submission Discipline:**
The team shows {team_metrics['consistent_reporters']} consistent reporters, {team_metrics['partial_reporters']} partial reporters, and {team_metrics['frequent_defaulters']} frequent defaulters. Currently, {team_metrics['employees_with_gaps']} employees have gaps of 2 or more consecutive days without submissions.

**Performance Highlights:**
The team has {team_metrics['high_performers']} high performers completing more than 3 tasks daily. Workload distribution indicates {team_metrics['underutilized_percentage']}% underutilized days and {team_metrics['overloaded_percentage']}% overloaded days, suggesting opportunities for better resource allocation.

**Key Recommendations:**
Focus on improving engagement with the {team_metrics['frequent_defaulters']} frequent defaulters through coaching and support. Recognize and learn from the practices of consistent reporters to improve overall team performance."""
            
            return {
                'response': fallback,
                'type': 'team',
                'metrics': team_metrics,
                'chartData': chart_data
            }
    
    def generate_comparison_insights(self, query, employee_emails):
        print(f"Generating comparison for: {employee_emails}")
        comparison_data = self.individual.get_comparison_metrics(employee_emails)
        
        if len(comparison_data) < 2:
            return {
                'response': "I need at least two valid employees to perform a comparison. Please verify the employee names or emails in your question.",
                'type': 'error'
            }
        
        context = "EMPLOYEE COMPARISON:\n\n"
        
        for metrics in comparison_data:
            context += f"""
Employee: {metrics['name']} ({metrics['email']})
- Status: {metrics['status']}
- Submission Rate: {metrics['submission_rate']}%
- Days Submitted: {metrics['days_submitted']}/{self.base.total_days}
- Max Gap: {metrics['max_gap']} days
- Avg Daily Hours: {metrics['avg_daily_hours']} hrs
- Avg Tasks/Day: {metrics['avg_tasks_per_day']}
- Completion Ratio: {metrics['completion_ratio']}
- Task Diversity: {metrics['task_diversity']}
- Recent Activity (7 days): {metrics['recent_7_days_submissions']} submissions
- Recent Activity (30 days): {metrics['recent_30_days_submissions']} submissions
{'-' * 60}
"""
        
        prompt = f"""You are an HR analytics expert comparing employee performance for management decision-making.

COMPARISON DATA:
{context}

MANAGER'S QUESTION: {query}

INSTRUCTIONS:
- Provide a fair, data-driven comparison of these employees
- Highlight relative strengths and weaknesses
- Identify who excels in which areas
- Note any concerning patterns or impressive achievements
- Offer insights on team dynamics or role suitability
- Maintain objectivity and professionalism

5. **CHART DATA STRUCTURE (JSON)**
Generate a JSON object for chart visualization that compares the key metrics.
The JSON must have this exact structure:
{{
  "chartType": "bar|line|radar",
  "chartTitle": "Descriptive title for the comparison chart",
  "labels": ["Metric1", "Metric2", ...],
  "datasets": [
    {{
      "label": "Employee1 Name",
      "data": [value1, value2, ...],
      "backgroundColor": "color1"
    }},
    {{
      "label": "Employee2 Name",
      "data": [value1, value2, ...],
      "backgroundColor": "color2"
    }}
  ],
  "options": {{
    "xAxisLabel": "Metrics",
    "yAxisLabel": "Values"
  }}
}}

- Place the JSON at the END of your response.
- Use radar chart for multi-dimensional comparison, bar chart for side-by-side metrics.
- Use the actual metric values from the data provided.
"""
        
        try:
            print("Calling Gemini API for comparison...")
            response = self.model.generate_content(prompt)
            response_text = response.candidates[0].content.parts[0].text
            print(f"Got response: {response_text[:100]}...")
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                try:
                    chart_data = json.loads(json_str)
                    text_response = response_text[:json_start].strip()
                except json.JSONDecodeError:
                    print("Failed to parse JSON, using fallback")
                    chart_data = self.generate_fallback_chart(comparison_data, 'comparison')
                    text_response = response_text
            else:
                # Fallback: Generate simple chart data
                chart_data = self.generate_fallback_chart(comparison_data, 'comparison')
                text_response = response_text
            
            return {
                'response': text_response,
                'type': 'comparison',
                'metrics': comparison_data,
                'chartData': chart_data
            }
        except Exception as e:
            print(f"ERROR in generate_comparison_insights: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fallback with chart data
            chart_data = self.generate_fallback_chart(comparison_data, 'comparison')
            
            # Fallback response with actual data
            fallback = f"""**Employee Comparison Summary:**

Comparing {len(comparison_data)} employees based on their performance metrics:

"""
            for metrics in comparison_data:
                fallback += f"\n**{metrics['name']}:** {metrics['submission_rate']}% submission rate, {metrics['avg_tasks_per_day']:.2f} tasks/day, {metrics['avg_daily_hours']:.2f} hrs/day, Status: {metrics['status']}\n"
            
            return {
                'response': fallback,
                'type': 'comparison',
                'metrics': comparison_data,
                'chartData': chart_data
            }
    
    def generate_general_insights(self, query):
        print("Generating general insights...")
        team_metrics = self.team.get_team_overview_metrics()
        
        if not team_metrics:
            return {
                'response': "I'm here to help you analyze employee performance. Please ask about specific employees by name, or ask for team-wide insights.",
                'type': 'general'
            }
        
        context = f"""
AVAILABLE TEAM DATA:
- Total Employees: {team_metrics['total_employees']}
- Analysis Period: {team_metrics['date_range']}
- Consistent Reporters: {team_metrics['consistent_reporters']}
- High Performers: {team_metrics['high_performers']}
- Average Submission Rate: {team_metrics['avg_submission_rate']}%
"""
        
        prompt = f"""You are an employee analytics assistant helping a manager understand their team's performance.

CONTEXT:
{context}

MANAGER'S QUESTION: {query}

INSTRUCTIONS:
- If the question is about a specific employee, politely ask for the employee name or email
- If the question is general, provide helpful insights based on available data
- Suggest specific questions the manager might want to ask
- Be helpful and guide them toward actionable insights
- Keep the tone professional and supportive

5. **CHART DATA STRUCTURE (JSON)**
If appropriate, generate a JSON object for a simple overview chart.
If no chart is needed, use: {{"chartType": "none"}}

RESPONSE:"""
        
        try:
            print("Calling Gemini API for general insights...")
            response = self.model.generate_content(prompt)
            response_text = response.candidates[0].content.parts[0].text
            print(f"Got response: {response_text[:100]}...")
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                try:
                    chart_data = json.loads(json_str)
                    text_response = response_text[:json_start].strip()
                except json.JSONDecodeError:
                    print("Failed to parse JSON, using no chart")
                    chart_data = {"chartType": "none"}
                    text_response = response_text
            else:
                chart_data = {"chartType": "none"}
                text_response = response_text
            
            return {
                'response': text_response,
                'type': 'general',
                'chartData': chart_data
            }
        except Exception as e:
            print(f"ERROR in generate_general_insights: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                'response': f"""I'm here to help you analyze employee performance data for your team of {team_metrics['total_employees']} employees.

You can ask me about:
- Specific employees by name (e.g., "How is John performing?")
- Team-wide metrics (e.g., "Show me overall team performance")
- Comparisons (e.g., "Compare Alice and Bob")
- Top performers or employees needing attention

What would you like to know?""",
                'type': 'general',
                'chartData': {"chartType": "none"}
            }
    
    def generate_fallback_chart(self, metrics, insight_type):
        """Generate fallback chart data when LLM fails"""
        if insight_type == 'individual':
            return {
                "chartType": "bar",
                "chartTitle": f"Performance Overview - {metrics['name']}",
                "labels": ["Submission Rate", "Avg Daily Hours", "Avg Tasks/Day", "Completion Ratio"],
                "datasets": [
                    {
                        "label": "Metrics",
                        "data": [
                            metrics['submission_rate'],
                            metrics['avg_daily_hours'],
                            metrics['avg_tasks_per_day'],
                            metrics['completion_ratio'] * 100 if metrics['completion_ratio'] else 0
                        ],
                        "backgroundColor": "rgba(59, 130, 246, 0.7)",
                        "borderColor": "rgb(59, 130, 246)"
                    }
                ],
                "options": {
                    "xAxisLabel": "Metrics",
                    "yAxisLabel": "Values"
                }
            }
        elif insight_type == 'team':
            # Use actual status breakdown data if available
            if 'status_breakdown' in metrics:
                status_data = metrics['status_breakdown']
                return {
                    "chartType": "doughnut",
                    "chartTitle": "Team Performance Status Distribution",
                    "labels": list(status_data.keys()),
                    "datasets": [
                        {
                            "label": "Number of Employees",
                            "data": list(status_data.values()),
                            "backgroundColor": ["#10B981", "#3B82F6", "#F59E0B", "#EF4444", "#8B5CF6", "#6B7280"],
                            "borderColor": "#FFFFFF"
                        }
                    ],
                    "options": {
                        "xAxisLabel": "",
                        "yAxisLabel": ""
                    }
                }
            else:
                return {
                    "chartType": "bar",
                    "chartTitle": "Team Overview",
                    "labels": ["Consistent", "Partial", "Frequent Defaulters", "High Performers"],
                    "datasets": [
                        {
                            "label": "Count",
                            "data": [
                                metrics.get('consistent_reporters', 0),
                                metrics.get('partial_reporters', 0),
                                metrics.get('frequent_defaulters', 0),
                                metrics.get('high_performers', 0)
                            ],
                            "backgroundColor": "rgba(139, 92, 246, 0.7)",
                            "borderColor": "rgb(139, 92, 246)"
                        }
                    ],
                    "options": {
                        "xAxisLabel": "Categories",
                        "yAxisLabel": "Number of Employees"
                    }
                }
        elif insight_type == 'comparison':
            # Create comparison chart from multiple employees
            if isinstance(metrics, list) and len(metrics) >= 2:
                chart_data = {
                    "chartType": "bar",
                    "chartTitle": "Employee Comparison - Key Metrics",
                    "labels": ["Submission Rate", "Avg Daily Hours", "Avg Tasks/Day"],
                    "datasets": []
                }
                
                colors = ["rgba(59, 130, 246, 0.7)", "rgba(239, 68, 68, 0.7)", "rgba(34, 197, 94, 0.7)", 
                         "rgba(245, 158, 11, 0.7)", "rgba(139, 92, 246, 0.7)"]
                
                for i, employee in enumerate(metrics[:5]):  # Max 5 employees for clarity
                    chart_data["datasets"].append({
                        "label": employee['name'],
                        "data": [
                            employee['submission_rate'],
                            employee['avg_daily_hours'],
                            employee['avg_tasks_per_day']
                        ],
                        "backgroundColor": colors[i % len(colors)],
                        "borderColor": colors[i % len(colors)].replace('0.7', '1')
                    })
                
                chart_data["options"] = {
                    "xAxisLabel": "Metrics",
                    "yAxisLabel": "Values"
                }
                return chart_data
        
        # Default fallback
        return {
            "chartType": "bar",
            "chartTitle": "Performance Overview",
            "labels": ["Metric 1", "Metric 2", "Metric 3"],
            "datasets": [
                {
                    "label": "Values",
                    "data": [1, 2, 3],
                    "backgroundColor": "rgba(59, 130, 246, 0.7)",
                    "borderColor": "rgb(59, 130, 246)"
                }
            ],
            "options": {
                "xAxisLabel": "Metrics",
                "yAxisLabel": "Values"
            }
        }





