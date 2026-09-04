import React, { useState } from 'react';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Button } from '../../../shared/components/Button';
import { Input } from '../../../shared/components/Input';

export const AshaCheckin: React.FC = () => {
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([]);
  const [severity, setSeverity] = useState(5);
  const [loading, setLoading] = useState(false);

  const allSymptoms = [
    'fever', 'headache', 'cough', 'breathing_difficulty',
    'chest_pain', 'vomiting', 'diarrhea', 'abdominal_pain',
    'rash', 'fatigue', 'dizziness', 'confusion'
  ];

  const toggleSymptom = (symptom: string) => {
    setSelectedSymptoms(prev =>
      prev.includes(symptom)
        ? prev.filter(s => s !== symptom)
        : [...prev, symptom]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await fetch('/api/v1/checkins', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          method: 'in_person',
          input_type: 'text',
          responses: {
            symptoms: selectedSymptoms,
            severity,
          },
        }),
      });
      setLoading(false);
      // Reset form or navigate
      setSelectedSymptoms([]);
      setSeverity(5);
    } catch (error) {
      console.error('Error creating check-in:', error);
      setLoading(false);
    }
  };

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">Create Check-in</h1>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-medium">Symptoms</h2>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2">
            {allSymptoms.map((symptom) => (
              <button
                key={symptom}
                type="button"
                onClick={() => toggleSymptom(symptom)}
                className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                  selectedSymptoms.includes(symptom)
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {symptom.replace('_', ' ')}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-medium">Severity (0-10)</h2>
        </CardHeader>
        <CardContent>
          <Input
            type="range"
            min="0"
            max="10"
            value={severity}
            onChange={(e) => setSeverity(Number(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between mt-2">
            <span className="text-sm text-gray-500">0 (None)</span>
            <span className="text-lg font-medium">{severity}/10</span>
            <span className="text-sm text-gray-500">10 (Severe)</span>
          </div>
        </CardContent>
      </Card>

      <Button
        onClick={handleSubmit}
        disabled={selectedSymptoms.length === 0 || loading}
        className="w-full"
      >
        {loading ? 'Creating Check-in...' : 'Submit Check-in'}
      </Button>
    </div>
  );
};
