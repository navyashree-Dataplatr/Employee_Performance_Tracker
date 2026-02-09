import datetime
import pandas as pd
import re
from datetime import date
from google_sheet_connector import SimpleGoogleSheetConnector  # Updated import

class BaseDataProcessor:
    def __init__(self, employees_csv, google_sheet_url=None):
        self.employees_csv = employees_csv
        self.google_sheet_url = google_sheet_url
        self.load_data()
    
    def load_data(self):
        print("Loading employee data...")
        emp_df = pd.read_csv(self.employees_csv)
        emp_df.columns = ['Name_Email', 'Mobile_Number', 'Emergency_Contact_Number', 'Emergency_Contact_Name']
        
        emails_list = []
        names = []
        
        for text in emp_df['Name_Email']:
            if pd.isna(text):
                emails_list.append([])
                names.append(None)
                continue
            
            text_str = str(text)
            emails_in_entry = []
            
            bracket_emails = re.findall(r'<([^>]+)>', text_str)
            emails_in_entry.extend([e.lower().strip() for e in bracket_emails])
            
            text_without_brackets = re.sub(r'<[^>]+>', '', text_str)
            plain_emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text_without_brackets)
            emails_in_entry.extend([e.lower().strip() for e in plain_emails])
            
            seen = set()
            unique_emails = []
            for email in emails_in_entry:
                if email not in seen:
                    seen.add(email)
                    unique_emails.append(email)
            
            emails_list.append(unique_emails)
            name = text_str.split('<')[0].split('@')[0].strip().rstrip(', ').strip()
            names.append(name)
        
        emp_df['Emails'] = emails_list
        emp_df['Name'] = names
        emp_df = emp_df[emp_df['Emails'].apply(len) > 0]
        emp_df['Email'] = emp_df['Emails'].apply(lambda x: x[0] if x else None)
        
        self.master_df = emp_df[['Name', 'Email', 'Emails', 'Mobile_Number']]
        print(f"Loaded {len(self.master_df)} employees")
        
        print("Loading work reports from Google Sheet...")
        
        if self.google_sheet_url:
            # Use Google Sheet with connector
            try:
                connector = SimpleGoogleSheetConnector(self.google_sheet_url)
                
                
                work_df = connector.get_work_reports(gid='1012493901')
                
                if work_df.empty:
                    print("Warning: No data found in Google Sheet. Using empty DataFrame.")
                    work_df = pd.DataFrame(columns=['Timestamp', 'Email Address', 'Enter your name', 
                                                     'Select the date', 'Tasks Completed', 'Time Spent'])
                else:
                    print(f"Successfully loaded {len(work_df)} work reports from Google Sheet")
                    
            except Exception as e:
                print(f"Error loading from Google Sheet: {str(e)}")
                print("Falling back to empty DataFrame")
                work_df = pd.DataFrame(columns=['Timestamp', 'Email Address', 'Enter your name', 
                                                 'Select the date', 'Tasks Completed', 'Time Spent'])
        else:
            # Fallback to empty DataFrame
            work_df = pd.DataFrame(columns=['Timestamp', 'Email Address', 'Enter your name', 
                                             'Select the date', 'Tasks Completed', 'Time Spent'])
        
        
        
        column_mapping = {
            'Timestamp': 'Timestamp',
            'Email Address': 'Email_Address',
            'Enter your name': 'Name',
            'Select the date': 'Date',
            'Tasks Completed': 'Tasks_Completed',
            'Time Spent': 'Time_Spent'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in work_df.columns:
                work_df = work_df.rename(columns={old_col: new_col})
        
        # Ensure all required columns exist
        required_columns = ['Timestamp', 'Email_Address', 'Name', 'Date', 'Tasks_Completed', 'Time_Spent']
        for col in required_columns:
            if col not in work_df.columns:
                work_df[col] = ''
        
        # Clean and process the data (same as before)
        work_df['email'] = work_df['Email_Address'].astype(str).str.lower().str.strip()
        work_df = work_df.dropna(subset=['email'])
        
        # Parse dates
        parsed_dates = []
        for date_str in work_df['Date']:
            if pd.isna(date_str):
                parsed_dates.append(pd.NaT)
                continue
            date_str = str(date_str).strip()
            # Try multiple date formats
            for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y']:
                try:
                    parsed = datetime.strptime(date_str, fmt)
                    parsed_dates.append(parsed)
                    break
                except:
                    continue
            else:
                # Use pandas as fallback
                parsed = pd.to_datetime(date_str, errors='coerce')
                parsed_dates.append(parsed)
        
        work_df['clean_date'] = parsed_dates
        work_df = work_df.dropna(subset=['clean_date'])
        
        today = date.today()
        work_df = work_df[work_df['clean_date'].dt.date <= today]
        
        work_df['Hours'] = work_df['Time_Spent'].apply(self.parse_hours)
        work_df['task_count'] = work_df['Tasks_Completed'].apply(self.count_tasks)
        
        self.work_df = work_df
        print(f"Loaded {len(self.work_df)} work reports total")
        
        self.email_to_employee = {}
        self.employee_all_emails = {}
        
        for idx, row in self.master_df.iterrows():
            primary_email = row['Email']
            all_emails = row['Emails'].copy()
            self.employee_all_emails[primary_email] = all_emails
            
            for email in all_emails:
                self.email_to_employee[email] = primary_email
        
        self.calculate_submissions()
        print("Data loading complete!")
    
    def calculate_submissions(self):
        unique_dates = self.work_df['clean_date'].dt.date.unique()
        unique_dates.sort()
        
        if len(unique_dates) > 0:
            self.working_days_set = set(unique_dates)
            self.total_days = len(unique_dates)
            self.min_date = min(unique_dates)
            self.max_date = max(unique_dates)
        else:
            self.working_days_set = set()
            self.total_days = 0
            self.min_date = None
            self.max_date = None
        
        self.submissions = {}
        for primary_email in self.employee_all_emails.keys():
            submitted_dates = set()
            
            for email_variant in self.employee_all_emails[primary_email]:
                employee_reports = self.work_df[self.work_df['email'] == email_variant]
                submitted_dates.update(d.date() for d in employee_reports['clean_date'])
            
            self.submissions[primary_email] = submitted_dates
    
    def parse_hours(self, text):
        if pd.isna(text):
            return 0
        text = str(text).lower()
        hrs = sum(map(float, re.findall(r'(\d+(?:\.\d+)?)\s*hr', text)))
        mins = sum(map(float, re.findall(r'(\d+(?:\.\d+)?)\s*min', text)))
        if hrs == 0 and mins == 0:
            nums = re.findall(r'(\d+(?:\.\d+)?)', text)
            if nums:
                hrs = float(nums[0])
        return hrs + mins/60
    
    def count_tasks(self, task_text):
        if pd.isna(task_text):
            return 0
        
        task_text = str(task_text).strip()
        if not task_text:
            return 0
        
        count = 0
        numbered_tasks = len([line for line in task_text.split('\n')
                             if re.match(r'^\d+\.', line.strip())])
        if numbered_tasks > 0:
            count = numbered_tasks
        else:
            lines = task_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('-') and not line.startswith(':'):
                    comma_count = line.count(',')
                    if comma_count > 0 and len(line) > 20:
                        count += comma_count + 1
                    else:
                        count += 1
        
        return max(1, count)
    
    def find_employee_by_name(self, name_query):
        """Find employee email by partial name match"""
        name_query = name_query.lower().strip()
        
        for idx, row in self.master_df.iterrows():
            employee_name = row['Name'].lower()
            if name_query in employee_name or employee_name in name_query:
                return row['Email']
        
        return None
    
    def get_employees_list(self):
        employees = []
        for idx, row in self.master_df.iterrows():
            employees.append({
                'id': idx,
                'name': row['Name'],
                'email': row['Email']
            })
        return employees
    
    def get_employee_summary(self):
        today = date.today()
        
        total_employees = len(self.master_df)
        
        submitted_today = 0
        for primary_email in self.employee_all_emails.keys():
            if today in self.submissions.get(primary_email, set()):
                submitted_today += 1
        
        not_submitted_today = total_employees - submitted_today
        
        return {
            'total_employees': total_employees,
            'submitted_today': submitted_today,
            'not_submitted_today': not_submitted_today
        }






























