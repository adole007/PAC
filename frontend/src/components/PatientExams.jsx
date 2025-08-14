import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { Search, Eye, Calendar, User as UserIcon } from 'lucide-react';

// Get API URL function - uses the same logic as main App.js
const getApiUrl = () => {
  // Use the global API URL that's set in the main App.js
  if (window.PAC_DEBUG && window.PAC_DEBUG.getApiUrl) {
    return window.PAC_DEBUG.getApiUrl();
  }
  // Fallback logic
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  if (isLocal) {
    return 'http://localhost:8000/api';
  }
  return 'https://pac-ik6nachlb-adole007s-projects.vercel.app/api';
};

const PatientExams = () => {
  const [patients, setPatients] = useState([]);
  const [patientImageCounts, setPatientImageCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const response = await axios.get(`${getApiUrl()}/patients`);
        setPatients(response.data);
        // Get image counts for each patient
        await fetchPatientImageCounts(response.data);
      } catch (error) {
        toast.error('Failed to fetch patients');
      } finally {
        setLoading(false);
      }
    };
    fetchPatients();
  }, []);

  const fetchPatientImageCounts = async (patientList) => {
    const counts = {};
    try {
      for (const patient of patientList) {
        try {
          const response = await axios.get(`${getApiUrl()}/patients/${patient.id}/images`);
          counts[patient.id] = response.data.length;
        } catch (error) {
          counts[patient.id] = 0;
        }
      }
      setPatientImageCounts(counts);
    } catch (error) {
      console.error('Failed to fetch patient image counts:', error);
    }
  };

  if (loading) {
    return <div>Loading exams...</div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold mb-4">Patient Exams</h2>
      <table className="min-w-full bg-white">
        <thead>
          <tr>
            <th className="py-2">Patient ID</th>
            <th className="py-2">Name</th>
            <th className="py-2">Date of Birth</th>
            <th className="py-2">Images Count</th>
            <th className="py-2">Clinician</th>
          </tr>
        </thead>
        <tbody>
          {patients.map(patient => (
            <tr key={patient.id}>
              <td className="border px-4 py-2">{patient.patient_id}</td>
              <td className="border px-4 py-2">{patient.first_name} {patient.last_name}</td>
              <td className="border px-4 py-2">{patient.date_of_birth}</td>
              <td className="border px-4 py-2">{patientImageCounts[patient.id] || 0}</td>
              <td className="border px-4 py-2">{patient.primary_physician}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PatientExams;

