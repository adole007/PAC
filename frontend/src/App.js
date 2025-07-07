import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';
import { 
  User, 
  Users, 
  Upload, 
  Eye, 
  Settings, 
  LogOut, 
  Plus, 
  Edit, 
  Trash2, 
  Search,
  Image as ImageIcon,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Maximize,
  Download,
  Ruler,
  Move,
  MousePointer,
  Moon,
  Sun
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Theme Context
const ThemeContext = React.createContext();

const ThemeProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(true); // Default to dark mode

  useEffect(() => {
    const savedTheme = localStorage.getItem('pac-theme');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);
    localStorage.setItem('pac-theme', newTheme ? 'dark' : 'light');
  };

  const value = {
    isDarkMode,
    toggleTheme
  };

  return (
    <ThemeContext.Provider value={value}>
      <div className={isDarkMode ? 'dark-theme' : 'light-theme'}>
        {children}
      </div>
    </ThemeContext.Provider>
  );
};

const useTheme = () => {
  return React.useContext(ThemeContext);
};

// Authentication Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { username, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      
      toast.success('Login successful!');
      return true;
    } catch (error) {
      toast.error('Login failed. Please check your credentials.');
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    toast.info('Logged out successfully');
  };

  const value = {
    user,
    login,
    logout,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  return React.useContext(AuthContext);
};

// Login Component
const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const { isDarkMode } = useTheme();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    const success = await login(username, password);
    if (!success) {
      setIsLoading(false);
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center p-4 ${
      isDarkMode 
        ? 'bg-slate-900' 
        : 'bg-gradient-to-br from-blue-50 to-indigo-100'
    }`}>
      <div className={`rounded-xl shadow-2xl p-8 w-full max-w-md ${
        isDarkMode 
          ? 'bg-slate-800 border border-slate-700' 
          : 'bg-white'
      }`}>
        <div className="text-center mb-8">
          <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 ${
            isDarkMode ? 'bg-blue-600' : 'bg-blue-100'
          }`}>
            <User className={`w-8 h-8 ${isDarkMode ? 'text-white' : 'text-blue-600'}`} />
          </div>
          <h1 className={`text-3xl font-bold mb-2 ${
            isDarkMode ? 'text-slate-100' : 'text-gray-800'
          }`}>JAJUWA HEALTHCARE PAC System</h1>
          <p className={isDarkMode ? 'text-slate-400' : 'text-gray-600'}>
            Medical Image Management Platform
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              isDarkMode ? 'text-slate-300' : 'text-gray-700'
            }`}>
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={`w-full px-4 py-3 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                isDarkMode 
                  ? 'bg-slate-700 border border-slate-600 text-slate-100 placeholder-slate-400' 
                  : 'bg-white border border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
              placeholder="Enter your username"
              required
            />
          </div>
          
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              isDarkMode ? 'text-slate-300' : 'text-gray-700'
            }`}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={`w-full px-4 py-3 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                isDarkMode 
                  ? 'bg-slate-700 border border-slate-600 text-slate-100 placeholder-slate-400' 
                  : 'bg-white border border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
              placeholder="Enter your password"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className={`w-full py-3 px-4 rounded-lg font-medium transition-colors focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed ${
              isDarkMode 
                ? 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-offset-slate-800' 
                : 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-offset-2'
            }`}
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <p className={`text-sm ${isDarkMode ? 'text-slate-400' : 'text-gray-600'}`}>
            Demo Credentials: admin/password
          </p>
        </div>
      </div>
    </div>
  );
};

// Dashboard Layout
const DashboardLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const { isDarkMode, toggleTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('patients');

  const navigation = [
    { id: 'patients', label: 'Patients', icon: Users },
    { id: 'viewer', label: 'Image Viewer', icon: Eye },
    { id: 'upload', label: 'Upload Images', icon: Upload },
    ...(user?.role === 'admin' ? [{ id: 'settings', label: 'Settings', icon: Settings }] : [])
  ];

  return (
    <div className={`min-h-screen ${isDarkMode ? 'bg-slate-900' : 'bg-gray-50'}`}>
      <div className={`shadow-sm border-b ${
        isDarkMode 
          ? 'bg-slate-800 border-slate-700' 
          : 'bg-white border-gray-200'
      }`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <User className="w-5 h-5 text-white" />
                </div>
                <span className={`text-xl font-bold ${
                  isDarkMode ? 'text-slate-100' : 'text-gray-800'
                }`}>JAJUWA HEALTHCARE PAC System</span>
              </div>
              
              <nav className="hidden md:flex space-x-1">
                {navigation.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-2 ${
                      activeTab === item.id
                        ? 'bg-blue-600 text-white'
                        : isDarkMode
                          ? 'text-slate-300 hover:bg-slate-700 hover:text-slate-100'
                          : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <item.icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </button>
                ))}
              </nav>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Theme Toggle Button */}
              <button
                onClick={toggleTheme}
                className={`p-2 rounded-lg transition-colors ${
                  isDarkMode
                    ? 'bg-slate-700 hover:bg-slate-600 text-slate-300'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
                }`}
                title={`Switch to ${isDarkMode ? 'light' : 'dark'} theme`}
              >
                {isDarkMode ? (
                  <Sun className="w-5 h-5" />
                ) : (
                  <Moon className="w-5 h-5" />
                )}
              </button>
              
              <div className={`text-sm ${
                isDarkMode ? 'text-slate-300' : 'text-gray-600'
              }`}>
                <span className={`font-medium ${
                  isDarkMode ? 'text-slate-100' : 'text-gray-900'
                }`}>{user?.full_name}</span>
                <span className={isDarkMode ? 'text-slate-400' : 'text-gray-400'}>
                  {' '}({user?.role})
                </span>
              </div>
              <button
                onClick={logout}
                className={`flex items-center space-x-1 transition-colors ${
                  isDarkMode
                    ? 'text-slate-400 hover:text-red-400'
                    : 'text-gray-600 hover:text-red-600'
                }`}
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {React.cloneElement(children, { activeTab, setActiveTab })}
      </div>
    </div>
  );
};

// Patient Management Component
const PatientManagement = () => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingPatient, setEditingPatient] = useState(null);
  const [formData, setFormData] = useState({
    patient_id: '',
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: '',
    phone: '',
    email: '',
    address: '',
    medical_record_number: '',
    primary_physician: '',
    allergies: [],
    medications: [],
    medical_history: [],
    insurance_provider: '',
    insurance_policy_number: '',
    insurance_group_number: '',
    consent_given: false
  });

  useEffect(() => {
    fetchPatients();
  }, []);

  // Filter patients based on search term
  const filteredPatients = patients.filter(patient => {
    if (!patientSearchTerm) return true;
    
    const searchLower = patientSearchTerm.toLowerCase();
    return (
      patient.first_name.toLowerCase().includes(searchLower) ||
      patient.last_name.toLowerCase().includes(searchLower) ||
      `${patient.first_name} ${patient.last_name}`.toLowerCase().includes(searchLower) ||
      patient.patient_id.toLowerCase().includes(searchLower) ||
      patient.medical_record_number.toLowerCase().includes(searchLower)
    );
  });

  // Handle patient selection from dropdown
  const handlePatientSelect = (patient) => {
    setSelectedPatient(patient.id);
    setPatientSearchTerm(`${patient.first_name} ${patient.last_name} (ID: ${patient.patient_id})`);
    setShowPatientDropdown(false);
  };

  // Handle search input focus
  const handleSearchFocus = () => {
    setShowPatientDropdown(true);
    setPatientSearchTerm('');
  };

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (patientSearchRef.current && !patientSearchRef.current.contains(event.target)) {
        setShowPatientDropdown(false);
        // If no patient selected, clear search
        if (!selectedPatient) {
          setPatientSearchTerm('');
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [selectedPatient]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingPatient) {
        await axios.put(`${API}/patients/${editingPatient.id}`, formData);
        toast.success('Patient updated successfully');
      } else {
        await axios.post(`${API}/patients`, formData);
        toast.success('Patient created successfully');
      }
      
      setShowForm(false);
      setEditingPatient(null);
      resetForm();
      fetchPatients();
    } catch (error) {
      toast.error('Operation failed');
    }
  };

  const handleEdit = (patient) => {
    setEditingPatient(patient);
    setFormData({
      patient_id: patient.patient_id,
      first_name: patient.first_name,
      last_name: patient.last_name,
      date_of_birth: patient.date_of_birth,
      gender: patient.gender,
      phone: patient.phone,
      email: patient.email || '',
      address: patient.address,
      medical_record_number: patient.medical_record_number,
      primary_physician: patient.primary_physician,
      allergies: patient.allergies,
      medications: patient.medications,
      medical_history: patient.medical_history,
      insurance_provider: patient.insurance_provider,
      insurance_policy_number: patient.insurance_policy_number,
      insurance_group_number: patient.insurance_group_number || '',
      consent_given: patient.consent_given
    });
    setShowForm(true);
  };

  const handleDelete = async (patientId) => {
    if (window.confirm('Are you sure you want to delete this patient?')) {
      try {
        await axios.delete(`${API}/patients/${patientId}`);
        toast.success('Patient deleted successfully');
        fetchPatients();
      } catch (error) {
        toast.error('Failed to delete patient');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      patient_id: '',
      first_name: '',
      last_name: '',
      date_of_birth: '',
      gender: '',
      phone: '',
      email: '',
      address: '',
      medical_record_number: '',
      primary_physician: '',
      allergies: [],
      medications: [],
      medical_history: [],
      insurance_provider: '',
      insurance_policy_number: '',
      insurance_group_number: '',
      consent_given: false
    });
  };

  const filteredPatientsForManagement = patients.filter(patient =>
    patient.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    patient.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    patient.patient_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="text-center">Loading patients...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Patient Management</h1>
        <button
          onClick={() => setShowForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Add Patient</span>
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search patients..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Patient ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date of Birth
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Gender
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Phone
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredPatients.map((patient) => (
                <tr key={patient.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {patient.patient_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {patient.first_name} {patient.last_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {patient.date_of_birth}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {patient.gender}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {patient.phone}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => handleEdit(patient)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(patient.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Patient Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b">
              <h2 className="text-2xl font-bold text-gray-800">
                {editingPatient ? 'Edit Patient' : 'Add New Patient'}
              </h2>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Patient ID
                  </label>
                  <input
                    type="text"
                    value={formData.patient_id}
                    onChange={(e) => setFormData({...formData, patient_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Medical Record Number
                  </label>
                  <input
                    type="text"
                    value={formData.medical_record_number}
                    onChange={(e) => setFormData({...formData, medical_record_number: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    First Name
                  </label>
                  <input
                    type="text"
                    value={formData.first_name}
                    onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Last Name
                  </label>
                  <input
                    type="text"
                    value={formData.last_name}
                    onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    value={formData.date_of_birth}
                    onChange={(e) => setFormData({...formData, date_of_birth: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Gender
                  </label>
                  <select
                    value={formData.gender}
                    onChange={(e) => setFormData({...formData, gender: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select Gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone
                  </label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Primary Physician
                  </label>
                  <input
                    type="text"
                    value={formData.primary_physician}
                    onChange={(e) => setFormData({...formData, primary_physician: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Insurance Provider
                  </label>
                  <input
                    type="text"
                    value={formData.insurance_provider}
                    onChange={(e) => setFormData({...formData, insurance_provider: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Insurance Policy Number
                  </label>
                  <input
                    type="text"
                    value={formData.insurance_policy_number}
                    onChange={(e) => setFormData({...formData, insurance_policy_number: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Insurance Group Number
                  </label>
                  <input
                    type="text"
                    value={formData.insurance_group_number}
                    onChange={(e) => setFormData({...formData, insurance_group_number: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Address
                </label>
                <textarea
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                  required
                />
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="consent"
                  checked={formData.consent_given}
                  onChange={(e) => setFormData({...formData, consent_given: e.target.checked})}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="consent" className="ml-2 block text-sm text-gray-700">
                  Patient has given consent for data processing (HIPAA compliance)
                </label>
              </div>
              
              <div className="flex justify-end space-x-3 pt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setEditingPatient(null);
                    resetForm();
                  }}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  {editingPatient ? 'Update Patient' : 'Add Patient'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Image Upload Component
const ImageUpload = () => {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [uploadData, setUploadData] = useState({
    study_id: '',
    series_id: '',
    modality: '',
    body_part: '',
    study_date: '',
    study_time: '',
    institution_name: '',
    referring_physician: ''
  });
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`);
      setPatients(response.data);
    } catch (error) {
      toast.error('Failed to fetch patients');
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(files);
  };

  const handleUpload = async () => {
    if (!selectedPatient || selectedFiles.length === 0) {
      toast.error('Please select a patient and at least one file');
      return;
    }

    setUploading(true);
    
    for (const file of selectedFiles) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('study_id', uploadData.study_id);
        formData.append('series_id', uploadData.series_id);
        formData.append('modality', uploadData.modality);
        formData.append('body_part', uploadData.body_part);
        formData.append('study_date', uploadData.study_date);
        formData.append('study_time', uploadData.study_time);
        formData.append('institution_name', uploadData.institution_name);
        formData.append('referring_physician', uploadData.referring_physician);

        await axios.post(`${API}/patients/${selectedPatient}/images`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        toast.success(`${file.name} uploaded successfully`);
      } catch (error) {
        toast.error(`Failed to upload ${file.name}`);
      }
    }
    
    setUploading(false);
    setSelectedFiles([]);
    
    // Reset form
    setUploadData({
      study_id: '',
      series_id: '',
      modality: '',
      body_part: '',
      study_date: '',
      study_time: '',
      institution_name: '',
      referring_physician: ''
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Upload Medical Images</h1>
      </div>

      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Patient
            </label>
            <select
              value={selectedPatient}
              onChange={(e) => setSelectedPatient(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              <option value="">Select a patient</option>
              {patients.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {patient.first_name} {patient.last_name} (ID: {patient.patient_id})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Study ID
              </label>
              <input
                type="text"
                value={uploadData.study_id}
                onChange={(e) => setUploadData({...uploadData, study_id: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Series ID
              </label>
              <input
                type="text"
                value={uploadData.series_id}
                onChange={(e) => setUploadData({...uploadData, series_id: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Modality
              </label>
              <select
                value={uploadData.modality}
                onChange={(e) => setUploadData({...uploadData, modality: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select modality</option>
                <option value="CT">CT</option>
                <option value="MRI">MRI</option>
                <option value="X-Ray">X-Ray</option>
                <option value="Ultrasound">Ultrasound</option>
                <option value="PET">PET</option>
                <option value="Mammography">Mammography</option>
                <option value="Nuclear Medicine">Nuclear Medicine</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Body Part
              </label>
              <input
                type="text"
                value={uploadData.body_part}
                onChange={(e) => setUploadData({...uploadData, body_part: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Chest, Head, Abdomen"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Study Date
              </label>
              <input
                type="date"
                value={uploadData.study_date}
                onChange={(e) => setUploadData({...uploadData, study_date: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Study Time
              </label>
              <input
                type="time"
                value={uploadData.study_time}
                onChange={(e) => setUploadData({...uploadData, study_time: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Institution Name
              </label>
              <input
                type="text"
                value={uploadData.institution_name}
                onChange={(e) => setUploadData({...uploadData, institution_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Referring Physician
              </label>
              <input
                type="text"
                value={uploadData.referring_physician}
                onChange={(e) => setUploadData({...uploadData, referring_physician: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Files
            </label>
            <input
              type="file"
              multiple
              accept=".dcm,.jpg,.jpeg,.png,.tiff,.tif"
              onChange={handleFileSelect}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-sm text-gray-500 mt-2">
              Supported formats: DICOM (.dcm), JPEG, PNG, TIFF
            </p>
          </div>

          {selectedFiles.length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-2">Selected Files:</h3>
              <div className="space-y-2">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <ImageIcon className="w-5 h-5 text-gray-400" />
                      <span className="text-sm text-gray-700">{file.name}</span>
                    </div>
                    <span className="text-sm text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end">
            <button
              onClick={handleUpload}
              disabled={uploading || !selectedPatient || selectedFiles.length === 0}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <Upload className="w-4 h-4" />
              <span>{uploading ? 'Uploading...' : 'Upload Images'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Medical Image Viewer Component
const MedicalImageViewer = () => {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [patientImages, setPatientImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [patientSearchTerm, setPatientSearchTerm] = useState('');
  const [showPatientDropdown, setShowPatientDropdown] = useState(false);
  const [viewerState, setViewerState] = useState({
    zoom: 1,
    rotation: 0,
    brightness: 1,
    contrast: 1,
    windowCenter: 0,
    windowWidth: 0,
    isMaximized: false,
    noiseThreshold: 0,
    boneRemoval: 0,
    fleshRemoval: 0
  });
  const [annotationState, setAnnotationState] = useState({
    tool: 'none', // 'line', 'rectangle', 'arrow', 'circle', 'text', 'ruler', 'angle', 'roi'
    isDrawing: false,
    startPoint: null,
    annotations: [],
    measurements: []
  });
  const canvasRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const patientSearchRef = useRef(null);

  useEffect(() => {
    fetchPatients();
  }, []);

  useEffect(() => {
    if (selectedPatient) {
      fetchPatientImages();
    }
  }, [selectedPatient]);

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`);
      setPatients(response.data);
    } catch (error) {
      toast.error('Failed to fetch patients');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedImage && canvasRef.current) {
      renderImage();
    }
  }, [selectedImage, viewerState]);

  useEffect(() => {
    if (overlayCanvasRef.current) {
      drawAnnotations();
    }
  }, [annotationState.annotations, annotationState.measurements, viewerState.zoom, viewerState.rotation]);

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`);
      setPatients(response.data);
    } catch (error) {
      toast.error('Failed to fetch patients');
    }
  };

  const fetchPatientImages = async () => {
    try {
      const response = await axios.get(`${API}/patients/${selectedPatient}/images`);
      setPatientImages(response.data);
    } catch (error) {
      toast.error('Failed to fetch patient images');
    }
  };

  // Advanced image processing functions
  const applyNoiseReduction = (imageData, threshold) => {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    
    // Apply median filter for noise reduction
    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        const idx = (y * width + x) * 4;
        
        // Get surrounding pixels
        const neighbors = [];
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            const nIdx = ((y + dy) * width + (x + dx)) * 4;
            neighbors.push(data[nIdx]);
          }
        }
        
        // Apply threshold-based noise reduction
        neighbors.sort((a, b) => a - b);
        const median = neighbors[4];
        const currentPixel = data[idx];
        
        if (Math.abs(currentPixel - median) > threshold) {
          data[idx] = data[idx + 1] = data[idx + 2] = median;
        }
      }
    }
    
    return imageData;
  };

  const applyBoneRemoval = (imageData, intensity) => {
    const data = imageData.data;
    
    for (let i = 0; i < data.length; i += 4) {
      const grayscale = (data[i] + data[i + 1] + data[i + 2]) / 3;
      
      // Remove high-density pixels (bones appear bright in X-rays)
      if (grayscale > 200 - (intensity * 50)) {
        const reduction = intensity * 0.8;
        data[i] *= (1 - reduction);     // R
        data[i + 1] *= (1 - reduction); // G
        data[i + 2] *= (1 - reduction); // B
      }
    }
    
    return imageData;
  };

  const applyFleshRemoval = (imageData, intensity) => {
    const data = imageData.data;
    
    for (let i = 0; i < data.length; i += 4) {
      const grayscale = (data[i] + data[i + 1] + data[i + 2]) / 3;
      
      // Remove low-density pixels (soft tissue appears darker)
      if (grayscale < 150 + (intensity * 50)) {
        const reduction = intensity * 0.7;
        data[i] *= (1 - reduction);     // R
        data[i + 1] *= (1 - reduction); // G
        data[i + 2] *= (1 - reduction); // B
      }
    }
    
    return imageData;
  };

  const renderImage = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    if (!selectedImage || !canvas) return;

    const img = new Image();
    img.onload = () => {
      // Set canvas size to match container
      canvas.width = 800;
      canvas.height = 600;
      
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Calculate image dimensions to fit canvas while maintaining aspect ratio
      const imgAspect = img.width / img.height;
      const canvasAspect = canvas.width / canvas.height;
      
      let drawWidth, drawHeight, drawX, drawY;
      
      if (imgAspect > canvasAspect) {
        // Image is wider than canvas
        drawWidth = canvas.width * 0.8; // Leave some margin
        drawHeight = drawWidth / imgAspect;
      } else {
        // Image is taller than canvas
        drawHeight = canvas.height * 0.8; // Leave some margin
        drawWidth = drawHeight * imgAspect;
      }
      
      drawX = (canvas.width - drawWidth) / 2;
      drawY = (canvas.height - drawHeight) / 2;
      
      // Save context state
      ctx.save();
      
      // Apply transformations
      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.scale(viewerState.zoom, viewerState.zoom);
      ctx.rotate((viewerState.rotation * Math.PI) / 180);
      ctx.translate(-canvas.width / 2, -canvas.height / 2);
      
      // Apply brightness and contrast
      ctx.filter = `brightness(${viewerState.brightness}) contrast(${viewerState.contrast})`;
      
      // Draw image
      ctx.drawImage(img, drawX, drawY, drawWidth, drawHeight);
      
      // Apply advanced image processing if needed
      if (viewerState.noiseThreshold > 0 || viewerState.boneRemoval > 0 || viewerState.fleshRemoval > 0) {
        try {
          const imageData = ctx.getImageData(drawX, drawY, drawWidth, drawHeight);
          
          if (viewerState.noiseThreshold > 0) {
            applyNoiseReduction(imageData, viewerState.noiseThreshold * 50);
          }
          
          if (viewerState.boneRemoval > 0) {
            applyBoneRemoval(imageData, viewerState.boneRemoval);
          }
          
          if (viewerState.fleshRemoval > 0) {
            applyFleshRemoval(imageData, viewerState.fleshRemoval);
          }
          
          ctx.putImageData(imageData, drawX, drawY);
        } catch (error) {
          console.log('Advanced processing not applied due to canvas restrictions');
        }
      }
      
      // Restore context state
      ctx.restore();
    };
    
    img.onerror = () => {
      console.error('Failed to load image');
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#333';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#fff';
      ctx.font = '16px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('Failed to load image', canvas.width / 2, canvas.height / 2);
    };
    
    // Set the image source
    img.src = `data:image/png;base64,${selectedImage.image_data}`;
  };

  const drawAnnotations = () => {
    const overlayCanvas = overlayCanvasRef.current;
    if (!overlayCanvas) return;
    
    const ctx = overlayCanvas.getContext('2d');
    // Set overlay canvas size to match main canvas
    overlayCanvas.width = 800;
    overlayCanvas.height = 600;
    ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    
    // Apply the same transformations as the main canvas
    ctx.save();
    
    // Apply transformations to match the image
    ctx.translate(overlayCanvas.width / 2, overlayCanvas.height / 2);
    ctx.scale(viewerState.zoom, viewerState.zoom);
    ctx.rotate((viewerState.rotation * Math.PI) / 180);
    ctx.translate(-overlayCanvas.width / 2, -overlayCanvas.height / 2);
    
    // Draw annotations
    annotationState.annotations.forEach(annotation => {
      ctx.strokeStyle = annotation.color || '#ff0000';
      ctx.lineWidth = 2 / viewerState.zoom; // Adjust line width for zoom
      ctx.fillStyle = annotation.color || '#ff0000';
      
      switch (annotation.type) {
        case 'line':
          ctx.beginPath();
          ctx.moveTo(annotation.startX, annotation.startY);
          ctx.lineTo(annotation.endX, annotation.endY);
          ctx.stroke();
          break;
          
        case 'rectangle':
          ctx.strokeRect(
            annotation.x, 
            annotation.y, 
            annotation.width, 
            annotation.height
          );
          break;
          
        case 'circle':
          ctx.beginPath();
          ctx.arc(annotation.x, annotation.y, annotation.radius, 0, 2 * Math.PI);
          ctx.stroke();
          break;
          
        case 'arrow':
          drawArrow(ctx, annotation.startX, annotation.startY, annotation.endX, annotation.endY);
          break;
          
        case 'text':
          ctx.save();
          ctx.font = `${16 / viewerState.zoom}px Arial`; // Adjust font size for zoom
          ctx.fillText(annotation.text, annotation.x, annotation.y);
          ctx.restore();
          break;
          
        case 'roi':
          ctx.strokeStyle = '#00ff00';
          ctx.setLineDash([5 / viewerState.zoom, 5 / viewerState.zoom]); // Adjust dash for zoom
          ctx.strokeRect(annotation.x, annotation.y, annotation.width, annotation.height);
          ctx.setLineDash([]);
          break;
      }
    });
    
    // Draw measurements
    annotationState.measurements.forEach(measurement => {
      ctx.strokeStyle = '#ffff00';
      ctx.lineWidth = 2 / viewerState.zoom;
      ctx.font = `${14 / viewerState.zoom}px Arial`;
      ctx.fillStyle = '#ffff00';
      
      if (measurement.type === 'distance') {
        // Draw line
        ctx.beginPath();
        ctx.moveTo(measurement.startX, measurement.startY);
        ctx.lineTo(measurement.endX, measurement.endY);
        ctx.stroke();
        
        // Draw measurement text
        const midX = (measurement.startX + measurement.endX) / 2;
        const midY = (measurement.startY + measurement.endY) / 2;
        
        ctx.save();
        // Rotate text to be readable regardless of image rotation
        ctx.translate(midX, midY);
        ctx.rotate(-viewerState.rotation * Math.PI / 180); // Counter-rotate text
        ctx.fillText(`${measurement.value.toFixed(2)} px`, 5 / viewerState.zoom, -5 / viewerState.zoom);
        ctx.restore();
        
      } else if (measurement.type === 'angle') {
        // Draw angle lines
        ctx.beginPath();
        ctx.moveTo(measurement.vertex.x, measurement.vertex.y);
        ctx.lineTo(measurement.point1.x, measurement.point1.y);
        ctx.moveTo(measurement.vertex.x, measurement.vertex.y);
        ctx.lineTo(measurement.point2.x, measurement.point2.y);
        ctx.stroke();
        
        // Draw angle arc
        ctx.beginPath();
        ctx.arc(measurement.vertex.x, measurement.vertex.y, 30 / viewerState.zoom, measurement.startAngle, measurement.endAngle);
        ctx.stroke();
        
        // Draw angle text
        ctx.save();
        ctx.translate(measurement.vertex.x, measurement.vertex.y);
        ctx.rotate(-viewerState.rotation * Math.PI / 180); // Counter-rotate text
        ctx.fillText(`${measurement.value.toFixed(1)}°`, 35 / viewerState.zoom, 0);
        ctx.restore();
      }
    });
    
    ctx.restore();
  };

  const drawArrow = (ctx, startX, startY, endX, endY) => {
    const headLength = 20 / viewerState.zoom; // Adjust arrow head size for zoom
    const dx = endX - startX;
    const dy = endY - startY;
    const angle = Math.atan2(dy, dx);
    
    // Draw line
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.stroke();
    
    // Draw arrowhead
    ctx.beginPath();
    ctx.moveTo(endX, endY);
    ctx.lineTo(
      endX - headLength * Math.cos(angle - Math.PI / 6),
      endY - headLength * Math.sin(angle - Math.PI / 6)
    );
    ctx.moveTo(endX, endY);
    ctx.lineTo(
      endX - headLength * Math.cos(angle + Math.PI / 6),
      endY - headLength * Math.sin(angle + Math.PI / 6)
    );
    ctx.stroke();
  };

  const calculateDistance = (x1, y1, x2, y2) => {
    return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
  };

  const calculateAngle = (vertex, point1, point2) => {
    const angle1 = Math.atan2(point1.y - vertex.y, point1.x - vertex.x);
    const angle2 = Math.atan2(point2.y - vertex.y, point2.x - vertex.x);
    let angle = Math.abs(angle1 - angle2) * (180 / Math.PI);
    return angle > 180 ? 360 - angle : angle;
  };

  // Helper function to transform mouse coordinates to image space
  const transformMouseCoordinates = (clientX, clientY) => {
    const rect = overlayCanvasRef.current.getBoundingClientRect();
    const canvasX = clientX - rect.left;
    const canvasY = clientY - rect.top;
    
    // Convert from canvas coordinates to image coordinates accounting for transformations
    const centerX = overlayCanvasRef.current.width / 2;
    const centerY = overlayCanvasRef.current.height / 2;
    
    // Reverse the transformations applied to the canvas
    // 1. Translate to origin
    let x = canvasX - centerX;
    let y = canvasY - centerY;
    
    // 2. Reverse zoom
    x = x / viewerState.zoom;
    y = y / viewerState.zoom;
    
    // 3. Reverse rotation
    const rotationRad = -viewerState.rotation * Math.PI / 180;
    const rotatedX = x * Math.cos(rotationRad) - y * Math.sin(rotationRad);
    const rotatedY = x * Math.sin(rotationRad) + y * Math.cos(rotationRad);
    
    // 4. Translate back
    return {
      x: rotatedX + centerX,
      y: rotatedY + centerY
    };
  };

  const handleCanvasMouseDown = (e) => {
    if (annotationState.tool === 'none') return;
    
    const transformed = transformMouseCoordinates(e.clientX, e.clientY);
    
    setAnnotationState(prev => ({
      ...prev,
      isDrawing: true,
      startPoint: transformed
    }));
  };

  const handleCanvasMouseMove = (e) => {
    const rect = overlayCanvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setMousePos({ x, y });
  };

  const handleCanvasMouseUp = (e) => {
    if (!annotationState.isDrawing || !annotationState.startPoint) return;
    
    const transformed = transformMouseCoordinates(e.clientX, e.clientY);
    const { x: startX, y: startY } = annotationState.startPoint;
    const { x: endX, y: endY } = transformed;
    
    let newAnnotation = null;
    let newMeasurement = null;
    
    switch (annotationState.tool) {
      case 'line':
        newAnnotation = {
          type: 'line',
          startX,
          startY,
          endX,
          endY,
          color: '#ff0000'
        };
        break;
        
      case 'rectangle':
        newAnnotation = {
          type: 'rectangle',
          x: Math.min(startX, endX),
          y: Math.min(startY, endY),
          width: Math.abs(endX - startX),
          height: Math.abs(endY - startY),
          color: '#ff0000'
        };
        break;
        
      case 'circle':
        const radius = calculateDistance(startX, startY, endX, endY);
        newAnnotation = {
          type: 'circle',
          x: startX,
          y: startY,
          radius,
          color: '#ff0000'
        };
        break;
        
      case 'arrow':
        newAnnotation = {
          type: 'arrow',
          startX,
          startY,
          endX,
          endY,
          color: '#ff0000'
        };
        break;
        
      case 'roi':
        newAnnotation = {
          type: 'roi',
          x: Math.min(startX, endX),
          y: Math.min(startY, endY),
          width: Math.abs(endX - startX),
          height: Math.abs(endY - startY),
          color: '#00ff00'
        };
        break;
        
      case 'ruler':
        const distance = calculateDistance(startX, startY, endX, endY);
        newMeasurement = {
          type: 'distance',
          startX,
          startY,
          endX,
          endY,
          value: distance
        };
        break;
    }
    
    setAnnotationState(prev => ({
      ...prev,
      isDrawing: false,
      startPoint: null,
      annotations: newAnnotation ? [...prev.annotations, newAnnotation] : prev.annotations,
      measurements: newMeasurement ? [...prev.measurements, newMeasurement] : prev.measurements
    }));
  };

  const handleTextAnnotation = (clientX, clientY) => {
    const text = prompt('Enter annotation text:');
    if (text) {
      const transformed = transformMouseCoordinates(clientX, clientY);
      
      const newAnnotation = {
        type: 'text',
        x: transformed.x,
        y: transformed.y,
        text,
        color: '#ff0000'
      };
      
      setAnnotationState(prev => ({
        ...prev,
        annotations: [...prev.annotations, newAnnotation]
      }));
    }
  };

  const clearAnnotations = () => {
    setAnnotationState(prev => ({
      ...prev,
      annotations: [],
      measurements: []
    }));
  };

  const handleImageSelect = (image) => {
    setSelectedImage(image);
    setViewerState({
      zoom: 1,
      rotation: 0,
      brightness: 1,
      contrast: 1,
      windowCenter: image.window_center || 0,
      windowWidth: image.window_width || 0,
      isMaximized: false,
      noiseThreshold: 0,
      boneRemoval: 0,
      fleshRemoval: 0
    });
    
    // Clear annotations when switching images
    setAnnotationState(prev => ({
      ...prev,
      annotations: [],
      measurements: []
    }));
    
    // Ensure overlay canvas is properly set up
    setTimeout(() => {
      if (overlayCanvasRef.current) {
        const overlayCanvas = overlayCanvasRef.current;
        overlayCanvas.width = 800;
        overlayCanvas.height = 600;
      }
    }, 100);
  };

  const handleZoom = (delta) => {
    setViewerState(prev => ({
      ...prev,
      zoom: Math.max(0.1, Math.min(5, prev.zoom + delta))
    }));
  };

  const handleRotation = (angle) => {
    setViewerState(prev => ({
      ...prev,
      rotation: (prev.rotation + angle) % 360
    }));
  };

  const handleBrightness = (delta) => {
    setViewerState(prev => ({
      ...prev,
      brightness: Math.max(0.1, Math.min(3, prev.brightness + delta))
    }));
  };

  const handleContrast = (delta) => {
    setViewerState(prev => ({
      ...prev,
      contrast: Math.max(0.1, Math.min(3, prev.contrast + delta))
    }));
  };

  const handleReset = () => {
    setViewerState(prev => ({
      ...prev,
      zoom: 1,
      rotation: 0,
      brightness: 1,
      contrast: 1
    }));
  };

  const handleMaximize = () => {
    setViewerState(prev => ({
      ...prev,
      isMaximized: !prev.isMaximized
    }));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">JAJUWA HEALTHCARE Medical Image Viewer</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Patient Selection and Image List */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search & Select Patient
            </label>
            <div className="relative" ref={patientSearchRef}>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  value={patientSearchTerm}
                  onChange={(e) => {
                    setPatientSearchTerm(e.target.value);
                    setShowPatientDropdown(true);
                  }}
                  onFocus={handleSearchFocus}
                  placeholder="Search by name, Patient ID, or Medical Record Number..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              {showPatientDropdown && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {filteredPatients.length > 0 ? (
                    filteredPatients.map((patient) => (
                      <div
                        key={patient.id}
                        onClick={() => handlePatientSelect(patient)}
                        className="p-3 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium text-gray-900">
                              {patient.first_name} {patient.last_name}
                            </p>
                            <p className="text-sm text-gray-600">
                              Patient ID: {patient.patient_id}
                            </p>
                            <p className="text-sm text-gray-600">
                              MRN: {patient.medical_record_number}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-gray-500">
                              {patient.gender}, DOB: {patient.date_of_birth}
                            </p>
                            <p className="text-xs text-gray-500">
                              Dr. {patient.primary_physician}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-3 text-center text-gray-500">
                      {patientSearchTerm ? 'No patients found matching your search' : 'Start typing to search patients...'}
                    </div>
                  )}
                </div>
              )}
            </div>
            
            {selectedPatient && (
              <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  ✓ Patient selected: {patients.find(p => p.id === selectedPatient)?.first_name} {patients.find(p => p.id === selectedPatient)?.last_name}
                </p>
              </div>
            )}
          </div>

          {selectedPatient && (
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <h3 className="text-lg font-medium text-gray-800 mb-4">Patient Images</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {patientImages.map((image) => (
                  <div
                    key={image.id}
                    onClick={() => handleImageSelect(image)}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedImage?.id === image.id
                        ? 'bg-blue-100 border-blue-300'
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <img
                        src={`data:image/png;base64,${image.thumbnail_data}`}
                        alt="Thumbnail"
                        className="w-12 h-12 object-cover rounded"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {image.modality} - {image.body_part}
                        </p>
                        <p className="text-xs text-gray-500">
                          {image.study_date} {image.study_time}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Advanced Image Viewer */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border">
            {selectedImage ? (
              <div className="p-4">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h3 className="text-lg font-medium text-gray-800">
                      {selectedImage.modality} - {selectedImage.body_part}
                    </h3>
                    <p className="text-sm text-gray-600">
                      Study: {selectedImage.study_date} {selectedImage.study_time}
                    </p>
                  </div>
                  
                  {/* Annotation Tools */}
                  <div className="flex flex-wrap gap-2">
                    <div className="flex bg-gray-100 rounded-lg p-1">
                      <button
                        onClick={() => setAnnotationState(prev => ({...prev, tool: 'none'}))}
                        className={`p-2 rounded ${annotationState.tool === 'none' ? 'bg-blue-500 text-white' : 'hover:bg-gray-200'}`}
                        title="Select/Move"
                      >
                        <MousePointer className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setAnnotationState(prev => ({...prev, tool: 'line'}))}
                        className={`p-2 rounded ${annotationState.tool === 'line' ? 'bg-blue-500 text-white' : 'hover:bg-gray-200'}`}
                        title="Line"
                      >
                        <div className="w-4 h-4 border-b-2 border-current"></div>
                      </button>
                      <button
                        onClick={() => setAnnotationState(prev => ({...prev, tool: 'rectangle'}))}
                        className={`p-2 rounded ${annotationState.tool === 'rectangle' ? 'bg-blue-500 text-white' : 'hover:bg-gray-200'}`}
                        title="Rectangle"
                      >
                        <div className="w-4 h-4 border-2 border-current"></div>
                      </button>
                      <button
                        onClick={() => setAnnotationState(prev => ({...prev, tool: 'circle'}))}
                        className={`p-2 rounded ${annotationState.tool === 'circle' ? 'bg-blue-500 text-white' : 'hover:bg-gray-200'}`}
                        title="Circle"
                      >
                        <div className="w-4 h-4 border-2 border-current rounded-full"></div>
                      </button>
                      <button
                        onClick={() => setAnnotationState(prev => ({...prev, tool: 'arrow'}))}
                        className={`p-2 rounded ${annotationState.tool === 'arrow' ? 'bg-blue-500 text-white' : 'hover:bg-gray-200'}`}
                        title="Arrow"
                      >
                        ➤
                      </button>
                      <button
                        onClick={() => setAnnotationState(prev => ({...prev, tool: 'text'}))}
                        className={`p-2 rounded ${annotationState.tool === 'text' ? 'bg-blue-500 text-white' : 'hover:bg-gray-200'}`}
                        title="Text"
                      >
                        T
                      </button>
                      <button
                        onClick={() => setAnnotationState(prev => ({...prev, tool: 'ruler'}))}
                        className={`p-2 rounded ${annotationState.tool === 'ruler' ? 'bg-blue-500 text-white' : 'hover:bg-gray-200'}`}
                        title="Ruler"
                      >
                        <Ruler className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setAnnotationState(prev => ({...prev, tool: 'roi'}))}
                        className={`p-2 rounded ${annotationState.tool === 'roi' ? 'bg-blue-500 text-white' : 'hover:bg-gray-200'}`}
                        title="ROI"
                      >
                        ROI
                      </button>
                      <button
                        onClick={clearAnnotations}
                        className="p-2 rounded hover:bg-red-200 text-red-600"
                        title="Clear All"
                      >
                        ✕
                      </button>
                    </div>
                    
                    {/* Basic Controls */}
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleZoom(-0.1)}
                        className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                        title="Zoom Out"
                      >
                        <ZoomOut className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleZoom(0.1)}
                        className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                        title="Zoom In"
                      >
                        <ZoomIn className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleRotation(-90)}
                        className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                        title="Rotate Left"
                      >
                        <RotateCcw className="w-4 h-4" />
                      </button>
                      <button
                        onClick={handleReset}
                        className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                        title="Reset View"
                      >
                        <MousePointer className="w-4 h-4" />
                      </button>
                      <button
                        onClick={handleMaximize}
                        className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                        title="Maximize"
                      >
                        <Maximize className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>

                <div className="border border-gray-200 rounded-lg overflow-hidden relative">
                  <div className="canvas-container relative inline-block">
                    <canvas
                      ref={canvasRef}
                      width={800}
                      height={600}
                      className="main-canvas block bg-black"
                      style={{
                        width: '100%',
                        height: 'auto',
                        maxHeight: viewerState.isMaximized ? '80vh' : '600px'
                      }}
                    />
                    <canvas
                      ref={overlayCanvasRef}
                      width={800}
                      height={600}
                      className="overlay-canvas absolute top-0 left-0 cursor-crosshair"
                      style={{
                        width: '100%',
                        height: 'auto',
                        maxHeight: viewerState.isMaximized ? '80vh' : '600px'
                      }}
                      onMouseDown={handleCanvasMouseDown}
                      onMouseMove={handleCanvasMouseMove}
                      onMouseUp={handleCanvasMouseUp}
                      onClick={(e) => {
                        if (annotationState.tool === 'text') {
                          handleTextAnnotation(e.clientX, e.clientY);
                        }
                      }}
                    />
                  </div>
                </div>

                {/* Advanced Controls */}
                <div className="mt-4 space-y-4">
                  {/* Basic Image Controls */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Zoom: {(viewerState.zoom * 100).toFixed(0)}%
                      </label>
                      <input
                        type="range"
                        min="0.1"
                        max="5"
                        step="0.1"
                        value={viewerState.zoom}
                        onChange={(e) => setViewerState(prev => ({...prev, zoom: parseFloat(e.target.value)}))}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Brightness: {(viewerState.brightness * 100).toFixed(0)}%
                      </label>
                      <input
                        type="range"
                        min="0.1"
                        max="3"
                        step="0.1"
                        value={viewerState.brightness}
                        onChange={(e) => setViewerState(prev => ({...prev, brightness: parseFloat(e.target.value)}))}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Contrast: {(viewerState.contrast * 100).toFixed(0)}%
                      </label>
                      <input
                        type="range"
                        min="0.1"
                        max="3"
                        step="0.1"
                        value={viewerState.contrast}
                        onChange={(e) => setViewerState(prev => ({...prev, contrast: parseFloat(e.target.value)}))}
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Rotation: {viewerState.rotation}°
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="360"
                        step="1"
                        value={viewerState.rotation}
                        onChange={(e) => setViewerState(prev => ({...prev, rotation: parseInt(e.target.value)}))}
                        className="w-full"
                      />
                    </div>
                  </div>

                  {/* Advanced Image Processing Controls */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Advanced Image Processing</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Noise Removal: {(viewerState.noiseThreshold * 100).toFixed(0)}%
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.01"
                          value={viewerState.noiseThreshold}
                          onChange={(e) => setViewerState(prev => ({...prev, noiseThreshold: parseFloat(e.target.value)}))}
                          className="w-full"
                        />
                        <p className="text-xs text-gray-500 mt-1">Removes image noise using median filtering</p>
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Bone Removal: {(viewerState.boneRemoval * 100).toFixed(0)}%
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.01"
                          value={viewerState.boneRemoval}
                          onChange={(e) => setViewerState(prev => ({...prev, boneRemoval: parseFloat(e.target.value)}))}
                          className="w-full"
                        />
                        <p className="text-xs text-gray-500 mt-1">Reduces high-density structures (bones)</p>
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Flesh Removal: {(viewerState.fleshRemoval * 100).toFixed(0)}%
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.01"
                          value={viewerState.fleshRemoval}
                          onChange={(e) => setViewerState(prev => ({...prev, fleshRemoval: parseFloat(e.target.value)}))}
                          className="w-full"
                        />
                        <p className="text-xs text-gray-500 mt-1">Reduces low-density structures (soft tissue)</p>
                      </div>
                    </div>
                  </div>

                  {/* Measurements Display */}
                  {(annotationState.measurements.length > 0 || annotationState.annotations.length > 0) && (
                    <div className="bg-blue-50 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-3">Measurements & Annotations</h4>
                      <div className="space-y-2">
                        {annotationState.measurements.map((measurement, index) => (
                          <div key={index} className="text-sm text-gray-600">
                            {measurement.type === 'distance' && (
                              <span>Distance {index + 1}: {measurement.value.toFixed(2)} pixels</span>
                            )}
                            {measurement.type === 'angle' && (
                              <span>Angle {index + 1}: {measurement.value.toFixed(1)}°</span>
                            )}
                          </div>
                        ))}
                        {annotationState.annotations.length > 0 && (
                          <div className="text-sm text-gray-600">
                            Annotations: {annotationState.annotations.length} items
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Mouse Position Display */}
                <div className="mt-2 text-xs text-gray-500">
                  Mouse Position: X: {mousePos.x}, Y: {mousePos.y}
                </div>

                {selectedImage.dicom_metadata && Object.keys(selectedImage.dicom_metadata).length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">DICOM Metadata</h4>
                    <div className="bg-gray-50 rounded-lg p-3 max-h-32 overflow-y-auto">
                      <pre className="text-xs text-gray-600">
                        {JSON.stringify(selectedImage.dicom_metadata, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-12 text-center text-gray-500">
                <ImageIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p>Select a patient and image to view</p>
                <p className="text-sm mt-2">Use annotation tools to mark areas of interest</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = ({ activeTab }) => {
  const renderContent = () => {
    switch (activeTab) {
      case 'patients':
        return <PatientManagement />;
      case 'viewer':
        return <MedicalImageViewer />;
      case 'upload':
        return <ImageUpload />;
      default:
        return <PatientManagement />;
    }
  };

  return renderContent();
};

// Main App Component
const App = () => {
  const { user, loading } = useAuth();
  const { isDarkMode } = useTheme();

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${
        isDarkMode ? 'bg-slate-900' : 'bg-gray-50'
      }`}>
        <div className="text-center">
          <div className={`animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4 ${
            isDarkMode ? 'border-blue-500' : 'border-blue-600'
          }`}></div>
          <p className={isDarkMode ? 'text-slate-300' : 'text-gray-600'}>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route
            path="/login"
            element={!user ? <Login /> : <Navigate to="/" replace />}
          />
          <Route
            path="/"
            element={
              user ? (
                <DashboardLayout>
                  <Dashboard />
                </DashboardLayout>
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
        </Routes>
        <ToastContainer
          position="top-right"
          autoClose={3000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
        />
      </div>
    </Router>
  );
};

// Export with AuthProvider and ThemeProvider wrapper
export default function AppWithProviders() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <App />
      </AuthProvider>
    </ThemeProvider>
  );
}