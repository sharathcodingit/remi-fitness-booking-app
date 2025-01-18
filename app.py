import React, { useState } from 'react';
import { Calendar, Clock } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

const SessionCalendar = () => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedTime, setSelectedTime] = useState('');
  const [selectedClient, setSelectedClient] = useState('');

  // Mock data - replace with your actual data
  const clients = [
    { id: 1, name: 'John Doe', sessionsRemaining: 5 },
    { id: 2, name: 'Jane Smith', sessionsRemaining: 3 },
  ];

  // Generate available time slots (9 AM to 5 PM)
  const timeSlots = Array.from({ length: 9 }, (_, i) => {
    const hour = i + 9;
    return `${hour.toString().padStart(2, '0')}:00`;
  });

  // Get dates for the current week
  const getDatesForWeek = () => {
    const dates = [];
    const curr = new Date();
    const first = curr.getDate() - curr.getDay();
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(curr.setDate(first + i));
      dates.push(date);
    }
    return dates;
  };

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Session Booking Calendar
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Client Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Select Client</label>
          <select 
            className="w-full p-2 border rounded-md"
            value={selectedClient}
            onChange={(e) => setSelectedClient(e.target.value)}
          >
            <option value="">Select a client...</option>
            {clients.map(client => (
              <option key={client.id} value={client.id}>
                {client.name} ({client.sessionsRemaining} sessions remaining)
              </option>
            ))}
          </select>
        </div>

        {/* Weekly Calendar */}
        <div className="grid grid-cols-7 gap-2 mb-6">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <div key={day} className="text-center font-medium p-2 bg-gray-100 rounded">
              {day}
            </div>
          ))}
          {getDatesForWeek().map((date, index) => (
            <button
              key={index}
              onClick={() => setSelectedDate(date)}
              className={`p-2 text-center rounded hover:bg-blue-50 ${
                selectedDate.toDateString() === date.toDateString() 
                  ? 'bg-blue-100 font-medium' 
                  : ''
              }`}
            >
              {date.getDate()}
            </button>
          ))}
        </div>

        {/* Time Slots */}
        <div className="mb-6">
          <h3 className="flex items-center gap-2 mb-3 font-medium">
            <Clock className="h-4 w-4" />
            Available Time Slots
          </h3>
          <div className="grid grid-cols-3 gap-2">
            {timeSlots.map(time => (
              <button
                key={time}
                onClick={() => setSelectedTime(time)}
                className={`p-2 text-center rounded border ${
                  selectedTime === time 
                    ? 'bg-blue-100 border-blue-300' 
                    : 'hover:bg-gray-50'
                }`}
              >
                {time}
              </button>
            ))}
          </div>
        </div>

        {/* Booking Summary */}
        {selectedClient && selectedDate && selectedTime && (
          <Alert>
            <AlertDescription>
              Selected booking: {selectedDate.toLocaleDateString()} at {selectedTime}
            </AlertDescription>
          </Alert>
        )}

        {/* Book Button */}
        <button
          className={`w-full p-3 rounded-md text-white mt-4 ${
            selectedClient && selectedDate && selectedTime
              ? 'bg-blue-600 hover:bg-blue-700'
              : 'bg-gray-300 cursor-not-allowed'
          }`}
          disabled={!selectedClient || !selectedDate || !selectedTime}
        >
          Book Session
        </button>
      </CardContent>
    </Card>
  );
};

export default SessionCalendar;