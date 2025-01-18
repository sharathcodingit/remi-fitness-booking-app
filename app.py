// App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Calendar, Users, DollarSign, Clock } from 'lucide-react';

// Client Management Component
function ClientManagement() {
  const [clients, setClients] = useState([]);
  const [newClient, setNewClient] = useState({
    name: '',
    email: '',
    totalSessions: 12,
    sessionsRemaining: 12,
    sessionsCompleted: 0,
    bookedSessions: []
  });

  const handleAddClient = (e) => {
    e.preventDefault();
    setClients([...clients, { ...newClient, id: Date.now() }]);
    setNewClient({
      name: '',
      email: '',
      totalSessions: 12,
      sessionsRemaining: 12,
      sessionsCompleted: 0,
      bookedSessions: []
    });
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Client Management</h2>
      
      {/* Add Client Form */}
      <form onSubmit={handleAddClient} className="mb-8">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Client Name</label>
            <input
              type="text"
              value={newClient.name}
              onChange={(e) => setNewClient({ ...newClient, name: e.target.value })}
              className="w-full p-2 border rounded"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={newClient.email}
              onChange={(e) => setNewClient({ ...newClient, email: e.target.value })}
              className="w-full p-2 border rounded"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Total Sessions</label>
            <input
              type="number"
              value={newClient.totalSessions}
              onChange={(e) => setNewClient({ ...newClient, totalSessions: parseInt(e.target.value) })}
              className="w-full p-2 border rounded"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700"
          >
            Add Client
          </button>
        </div>
      </form>

      {/* Client List */}
      <div className="space-y-4">
        {clients.map(client => (
          <div key={client.id} className="border p-4 rounded">
            <h3 className="font-bold">{client.name}</h3>
            <p className="text-gray-600">{client.email}</p>
            <div className="mt-2">
              <span className="text-sm">
                Sessions: {client.sessionsCompleted}/{client.totalSessions}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Calendar Component
function SessionCalendar() {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedTime, setSelectedTime] = useState('');
  const [selectedClient, setSelectedClient] = useState('');
  const [bookings, setBookings] = useState([]);

  // Generate time slots (9 AM to 5 PM)
  const timeSlots = Array.from({ length: 9 }, (_, i) => {
    const hour = i + 9;
    return `${hour.toString().padStart(2, '0')}:00`;
  });

  const handleBooking = () => {
    if (selectedClient && selectedDate && selectedTime) {
      const newBooking = {
        id: Date.now(),
        clientId: selectedClient,
        date: selectedDate,
        time: selectedTime
      };
      setBookings([...bookings, newBooking]);
      // Reset selection
      setSelectedTime('');
      setSelectedClient('');
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Session Calendar</h2>
      
      <div className="grid grid-cols-7 gap-2 mb-6">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
          <div key={day} className="text-center font-medium p-2 bg-gray-100">
            {day}
          </div>
        ))}
        {/* Calendar days would be generated here */}
      </div>

      <div className="mt-6">
        <h3 className="font-bold mb-2">Available Time Slots</h3>
        <div className="grid grid-cols-3 gap-2">
          {timeSlots.map(time => (
            <button
              key={time}
              onClick={() => setSelectedTime(time)}
              className={`p-2 border rounded ${
                selectedTime === time ? 'bg-blue-100' : ''
              }`}
            >
              {time}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={handleBooking}
        className="mt-6 w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700"
        disabled={!selectedClient || !selectedTime}
      >
        Book Session
      </button>
    </div>
  );
}

// Payment Tracking Component
function PaymentTracking() {
  const [payments, setPayments] = useState([]);

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Payment Tracking</h2>
      
      <div className="space-y-4">
        {payments.map(payment => (
          <div key={payment.id} className="border p-4 rounded">
            <div className="flex justify-between">
              <div>
                <h3 className="font-bold">{payment.clientName}</h3>
                <p className="text-sm text-gray-600">
                  Sessions: {payment.sessions}
                </p>
              </div>
              <div className="text-right">
                <p className="font-bold">${payment.amount}</p>
                <p className="text-sm text-gray-600">{payment.date}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Main Navigation Component
function Navigation() {
  return (
    <nav className="bg-gray-800 text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link to="/" className="text-xl font-bold">
          Fitness Trainer
        </Link>
        <div className="space-x-4">
          <Link to="/clients" className="hover:text-gray-300">
            <Users className="inline-block mr-1" size={18} />
            Clients
          </Link>
          <Link to="/calendar" className="hover:text-gray-300">
            <Calendar className="inline-block mr-1" size={18} />
            Calendar
          </Link>
          <Link to="/payments" className="hover:text-gray-300">
            <DollarSign className="inline-block mr-1" size={18} />
            Payments
          </Link>
        </div>
      </div>
    </nav>
  );
}

// Main App Component
function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <Navigation />
        <main className="container mx-auto py-6">
          <Routes>
            <Route path="/clients" element={<ClientManagement />} />
            <Route path="/calendar" element={<SessionCalendar />} />
            <Route path="/payments" element={<PaymentTracking />} />
            <Route path="/" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

// Dashboard Component
function Dashboard() {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Today's Sessions</h2>
          {/* Today's sessions would be listed here */}
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Recent Clients</h2>
          {/* Recent clients would be listed here */}
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Payment Reminders</h2>
          {/* Payment reminders would be listed here */}
        </div>
      </div>
    </div>
  );
}

export default App;

// index.js
import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import './index.css';

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);

// index.css
@tailwind base;
@tailwind components;
@tailwind utilities;