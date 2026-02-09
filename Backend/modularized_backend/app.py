# from flask import Flask, jsonify, request
# from flask_cors import CORS
# from data_processor import DataProcessor

# app = Flask(__name__)
# CORS(app)

# # Initialize data processor
# data_processor = DataProcessor(
#     employees_csv=r'E:\poc projects\Employee_Performance_Tracker_App\Backend\Dataplatr_employees.csv',
#     work_reports_csv=r'E:\poc projects\Employee_Performance_Tracker_App\Backend\Daily_work_status_report.csv'
# )


from flask import Flask, jsonify, request
from flask_cors import CORS
from data_processor import DataProcessor

app = Flask(__name__)
CORS(app)

# Initialize data processor with Google Sheet URL
data_processor = DataProcessor(
    employees_csv=r'E:\poc projects\Employee_Performance_Tracker_App\Backend\Dataplatr_employees.csv',
    google_sheet_url='https://docs.google.com/spreadsheets/d/1ZUhkf7B5dU1-mfQOyTGRetS_GCo9lsqoXeq2KEq2bC4/edit?gid=1012493901#gid=1012493901'
)



@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/employees', methods=['GET'])
def get_employees():
    employees = data_processor.get_employees_list()
    return jsonify(employees)

@app.route('/employee-summary', methods=['GET'])
def get_employee_summary():
    summary = data_processor.get_employee_summary()
    return jsonify(summary)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    response = data_processor.process_query(query)
    return jsonify(response)

@app.route('/chart-data', methods=['GET'])
def get_chart_data():
    chart_data = data_processor.get_chart_data()
    if chart_data:
        return jsonify(chart_data)
    else:
        return jsonify({"error": "Unable to fetch chart data"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)



