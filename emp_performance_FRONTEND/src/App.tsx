
// src/App.tsx 
import { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import SmartSearchFilters, { FilterOptions } from './components/SmartSearchFilters';
import InvoiceModal from './components/InvoiceModal';
import { Employee, EmployeeSummary, Message } from './types';

const API_BASE_URL = 'http://localhost:5000';
// const API_BASE_URL = 'https://employee-tracker-api-313726293085.us-central1.run.app';

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [summary, setSummary] = useState<EmployeeSummary>({
    total_employees: 0,
    submitted_today: 0,
    not_submitted_today: 0
  });
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: `Hello! I'm your Employee Analytics Assistant powered by advanced AI.

I can help you with:
- Individual employee performance analysis
- Team-wide productivity insights
- Employee comparisons
- Submission patterns and trends
- Workload distribution analysis
- Project billing analysis (Lyell & DataPlatr)
- SOW compliance checking

Use the smart search bar above to search employees, apply filters, or ask any questions!`,
      sender: 'bot',
      timestamp: new Date(),
      comprehensiveCharts: undefined
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentFilters, setCurrentFilters] = useState<FilterOptions | null>(null);
  const [isInvoiceModalOpen, setIsInvoiceModalOpen] = useState(false);

  useEffect(() => {
    fetchEmployees();
    fetchSummary();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/employees`);
      const data = await response.json();
      setEmployees(data);
    } catch (error) {
      console.error('Error fetching employees:', error);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/employee-summary`);
      const data = await response.json();
      setSummary(data);
    } catch (error) {
      console.error('Error fetching summary:', error);
    }
  };

  const handleSendMessage = async (text: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text: text,
      sender: 'user',
      timestamp: new Date(),
      comprehensiveCharts: undefined
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: text })
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response || 'I apologize, but I encountered an error processing your request.',
        sender: 'bot',
        timestamp: new Date(),
        chartData: data.chartData || { chartType: 'none' },
        comprehensiveCharts: data.comprehensiveCharts,
        invoice_metadata: data.invoice_metadata
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an error. Please make sure the backend server is running and try again.',
        sender: 'bot',
        timestamp: new Date(),
        comprehensiveCharts: undefined
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmployeeClick = (employee: Employee) => {
    handleSendMessage(`Tell me about ${employee.name}'s performance`);
  };

  // Handler for smart search
  const handleSmartSearch = (query: string) => {
    console.log('Smart search query:', query);
    handleSendMessage(query);
  };

  // Handler for filter application
  const handleFiltersApply = (filters: FilterOptions) => {
    console.log('Filters applied:', filters);
    setCurrentFilters(filters);
    // The SmartSearchFilters component automatically generates and sends the query
  };

  return (
    <div className="h-screen flex flex-col bg-slate-50 font-sans text-slate-900">
      {/* Header */}
      <Header
        onMenuClick={() => setIsSidebarOpen(!isSidebarOpen)}
        onInvoiceClick={() => setIsInvoiceModalOpen(true)}
      />

      <div className="flex flex-1 overflow-hidden relative">
        {/* Sidebar */}
        <Sidebar
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          employees={employees}
          summary={summary}
          onEmployeeClick={handleEmployeeClick}
        />

        {/* Main Content - Full Height Chat */}
        <main className="flex-1 flex flex-col overflow-hidden w-full transition-all duration-300 ease-in-out">
          <div className="flex-1 flex flex-col h-full overflow-hidden p-4 md:p-6 lg:p-8 max-w-[1600px] mx-auto w-full">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 flex-1 overflow-hidden flex flex-col bg-opacity-80 backdrop-blur-sm">
              <ChatInterface
                messages={messages}
                onSendMessage={handleSendMessage}
                isLoading={isLoading}
                apiBaseUrl={API_BASE_URL}
              />
            </div>

            <div className="mt-2 text-center text-xs text-slate-400">
              AI-powered analytics • Internal Use Only
            </div>
          </div>
        </main>
      </div>

      {/* Invoice Modal */}
      <InvoiceModal
        isOpen={isInvoiceModalOpen}
        onClose={() => setIsInvoiceModalOpen(false)}
        apiBaseUrl={API_BASE_URL}
      />
    </div>
  );
}

export default App;
