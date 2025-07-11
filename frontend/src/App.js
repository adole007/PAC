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
  Sun,
  X
} from 'lucide-react';

// Smart backend URL detection with automatic local detection
let BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001'; // Use env var or local
let API = `${BACKEND_URL}/api`;

// Function to check if local backend is running
const checkLocalBackend = async () => {
  // Always check for local backend (not just in development)
  console.log('🔍 Checking for local backend at http://localhost:8001/health...');
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000); // 2 second timeout
    
    const response = await fetch('http://localhost:8001/health', {
      signal: controller.signal,
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      const healthData = await response.json();
      console.log('🔧 Local backend detected and running at http://localhost:8001');
      console.log('🔧 Health check response:', healthData);
      return true;
    } else {
      console.log('🌐 Local backend responded with error:', response.status, response.statusText);
    }
  } catch (error) {
    // Local backend not running or not responding
    console.log('🌐 Local backend not detected, using production backend');
    console.log('🌐 Health check error:', error.message);
  }
  
  return false;
};

// Initialize backend URL (simplified)
const initializeBackend = async () => {
  console.log('🔄 Initializing backend URL detection...');
  console.log('🔄 Forced to use LOCAL backend: http://localhost:8001');
  
  BACKEND_URL = 'http://localhost:8001';
  API = `${BACKEND_URL}/api`;
  
  console.log('🔄 ✅ Final API URL:', API);
  return BACKEND_URL;
};

// Export functions to get the current URLs
const getApiUrl = () => API;
const getBackendUrl = () => BACKEND_URL;

// Debug function to log current URLs
const logCurrentUrls = () => {
  console.log('Current BACKEND_URL:', BACKEND_URL);
  console.log('Current API URL:', API);
};

// Make these available globally for debugging
window.PAC_DEBUG = {
  getApiUrl,
  getBackendUrl,
  logCurrentUrls,
  initializeBackend,
  checkLocalBackend
};

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
  const [backendInitialized, setBackendInitialized] = useState(false);

  useEffect(() => {
    const initializeApp = async () => {
      // First, detect and set the correct backend URL
      await initializeBackend();
      setBackendInitialized(true);
      
      // Then proceed with authentication
      const token = localStorage.getItem('token');
      if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        fetchCurrentUser();
      } else {
        setLoading(false);
      }
    };
    
    initializeApp();
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(`${getApiUrl()}/auth/me`);
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
      const response = await axios.post(`${getApiUrl()}/auth/login`, { username, password });
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
    { id: 'examinations', label: 'Examinations', icon: ImageIcon },
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

// ThumbnailImage Component
const ThumbnailImage = ({ imageId, thumbnailData, className }) => {
  const [imageSrc, setImageSrc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const loadThumbnail = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        // Fallback to base64 if no token
        setImageSrc(`data:image/png;base64,${thumbnailData}`);
        setLoading(false);
        return;
      }

      try {
        // Choose endpoint based on backend type
        const isLocalBackend = API.includes('localhost');
        const endpoint = isLocalBackend ? '/thumbnail' : '/thumbnail-base64';
        const thumbnailUrl = `${API}/images/${imageId}${endpoint}`;
        
        const response = await fetch(thumbnailUrl, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            // Base64 endpoint returns JSON
            const data = await response.json();
            if (data.format === 'base64') {
              setImageSrc(`data:${data.media_type};base64,${data.thumbnail_data}`);
            }
          } else {
            // Binary endpoint returns blob
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            setImageSrc(url);
            
            // Clean up the URL when component unmounts
            return () => URL.revokeObjectURL(url);
          }
        } else {
          throw new Error('Failed to load thumbnail');
        }
      } catch (err) {
        console.error('Error loading thumbnail:', err);
        // Fallback to base64 if endpoint fails
        setImageSrc(`data:image/png;base64,${thumbnailData}`);
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    loadThumbnail();
  }, [imageId, thumbnailData]);

  if (loading) {
    return (
      <div className={`${className} bg-gray-200 animate-pulse flex items-center justify-center`}>
        <ImageIcon className="w-4 h-4 text-gray-400" />
      </div>
    );
  }

  return (
    <img
      src={imageSrc}
      alt="Thumbnail"
      className={className}
      onError={() => {
        if (!error) {
          // Final fallback to base64 if everything fails
          setImageSrc(`data:image/png;base64,${thumbnailData}`);
          setError(true);
        }
      }}
    />
  );
};

// Patient Examination View Component  
const PatientExaminationView = () => {
  console.log('🚀 PatientExaminationView component loaded');
  
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [examinations, setExaminations] = useState([]);
  const [selectedExamination, setSelectedExamination] = useState(null);
  const [examinationImages, setExaminationImages] = useState([]);
  const [examinationReports, setExaminationReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showExaminationModal, setShowExaminationModal] = useState(false);
  const [showImageViewer, setShowImageViewer] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  
  useEffect(() => {
    console.log('🔄 useEffect triggered - fetching patients');
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    console.log('📡 fetchPatients called');
    try {
      const response = await axios.get(`${getApiUrl()}/patients`);
      console.log('✅ fetchPatients success:', response.data);
      setPatients(response.data);
    } catch (error) {
      console.error('❌ fetchPatients error:', error);
      toast.error('Failed to fetch patients');
    } finally {
      setLoading(false);
    }
  };

  const fetchPatientExaminations = async (patientId) => {
    console.log('🔍 fetchPatientExaminations called with patientId:', patientId);
    try {
      // Get token and API URL
      const token = localStorage.getItem('token');
      const apiUrl = getApiUrl();
      
      console.log('🔑 Token exists:', !!token);
      console.log('🌐 API URL:', apiUrl);
      
      if (!token) {
        console.error('❌ No authentication token found');
        toast.error('Authentication required. Please login again.');
        return;
      }
      
      const fullUrl = `${apiUrl}/patients/${patientId}/examinations`;
      console.log('📡 Full URL:', fullUrl);
      
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      console.log('📋 Headers prepared:', Object.keys(headers));
      
      console.log('🚀 Making axios GET request...');
      
      // Add a small delay to ensure everything is ready
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Use axios with explicit configuration
      const response = await axios({
        method: 'GET',
        url: fullUrl,
        headers: headers,
        timeout: 10000,
        validateStatus: function (status) {
          return status >= 200 && status < 300;
        }
      });
      
      console.log('✅ Response received:', {
        status: response.status,
        dataLength: response.data?.length,
        firstExam: response.data?.[0]?.examination_type
      });
      
      if (response.data && Array.isArray(response.data)) {
        setExaminations(response.data);
        console.log('📊 Examinations set in state:', response.data.length);
      } else {
        console.error('❌ Invalid response data format:', response.data);
        toast.error('Invalid examination data received');
      }
      
    } catch (error) {
      console.error('❌ Error in fetchPatientExaminations:', error);
      
      if (error.response) {
        console.error('❌ Response error:', {
          status: error.response.status,
          statusText: error.response.statusText,
          data: error.response.data
        });
        
        if (error.response.status === 401) {
          toast.error('Authentication failed. Please login again.');
        } else if (error.response.status === 404) {
          toast.error('Patient examinations not found.');
        } else {
          toast.error(`Server error: ${error.response.status} ${error.response.statusText}`);
        }
      } else if (error.request) {
        console.error('❌ Network error:', error.request);
        toast.error('Network error. Please check your connection.');
      } else {
        console.error('❌ Unknown error:', error.message);
        toast.error('Failed to fetch patient examinations');
      }
    }
  };

  const fetchExaminationDetails = async (examinationId) => {
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      // Fetch examination images
      const imagesResponse = await axios.get(`${getApiUrl()}/examinations/${examinationId}/images`, { headers });
      setExaminationImages(imagesResponse.data);

      // Fetch examination reports
      const reportsResponse = await axios.get(`${getApiUrl()}/examinations/${examinationId}/reports`, { headers });
      setExaminationReports(reportsResponse.data);
    } catch (error) {
      console.error('Error fetching examination details:', error);
      toast.error('Failed to fetch examination details');
    }
  };

  const handlePatientClick = async (patient) => {
    console.log('👤 handlePatientClick called with patient:', patient);
    try {
      setSelectedPatient(patient);
      console.log('📋 Selected patient set in state');
      
      console.log('🔄 Fetching patient examinations...');
      await fetchPatientExaminations(patient.id);
      
      console.log('🎭 Opening examination modal...');
      setShowExaminationModal(true);
      console.log('✅ Modal should be open now');
    } catch (error) {
      console.error('❌ Error in handlePatientClick:', error);
      toast.error('Error opening patient examinations');
    }
  };

  const handleExaminationClick = async (examination) => {
    setSelectedExamination(examination);
    await fetchExaminationDetails(examination.id);
  };

  const handleImageClick = (image) => {
    setSelectedImage(image);
    setShowImageViewer(true);
  };

  const closeExaminationModal = () => {
    setShowExaminationModal(false);
    setSelectedPatient(null);
    setExaminations([]);
    setSelectedExamination(null);
    setExaminationImages([]);
    setExaminationReports([]);
  };

  const filteredPatients = patients.filter(patient =>
    patient.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    patient.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    patient.patient_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    patient.medical_record_number.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatTime = (timeString) => {
    return new Date(`2000-01-01T${timeString}`).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading patients...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Patient Examination Management</h1>
        <p className="text-gray-600 mt-2">Click on a patient to view their examinations and medical imaging history</p>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search patients by name, ID, or medical record number..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Patients Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredPatients.map((patient) => (
          <div
            key={patient.id}
            onClick={(e) => {
              console.log('🎯 PATIENT CARD CLICKED!', patient.first_name, patient.last_name);
              e.preventDefault();
              e.stopPropagation();
              handlePatientClick(patient);
            }}
            className="bg-white rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow border-l-4 border-blue-500 hover:border-blue-600"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-800">
                  {patient.first_name} {patient.last_name}
                </h3>
                <p className="text-sm text-gray-600 mt-1">ID: {patient.patient_id}</p>
                <p className="text-sm text-gray-600">MRN: {patient.medical_record_number}</p>
                <p className="text-sm text-gray-600">DOB: {formatDate(patient.date_of_birth)}</p>
                <p className="text-sm text-gray-600">Gender: {patient.gender}</p>
              </div>
              <div className="ml-4">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <User className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-200">
              <button className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center">
                View Examinations
                <Eye className="w-4 h-4 ml-1" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredPatients.length === 0 && (
        <div className="text-center py-12">
          <Search className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No patients found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm ? 'Try adjusting your search terms.' : 'No patients available.'}
          </p>
        </div>
      )}

      {/* Examination Modal */}
      {showExaminationModal && selectedPatient && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-800">
                Examinations for {selectedPatient.first_name} {selectedPatient.last_name}
              </h2>
              <button
                onClick={closeExaminationModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <div className="flex h-[calc(90vh-120px)]">
              {/* Examinations List */}
              <div className="w-1/2 border-r border-gray-200 p-6 overflow-y-auto">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Examinations</h3>
                {examinations.length === 0 ? (
                  <p className="text-gray-500">No examinations found for this patient.</p>
                ) : (
                  <div className="space-y-4">
                    {examinations.map((examination) => (
                      <div
                        key={examination.id}
                        onClick={() => handleExaminationClick(examination)}
                        className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                          selectedExamination?.id === examination.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-medium text-gray-800">{examination.examination_type}</h4>
                            <p className="text-sm text-gray-600 mt-1">{examination.body_part_examined}</p>
                            <p className="text-sm text-gray-600">
                              {formatDate(examination.examination_date)} at {formatTime(examination.examination_time)}
                            </p>
                            <div className="mt-2 flex items-center space-x-4">
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                {examination.device_type}
                              </span>
                              <span className="text-xs text-gray-500">
                                {examination.image_count} images
                              </span>
                              {examination.has_reports && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  {examination.report_count} reports
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="mt-3 text-sm text-gray-600">
                          <p><span className="font-medium">Device:</span> {examination.device_name}</p>
                          <p><span className="font-medium">Location:</span> {examination.device_location}</p>
                          <p><span className="font-medium">Technologist:</span> {examination.technologist_name}</p>
                          <p><span className="font-medium">Physician:</span> {examination.performing_physician}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Examination Details */}
              <div className="w-1/2 p-6 overflow-y-auto">
                {selectedExamination ? (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800 mb-4">Examination Details</h3>
                    
                    {/* Examination Info */}
                    <div className="bg-gray-50 rounded-lg p-4 mb-6">
                      <h4 className="font-medium text-gray-800 mb-2">Examination Information</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-gray-600">Type:</span>
                          <p>{selectedExamination.examination_type}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Body Part:</span>
                          <p>{selectedExamination.body_part_examined}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Date & Time:</span>
                          <p>{formatDate(selectedExamination.examination_date)} at {formatTime(selectedExamination.examination_time)}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Status:</span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            selectedExamination.status === 'completed' ? 'bg-green-100 text-green-800' :
                            selectedExamination.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {selectedExamination.status}
                          </span>
                        </div>
                        <div className="col-span-2">
                          <span className="font-medium text-gray-600">Clinical Indication:</span>
                          <p className="mt-1">{selectedExamination.clinical_indication}</p>
                        </div>
                      </div>
                    </div>

                    {/* Technologist Info */}
                    <div className="bg-green-50 rounded-lg p-4 mb-6">
                      <h4 className="font-medium text-gray-800 mb-2">Technologist Information</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-gray-600">Technologist:</span>
                          <p>{selectedExamination.technologist_name}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Specialization:</span>
                          <p>{selectedExamination.technologist_specialization}</p>
                        </div>
                        <div className="col-span-2">
                          <span className="font-medium text-gray-600">Certification:</span>
                          <p>{selectedExamination.technologist_certification}</p>
                        </div>
                      </div>
                    </div>

                    {/* Device Info */}
                    <div className="bg-blue-50 rounded-lg p-4 mb-6">
                      <h4 className="font-medium text-gray-800 mb-2">Device Information</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-gray-600">Device:</span>
                          <p>{selectedExamination.device_name}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Model:</span>
                          <p>{selectedExamination.device_model}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Manufacturer:</span>
                          <p>{selectedExamination.device_manufacturer}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Location:</span>
                          <p>{selectedExamination.device_location}</p>
                        </div>
                      </div>
                    </div>

                    {/* Images */}
                    <div className="mb-6">
                      <h4 className="font-medium text-gray-800 mb-3">Images ({examinationImages.length})</h4>
                      {examinationImages.length > 0 ? (
                        <div className="grid grid-cols-2 gap-3">
                          {examinationImages.map((image) => (
                            <div
                              key={image.id}
                              onClick={() => handleImageClick(image)}
                              className="border border-gray-200 rounded-lg p-3 cursor-pointer hover:border-blue-500 hover:shadow-md transition-all"
                            >
                              <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                                  <ImageIcon className="w-5 h-5 text-gray-600" />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium text-gray-800 truncate">
                                    {image.original_filename}
                                  </p>
                                  <p className="text-xs text-gray-500">
                                    {image.modality} • {formatDate(image.study_date)}
                                  </p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-500 text-sm">No images available for this examination.</p>
                      )}
                    </div>

                    {/* Reports */}
                    <div>
                      <h4 className="font-medium text-gray-800 mb-3">Reports ({examinationReports.length})</h4>
                      {examinationReports.length > 0 ? (
                        <div className="space-y-3">
                          {examinationReports.map((report) => (
                            <div key={report.id} className="border border-gray-200 rounded-lg p-4">
                              <div className="flex items-center justify-between mb-2">
                                <h5 className="font-medium text-gray-800 capitalize">{report.report_type} Report</h5>
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  report.report_status === 'signed' ? 'bg-green-100 text-green-800' :
                                  report.report_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-gray-100 text-gray-800'
                                }`}>
                                  {report.report_status}
                                </span>
                              </div>
                              <p className="text-sm text-gray-600 mb-2">
                                <span className="font-medium">Physician:</span> {report.reporting_physician}
                              </p>
                              <div className="text-sm">
                                <div className="mb-2">
                                  <span className="font-medium text-gray-700">Findings:</span>
                                  <p className="mt-1 text-gray-600">{report.findings}</p>
                                </div>
                                <div className="mb-2">
                                  <span className="font-medium text-gray-700">Impression:</span>
                                  <p className="mt-1 text-gray-600">{report.impression}</p>
                                </div>
                                <div>
                                  <span className="font-medium text-gray-700">Recommendations:</span>
                                  <p className="mt-1 text-gray-600">{report.recommendations}</p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-500 text-sm">No reports available for this examination.</p>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center text-gray-500">
                      <ImageIcon className="mx-auto h-12 w-12 text-gray-400" />
                      <h3 className="mt-2 text-sm font-medium text-gray-900">Select an examination</h3>
                      <p className="mt-1 text-sm text-gray-500">
                        Choose an examination from the list to view details, images, and reports.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Image Viewer Modal */}
      {showImageViewer && selectedImage && (
        <div className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50">
          <div className="relative max-w-4xl max-h-4xl w-full h-full p-4">
            <button
              onClick={() => setShowImageViewer(false)}
              className="absolute top-4 right-4 text-white hover:text-gray-300 z-10"
            >
              <X className="w-8 h-8" />
            </button>
            <div className="bg-white rounded-lg p-4 h-full flex flex-col">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-800">{selectedImage.original_filename}</h3>
                <p className="text-sm text-gray-600">
                  {selectedImage.modality} • {selectedImage.body_part} • {formatDate(selectedImage.study_date)}
                </p>
              </div>
              <div className="flex-1 bg-gray-100 rounded-lg flex items-center justify-center">
                <p className="text-gray-500">Image viewer would be integrated here</p>
                {/* This is where you would integrate with the existing MedicalImageViewer component */}
              </div>
            </div>
          </div>
        </div>
      )}
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
  const [patientImageCounts, setPatientImageCounts] = useState({});
  const [showQuickUpload, setShowQuickUpload] = useState(false);
  const [quickUploadPatient, setQuickUploadPatient] = useState(null);
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

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${getApiUrl()}/patients`);
      setPatients(response.data);
      // Fetch image counts for each patient
      await fetchPatientImageCounts(response.data);
    } catch (error) {
      toast.error('Failed to fetch patients');
    } finally {
      setLoading(false);
    }
  };

  const fetchPatientImageCounts = async (patientList) => {
    const counts = {};
    try {
      // Fetch image counts for all patients
      for (const patient of patientList) {
        try {
          const response = await axios.get(`${getApiUrl()}/patients/${patient.id}/images`);
          counts[patient.id] = response.data.length;
        } catch (error) {
          // If patient has no images or endpoint fails, set count to 0
          counts[patient.id] = 0;
        }
      }
      setPatientImageCounts(counts);
    } catch (error) {
      console.error('Failed to fetch patient image counts:', error);
    }
  };

  const handleQuickUpload = (patient) => {
    setQuickUploadPatient(patient);
    setShowQuickUpload(true);
  };

  const handleQuickUploadComplete = () => {
    setShowQuickUpload(false);
    setQuickUploadPatient(null);
    // Refresh patient data to update image counts
    fetchPatients();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingPatient) {
        await axios.put(`${getApiUrl()}/patients/${editingPatient.id}`, formData);
        toast.success('Patient updated successfully');
      } else {
        await axios.post(`${getApiUrl()}/patients`, formData);
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
        await axios.delete(`${getApiUrl()}/patients/${patientId}`);
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
                  Image Status
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
              {filteredPatientsForManagement.map((patient) => {
                const imageCount = patientImageCounts[patient.id] || 0;
                const hasImages = imageCount > 0;
                
                return (
                  <tr key={patient.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {patient.patient_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center space-x-3">
                        {/* Status Indicator */}
                        <div className={`w-3 h-3 rounded-full ${
                          hasImages ? 'bg-green-500' : 'bg-red-500'
                        }`} title={hasImages ? `${imageCount} images uploaded` : 'No images uploaded'}></div>
                        
                        {/* Image Count Badge */}
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          hasImages 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {imageCount} {imageCount === 1 ? 'image' : 'images'}
                        </span>
                        
                        {/* Quick Upload Button */}
                        <button
                          onClick={() => handleQuickUpload(patient)}
                          className="inline-flex items-center px-2 py-1 text-xs font-medium text-blue-600 bg-blue-100 rounded-md hover:bg-blue-200 transition-colors"
                          title="Quick upload images for this patient"
                        >
                          <Upload className="w-3 h-3 mr-1" />
                          Upload
                        </button>
                      </div>
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
                );
              })}
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

      {/* Quick Upload Modal */}
      {showQuickUpload && quickUploadPatient && (
        <QuickUploadModal 
          patient={quickUploadPatient}
          onClose={() => setShowQuickUpload(false)}
          onComplete={handleQuickUploadComplete}
        />
      )}
    </div>
  );
};

// Quick Upload Modal Component
const QuickUploadModal = ({ patient, onClose, onComplete }) => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadData, setUploadData] = useState({
    study_id: `STUDY_${Date.now()}`,
    series_id: `SERIES_${Date.now()}`,
    modality: 'CT',
    body_part: 'CHEST',
    study_date: new Date().toISOString().split('T')[0],
    study_time: new Date().toTimeString().split(' ')[0],
    institution_name: 'Jajuwa Healthcare',
    referring_physician: 'Dr. System'
  });

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(files);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      toast.error('Please select at least one file');
      return;
    }

    setUploading(true);
    let successCount = 0;
    let failureCount = 0;
    
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

        console.log('QuickUpload: Uploading file:', file.name, 'to patient:', patient.id);
        console.log('QuickUpload: Upload data:', {
          modality: uploadData.modality,
          body_part: uploadData.body_part,
          study_id: uploadData.study_id,
          series_id: uploadData.series_id,
          study_date: uploadData.study_date,
          study_time: uploadData.study_time,
          institution_name: uploadData.institution_name,
          referring_physician: uploadData.referring_physician
        });
        console.log('QuickUpload: File will be processed by backend image conversion algorithm');
        
        const token = localStorage.getItem('token');
        const headers = {
          'Content-Type': 'multipart/form-data'
        };
        
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await axios.post(`${getApiUrl()}/patients/${patient.id}/images`, formData, {
          headers
        });
        
        console.log('QuickUpload: Backend processed file successfully:', response.data);
        toast.success(`${file.name} uploaded successfully`);
        successCount++;
      } catch (error) {
        console.error('QuickUpload error for file:', file.name, error);
        console.error('QuickUpload error response:', error.response?.data);
        
        let errorMessage = 'Unknown error';
        if (error.response?.data?.detail) {
          if (Array.isArray(error.response.data.detail)) {
            // Handle validation error array
            errorMessage = error.response.data.detail.map(err => 
              `${err.loc?.join('.')} ${err.msg}`
            ).join(', ');
          } else {
            errorMessage = error.response.data.detail;
          }
        } else if (error.response?.status === 401) {
          errorMessage = 'Authentication failed. Please login again.';
        } else if (error.response?.status === 404) {
          errorMessage = 'Patient not found';
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        toast.error(`Failed to upload ${file.name}: ${errorMessage}`);
        failureCount++;
      }
    }
    
    setUploading(false);
    
    // Provide comprehensive feedback
    if (successCount > 0 && failureCount === 0) {
      toast.success(`All ${successCount} image(s) uploaded successfully!`);
    } else if (successCount > 0 && failureCount > 0) {
      toast.warning(`${successCount} image(s) uploaded, ${failureCount} failed`);
    } else if (failureCount > 0) {
      toast.error(`All ${failureCount} image(s) failed to upload`);
    }
    
    // Close modal and refresh data if any uploads succeeded
    if (successCount > 0) {
      onComplete();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-800">
              Quick Upload for {patient.first_name} {patient.last_name}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Patient ID: {patient.patient_id}
          </p>
        </div>
        
        <div className="p-6 space-y-4">
          {/* File Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Medical Images
            </label>
            <input
              type="file"
              multiple
              accept=".dcm,.jpg,.jpeg,.png,.tiff,.tif"
              onChange={handleFileSelect}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">
              Supported formats: DICOM (.dcm), JPEG, PNG, TIFF
            </p>
          </div>

          {/* Quick Settings */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Modality
              </label>
              <select
                value={uploadData.modality}
                onChange={(e) => setUploadData({...uploadData, modality: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="CT">CT</option>
                <option value="MRI">MRI</option>
                <option value="X-Ray">X-Ray</option>
                <option value="Ultrasound">Ultrasound</option>
                <option value="PET">PET</option>
                <option value="Mammography">Mammography</option>
                <option value="Nuclear Medicine">Nuclear Medicine</option>
                <option value="MR">MR</option>
                <option value="XR">XR</option>
                <option value="US">US</option>
                <option value="CR">CR</option>
                <option value="DR">DR</option>
                <option value="DX">DX</option>
                <option value="RF">RF</option>
                <option value="NM">NM</option>
                <option value="PT">PT</option>
                <option value="SC">SC</option>
                <option value="OT">OT</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Body Part
              </label>
              <select
                value={uploadData.body_part}
                onChange={(e) => setUploadData({...uploadData, body_part: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="CHEST">Chest</option>
                <option value="ABDOMEN">Abdomen</option>
                <option value="HEAD">Head</option>
                <option value="PELVIS">Pelvis</option>
                <option value="SPINE">Spine</option>
                <option value="EXTREMITY">Extremity</option>
              </select>
            </div>
          </div>

          {/* Selected Files Preview */}
          {selectedFiles.length > 0 && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">
                Selected Files ({selectedFiles.length}):
              </p>
              <div className="max-h-32 overflow-y-auto bg-gray-50 rounded-lg p-2">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="text-xs text-gray-600 py-1">
                    {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="flex justify-end space-x-3 p-6 border-t">
          <button
            onClick={onClose}
            disabled={uploading}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={uploading || selectedFiles.length === 0}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
          >
            {uploading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Uploading...</span>
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                <span>Upload Images</span>
              </>
            )}
          </button>
        </div>
      </div>
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
      const response = await axios.get(`${getApiUrl()}/patients`);
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

    // Validate required fields
    const missingFields = [];
    if (!uploadData.study_id) missingFields.push('Study ID');
    if (!uploadData.series_id) missingFields.push('Series ID');
    if (!uploadData.modality) missingFields.push('Modality');
    if (!uploadData.body_part) missingFields.push('Body Part');
    if (!uploadData.study_date) missingFields.push('Study Date');
    if (!uploadData.study_time) missingFields.push('Study Time');
    if (!uploadData.institution_name) missingFields.push('Institution Name');
    if (!uploadData.referring_physician) missingFields.push('Referring Physician');
    
    if (missingFields.length > 0) {
      toast.error(`Please fill in these required fields: ${missingFields.join(', ')}`);
      return;
    }

    setUploading(true);
    let successCount = 0;
    let failureCount = 0;
    
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

        console.log('Uploading file:', file.name);
        console.log('To patient ID:', selectedPatient);
        console.log('Upload data:', uploadData);
        
        const response = await axios.post(`${API}/patients/${selectedPatient}/images`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        console.log('Upload response:', response.data);
        toast.success(`${file.name} uploaded successfully`);
        successCount++;
      } catch (error) {
        console.error('Upload error:', error);
        console.error('Error response:', error.response?.data);
        
        let errorMessage = 'Unknown error';
        if (error.response?.data?.detail) {
          if (Array.isArray(error.response.data.detail)) {
            // Handle validation error array
            errorMessage = error.response.data.detail.map(err => 
              `${err.loc?.join('.')} ${err.msg}`
            ).join(', ');
          } else {
            errorMessage = error.response.data.detail;
          }
        } else if (error.response?.status === 401) {
          errorMessage = 'Authentication failed. Please login again.';
        } else if (error.response?.status === 404) {
          errorMessage = 'Patient not found';
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        toast.error(`Failed to upload ${file.name}: ${errorMessage}`);
        failureCount++;
      }
    }
    
    setUploading(false);
    
    if (successCount > 0) {
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
    }
    
    if (successCount > 0 && failureCount === 0) {
      toast.success(`All ${successCount} files uploaded successfully!`);
    } else if (successCount > 0 && failureCount > 0) {
      toast.warning(`${successCount} files uploaded, ${failureCount} failed`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Upload Medical Images</h1>
      </div>

      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="mb-4 p-4 bg-blue-50 rounded-lg">
          <h3 className="text-sm font-medium text-blue-800 mb-2">Upload Instructions:</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Select a patient from the dropdown</li>
            <li>• Fill in all required fields (marked with *)</li>
            <li>• Choose one or more image files</li>
            <li>• Supported formats: DICOM (.dcm), JPEG, PNG, TIFF</li>
          </ul>
        </div>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Patient *
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
                Study ID *
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
  // Save Annotated Image
  const handleSaveAnnotatedImage = () => {
    const mainCanvas = canvasRef.current;
    const overlayCanvas = overlayCanvasRef.current;
    
    if (!mainCanvas || !overlayCanvas || !selectedImage) {
      toast.error('No image selected or canvas not available');
      return;
    }

    // Create a temporary canvas to combine the main image and annotations
    const combinedCanvas = document.createElement('canvas');
    const combinedCtx = combinedCanvas.getContext('2d');
    
    // Set the combined canvas size to match the main canvas
    combinedCanvas.width = mainCanvas.width;
    combinedCanvas.height = mainCanvas.height;
    
    // Draw the main image first
    combinedCtx.drawImage(mainCanvas, 0, 0);
    
    // Draw the annotations on top
    combinedCtx.drawImage(overlayCanvas, 0, 0);
    
    // Convert to blob and trigger download
    combinedCanvas.toBlob((blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Create a more descriptive filename
      const patient = patients.find(p => p.id === selectedPatient);
      const patientName = patient ? `${patient.first_name}_${patient.last_name}` : 'Unknown';
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const filename = `${patientName}_${selectedImage.modality}_${selectedImage.body_part}_${timestamp}.png`;
      
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      
      toast.success('Annotated image saved successfully!');
    }, 'image/png');
  };
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
  
  // Performance optimization states
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const processingCacheRef = useRef(new Map());
  const workerRef = useRef(null);
  const processingQueueRef = useRef([]);
  const processingIdRef = useRef(0);
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

  // Filter patients based on search term for Medical Image Viewer
  const filteredPatientsForViewer = patients.filter(patient => {
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

  // Initialize Web Worker for image processing
  useEffect(() => {
    console.log('Initializing Web Worker for image processing...');
    if (typeof Worker !== 'undefined') {
      try {
        workerRef.current = new Worker('/imageProcessingWorker.js');
        console.log('Web Worker created successfully');
        
        workerRef.current.onmessage = (e) => {
          const { type, processingId, result, error } = e.data;
          console.log('Worker message received:', { type, processingId, hasResult: !!result, error });
          
          if (type === 'processingComplete') {
            const queueIndex = processingQueueRef.current.findIndex(item => item.id === processingId);
            if (queueIndex !== -1) {
              const { resolve, cacheKey } = processingQueueRef.current[queueIndex];
              processingQueueRef.current.splice(queueIndex, 1);
              
              // Cache the result
              processingCacheRef.current.set(cacheKey, result);
              
              resolve(result);
              
              // Update processing state
              setIsProcessing(processingQueueRef.current.length > 0);
              setProcessingProgress(0);
              console.log('Processing completed successfully for ID:', processingId);
            }
          } else if (type === 'processingError') {
            const queueIndex = processingQueueRef.current.findIndex(item => item.id === processingId);
            if (queueIndex !== -1) {
              const { reject } = processingQueueRef.current[queueIndex];
              processingQueueRef.current.splice(queueIndex, 1);
              
              reject(new Error(error));
              
              setIsProcessing(processingQueueRef.current.length > 0);
              setProcessingProgress(0);
              console.error('Processing failed for ID:', processingId, 'Error:', error);
            }
          }
        };
        
        workerRef.current.onerror = (error) => {
          console.error('Worker error:', error);
        };
      } catch (error) {
        console.error('Failed to create Web Worker:', error);
      }
    } else {
      console.error('Web Workers not supported in this environment');
    }
    
    return () => {
      if (workerRef.current) {
        console.log('Terminating Web Worker');
        workerRef.current.terminate();
      }
    };
  }, []);
  
  useEffect(() => {
    fetchPatients();
  }, []);

  useEffect(() => {
    if (selectedPatient) {
      fetchPatientImages();
    }
  }, [selectedPatient]);

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
      const response = await axios.get(`${getApiUrl()}/patients`);
      setPatients(response.data);
    } catch (error) {
      toast.error('Failed to fetch patients');
    }
  };

  const fetchPatientImages = async () => {
    try {
      const response = await axios.get(`${getApiUrl()}/patients/${selectedPatient}/images`);
      setPatientImages(response.data);
    } catch (error) {
      toast.error('Failed to fetch patient images');
    }
  };

  // Optimized image processing function with Web Worker
  const processImageWithWorker = async (type, imageData, params) => {
    if (!workerRef.current) {
      throw new Error('Web Worker not available');
    }
    
    // Generate cache key
    const cacheKey = `${type}-${JSON.stringify(params)}-${selectedImage?.id}`;
    
    // Check cache first
    if (processingCacheRef.current.has(cacheKey)) {
      return processingCacheRef.current.get(cacheKey);
    }
    
    return new Promise((resolve, reject) => {
      const processingId = processingIdRef.current++;
      
      // Add to processing queue
      processingQueueRef.current.push({
        id: processingId,
        resolve,
        reject,
        cacheKey
      });
      
      // Update processing state
      setIsProcessing(true);
      setProcessingProgress(25);
      
      // Send to worker
      workerRef.current.postMessage({
        type,
        imageData: {
          data: imageData.data,
          width: imageData.width,
          height: imageData.height
        },
        params,
        processingId
      });
      
      // Set timeout for long-running operations
      setTimeout(() => {
        const queueIndex = processingQueueRef.current.findIndex(item => item.id === processingId);
        if (queueIndex !== -1) {
          processingQueueRef.current.splice(queueIndex, 1);
          setIsProcessing(false);
          setProcessingProgress(0);
          reject(new Error('Processing timeout'));
        }
      }, 10000); // 10 second timeout
    });
  };
  
  // Advanced image processing functions
  const applyGaussianFilter = (imageData, sigma) => {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    const output = new Uint8ClampedArray(data);
    
    // Generate Gaussian kernel
    const kernelSize = Math.ceil(sigma * 3) * 2 + 1;
    const kernel = [];
    const center = Math.floor(kernelSize / 2);
    let sum = 0;
    
    for (let i = 0; i < kernelSize; i++) {
      kernel[i] = [];
      for (let j = 0; j < kernelSize; j++) {
        const x = i - center;
        const y = j - center;
        const value = Math.exp(-(x * x + y * y) / (2 * sigma * sigma));
        kernel[i][j] = value;
        sum += value;
      }
    }
    
    // Normalize kernel
    for (let i = 0; i < kernelSize; i++) {
      for (let j = 0; j < kernelSize; j++) {
        kernel[i][j] /= sum;
      }
    }
    
    // Apply Gaussian filter
    for (let y = center; y < height - center; y++) {
      for (let x = center; x < width - center; x++) {
        let r = 0, g = 0, b = 0;
        
        for (let ky = 0; ky < kernelSize; ky++) {
          for (let kx = 0; kx < kernelSize; kx++) {
            const py = y + ky - center;
            const px = x + kx - center;
            const idx = (py * width + px) * 4;
            const weight = kernel[ky][kx];
            
            r += data[idx] * weight;
            g += data[idx + 1] * weight;
            b += data[idx + 2] * weight;
          }
        }
        
        const outputIdx = (y * width + x) * 4;
        output[outputIdx] = Math.round(r);
        output[outputIdx + 1] = Math.round(g);
        output[outputIdx + 2] = Math.round(b);
      }
    }
    
    // Copy back to original
    for (let i = 0; i < data.length; i++) {
      data[i] = output[i];
    }
    
    return imageData;
  };

  const applyBilateralFilter = (imageData, spatialSigma, colorSigma) => {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    const output = new Uint8ClampedArray(data);
    
    const kernelRadius = Math.ceil(spatialSigma * 2);
    
    for (let y = kernelRadius; y < height - kernelRadius; y++) {
      for (let x = kernelRadius; x < width - kernelRadius; x++) {
        const centerIdx = (y * width + x) * 4;
        const centerR = data[centerIdx];
        const centerG = data[centerIdx + 1];
        const centerB = data[centerIdx + 2];
        
        let sumR = 0, sumG = 0, sumB = 0;
        let weightSum = 0;
        
        for (let dy = -kernelRadius; dy <= kernelRadius; dy++) {
          for (let dx = -kernelRadius; dx <= kernelRadius; dx++) {
            const ny = y + dy;
            const nx = x + dx;
            const nIdx = (ny * width + nx) * 4;
            
            // Spatial weight (Gaussian based on distance)
            const spatialDist = dx * dx + dy * dy;
            const spatialWeight = Math.exp(-spatialDist / (2 * spatialSigma * spatialSigma));
            
            // Color weight (Gaussian based on color difference)
            const colorDist = Math.pow(data[nIdx] - centerR, 2) + 
                             Math.pow(data[nIdx + 1] - centerG, 2) + 
                             Math.pow(data[nIdx + 2] - centerB, 2);
            const colorWeight = Math.exp(-colorDist / (2 * colorSigma * colorSigma));
            
            const weight = spatialWeight * colorWeight;
            
            sumR += data[nIdx] * weight;
            sumG += data[nIdx + 1] * weight;
            sumB += data[nIdx + 2] * weight;
            weightSum += weight;
          }
        }
        
        output[centerIdx] = Math.round(sumR / weightSum);
        output[centerIdx + 1] = Math.round(sumG / weightSum);
        output[centerIdx + 2] = Math.round(sumB / weightSum);
      }
    }
    
    // Copy back to original
    for (let i = 0; i < data.length; i++) {
      data[i] = output[i];
    }
    
    return imageData;
  };

  const applyNoiseReduction = (imageData, threshold) => {
    if (threshold === 0) return imageData;
    
    // Use bilateral filter for edge-preserving noise reduction
    const spatialSigma = threshold * 3 + 1;
    const colorSigma = threshold * 50 + 10;
    
    // Apply bilateral filtering
    applyBilateralFilter(imageData, spatialSigma, colorSigma);
    
    // Apply additional Gaussian smoothing for strong noise reduction
    if (threshold > 0.5) {
      const gaussianSigma = (threshold - 0.5) * 2;
      applyGaussianFilter(imageData, gaussianSigma);
    }
    
    return imageData;
  };

  const applyAdvancedBoneRemoval = (imageData, intensity) => {
    if (intensity === 0) return imageData;
    
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    
    // Convert to grayscale for processing
    const grayscale = new Array(width * height);
    for (let i = 0; i < data.length; i += 4) {
      const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
      grayscale[i / 4] = gray;
    }
    
    // Calculate local statistics for adaptive thresholding
    const windowSize = 15;
    const halfWindow = Math.floor(windowSize / 2);
    
    for (let y = halfWindow; y < height - halfWindow; y++) {
      for (let x = halfWindow; x < width - halfWindow; x++) {
        const centerIdx = y * width + x;
        const pixelIdx = centerIdx * 4;
        
        // Calculate local mean and standard deviation
        let sum = 0;
        let sumSq = 0;
        let count = 0;
        
        for (let dy = -halfWindow; dy <= halfWindow; dy++) {
          for (let dx = -halfWindow; dx <= halfWindow; dx++) {
            const ny = y + dy;
            const nx = x + dx;
            const nIdx = ny * width + nx;
            const gray = grayscale[nIdx];
            
            sum += gray;
            sumSq += gray * gray;
            count++;
          }
        }
        
        const mean = sum / count;
        const variance = (sumSq / count) - (mean * mean);
        const stdDev = Math.sqrt(Math.max(0, variance));
        
        // Adaptive bone detection threshold
        const adaptiveThreshold = mean + (stdDev * 0.5);
        const currentGray = grayscale[centerIdx];
        
        // Bone suppression based on local statistics
        if (currentGray > adaptiveThreshold) {
          // This pixel is likely bone tissue
          const boneStrength = (currentGray - adaptiveThreshold) / (255 - adaptiveThreshold);
          const suppressionFactor = 1 - (intensity * boneStrength * 0.8);
          
          // Apply morphological opening to preserve edge details
          const edgeEnhancement = Math.min(1, stdDev / 30);
          const finalSuppression = suppressionFactor + (edgeEnhancement * intensity * 0.2);
          
          data[pixelIdx] *= Math.max(0.1, finalSuppression);
          data[pixelIdx + 1] *= Math.max(0.1, finalSuppression);
          data[pixelIdx + 2] *= Math.max(0.1, finalSuppression);
        }
      }
    }
    
    // Apply contrast enhancement to remaining structures
    const contrastBoost = 1 + (intensity * 0.3);
    for (let i = 0; i < data.length; i += 4) {
      const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
      if (gray < 200) { // Don't enhance remaining bright pixels
        data[i] = Math.min(255, data[i] * contrastBoost);
        data[i + 1] = Math.min(255, data[i + 1] * contrastBoost);
        data[i + 2] = Math.min(255, data[i + 2] * contrastBoost);
      }
    }
    
    return imageData;
  };

  const applyAdvancedFleshRemoval = (imageData, intensity) => {
    if (intensity === 0) return imageData;
    
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    
    // Convert to grayscale for analysis
    const grayscale = new Array(width * height);
    for (let i = 0; i < data.length; i += 4) {
      const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
      grayscale[i / 4] = gray;
    }
    
    // Calculate global histogram for adaptive processing
    const histogram = new Array(256).fill(0);
    for (let i = 0; i < grayscale.length; i++) {
      histogram[Math.floor(grayscale[i])]++;
    }
    
    // Find optimal threshold using Otsu's method
    let totalPixels = grayscale.length;
    let sum = 0;
    for (let i = 0; i < 256; i++) {
      sum += i * histogram[i];
    }
    
    let sumB = 0;
    let wB = 0;
    let maximum = 0;
    let optimalThreshold = 0;
    
    for (let i = 0; i < 256; i++) {
      wB += histogram[i];
      if (wB === 0) continue;
      
      let wF = totalPixels - wB;
      if (wF === 0) break;
      
      sumB += i * histogram[i];
      let mB = sumB / wB;
      let mF = (sum - sumB) / wF;
      
      let between = wB * wF * (mB - mF) * (mB - mF);
      
      if (between > maximum) {
        maximum = between;
        optimalThreshold = i;
      }
    }
    
    // Apply advanced soft tissue suppression
    const windowSize = 11;
    const halfWindow = Math.floor(windowSize / 2);
    
    for (let y = halfWindow; y < height - halfWindow; y++) {
      for (let x = halfWindow; x < width - halfWindow; x++) {
        const centerIdx = y * width + x;
        const pixelIdx = centerIdx * 4;
        const currentGray = grayscale[centerIdx];
        
        // Calculate local edge strength
        let edgeStrength = 0;
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            if (dx === 0 && dy === 0) continue;
            const nIdx = (y + dy) * width + (x + dx);
            edgeStrength += Math.abs(grayscale[nIdx] - currentGray);
          }
        }
        edgeStrength /= 8;
        
        // Soft tissue detection (low intensity, low edge strength)
        const tissueThreshold = optimalThreshold + (intensity * 40);
        
        if (currentGray < tissueThreshold && edgeStrength < 20) {
          // This pixel is likely soft tissue
          const tissueStrength = 1 - (currentGray / tissueThreshold);
          const suppressionFactor = 1 - (intensity * tissueStrength * 0.7);
          
          // Preserve edges while suppressing uniform tissue areas
          const edgePreservation = Math.min(1, edgeStrength / 15);
          const finalSuppression = suppressionFactor + (edgePreservation * intensity * 0.3);
          
          data[pixelIdx] *= Math.max(0.15, finalSuppression);
          data[pixelIdx + 1] *= Math.max(0.15, finalSuppression);
          data[pixelIdx + 2] *= Math.max(0.15, finalSuppression);
        } else if (currentGray > tissueThreshold) {
          // Enhance bone/calcification structures
          const enhancementFactor = 1 + (intensity * 0.4);
          data[pixelIdx] = Math.min(255, data[pixelIdx] * enhancementFactor);
          data[pixelIdx + 1] = Math.min(255, data[pixelIdx + 1] * enhancementFactor);
          data[pixelIdx + 2] = Math.min(255, data[pixelIdx + 2] * enhancementFactor);
        }
      }
    }
    
    // Apply final sharpening to enhance remaining structures
    if (intensity > 0.3) {
      const sharpenKernel = [
        [0, -0.5, 0],
        [-0.5, 3, -0.5],
        [0, -0.5, 0]
      ];
      
      const tempData = new Uint8ClampedArray(data);
      
      for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
          const centerIdx = (y * width + x) * 4;
          
          for (let c = 0; c < 3; c++) {
            let sum = 0;
            for (let dy = -1; dy <= 1; dy++) {
              for (let dx = -1; dx <= 1; dx++) {
                const nIdx = ((y + dy) * width + (x + dx)) * 4 + c;
                sum += tempData[nIdx] * sharpenKernel[dy + 1][dx + 1];
              }
            }
            data[centerIdx + c] = Math.max(0, Math.min(255, sum));
          }
        }
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
      
      // Apply advanced image processing if needed (using Web Worker)
      if (viewerState.noiseThreshold > 0 || viewerState.boneRemoval > 0 || viewerState.fleshRemoval > 0) {
        console.log('Advanced processing triggered:', {
          noiseThreshold: viewerState.noiseThreshold,
          boneRemoval: viewerState.boneRemoval,
          fleshRemoval: viewerState.fleshRemoval
        });
        
        try {
          const imageData = ctx.getImageData(drawX, drawY, drawWidth, drawHeight);
          console.log('Image data extracted:', imageData.width, 'x', imageData.height);
          
          // Process with Web Worker for better performance
          const processImage = async () => {
            let processedData = imageData;
            
            if (viewerState.noiseThreshold > 0) {
              console.log('Starting noise reduction with threshold:', viewerState.noiseThreshold);
              processedData = await processImageWithWorker('noiseReduction', processedData, {
                threshold: viewerState.noiseThreshold
              });
              console.log('Noise reduction completed');
            }
            
            if (viewerState.boneRemoval > 0) {
              console.log('Starting bone removal with intensity:', viewerState.boneRemoval);
              processedData = await processImageWithWorker('boneRemoval', processedData, {
                intensity: viewerState.boneRemoval
              });
              console.log('Bone removal completed');
            }
            
            if (viewerState.fleshRemoval > 0) {
              console.log('Starting flesh removal with intensity:', viewerState.fleshRemoval);
              processedData = await processImageWithWorker('fleshRemoval', processedData, {
                intensity: viewerState.fleshRemoval
              });
              console.log('Flesh removal completed');
            }
            
            // Apply processed data back to canvas
            console.log('Applying processed data back to canvas');
            
            // Create a temporary canvas to apply the processed image data
            const tempCanvas = document.createElement('canvas');
            const tempCtx = tempCanvas.getContext('2d');
            tempCanvas.width = processedData.width;
            tempCanvas.height = processedData.height;
            
            // Reconstruct ImageData object if needed
            let finalImageData;
            if (processedData.data && processedData.width && processedData.height) {
              finalImageData = new ImageData(
                new Uint8ClampedArray(processedData.data),
                processedData.width,
                processedData.height
              );
            } else {
              finalImageData = processedData;
            }
            
            // Put the processed data on the temporary canvas
            tempCtx.putImageData(finalImageData, 0, 0);
            
            // Clear the area where the original image was drawn
            ctx.clearRect(drawX, drawY, drawWidth, drawHeight);
            
            // Draw the processed image back with the same dimensions
            ctx.drawImage(tempCanvas, 0, 0, tempCanvas.width, tempCanvas.height, drawX, drawY, drawWidth, drawHeight);
            
            console.log('Advanced processing pipeline completed successfully');
            
            // Restore context state after processing is complete
            ctx.restore();
          };
          
          processImage().catch(error => {
            console.error('Advanced processing failed:', error.message, error.stack);
            // Restore context even if processing fails
            ctx.restore();
          });
          
        } catch (error) {
          console.error('Advanced processing not applied due to canvas restrictions:', error.message);
          // Restore context if processing setup fails
          ctx.restore();
        }
      } else {
        // Restore context state when no processing is needed
        ctx.restore();
      }
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
      
      // Show more detailed error for DICOM images
      if (selectedImage.image_format === 'DICOM') {
        ctx.fillStyle = '#ff6b6b';
        ctx.font = '14px Arial';
        ctx.fillText('DICOM image processing error', canvas.width / 2, canvas.height / 2 + 30);
        ctx.fillText('Check console for details', canvas.width / 2, canvas.height / 2 + 50);
      }
    };
    
    // Set the image source using optimized endpoint selection
    const token = localStorage.getItem('token');
    if (token) {
      // Choose endpoint based on backend type (local vs Vercel)
      const isLocalBackend = getBackendUrl().includes('localhost');
      const endpoint = isLocalBackend ? '/data' : '/data-base64';
      const imageUrl = `${getApiUrl()}/images/${selectedImage.id}${endpoint}`;
      
      console.log('Fetching image from:', imageUrl, '(backend:', isLocalBackend ? 'local' : 'vercel', ')');
      console.log('With token:', token.substring(0, 20) + '...');
      
      fetch(imageUrl, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(response => {
        console.log('Image fetch response:', response.status, response.statusText);
        if (response.ok) {
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            // Base64 endpoint returns JSON
            return response.json();
          } else {
            // Binary endpoint returns blob
            return response.blob();
          }
        } else {
          throw new Error(`Failed to load image: ${response.status} ${response.statusText}`);
        }
      })
      .then(data => {
        if (data.format === 'base64') {
          // Handle base64 data from Vercel endpoint
          console.log('Received base64 data, type:', data.media_type);
          const dataUrl = `data:${data.media_type};base64,${data.image_data}`;
          img.src = dataUrl;
          
          const originalOnload = img.onload;
          img.onload = () => {
            console.log('Image loaded successfully from base64');
            if (originalOnload) originalOnload();
          };
        } else if (data instanceof Blob) {
          // Handle blob data from local endpoint
          console.log('Received blob:', data.size, 'bytes, type:', data.type);
          const url = URL.createObjectURL(data);
          img.src = url;
          
          const originalOnload = img.onload;
          img.onload = () => {
            console.log('Image loaded successfully from blob');
            if (originalOnload) originalOnload();
            URL.revokeObjectURL(url);
          };
        } else {
          console.error('Unexpected data format:', data);
          throw new Error('Unexpected response format');
        }
      })
      .catch(error => {
        console.error('Error loading image:', error);
        
        // Fallback: try the binary endpoint
        console.log('Attempting fallback to binary endpoint...');
        const fallbackUrl = `${getApiUrl()}/images/${selectedImage.id}/data`;
        
        fetch(fallbackUrl, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        .then(response => {
          if (response.ok) {
            return response.blob();
          } else {
            throw new Error('Fallback also failed');
          }
        })
        .then(blob => {
          console.log('Fallback successful - received blob:', blob.size, 'bytes');
          const url = URL.createObjectURL(blob);
          img.src = url;
          
          const originalOnload = img.onload;
          img.onload = () => {
            console.log('Image loaded successfully from fallback');
            if (originalOnload) originalOnload();
            URL.revokeObjectURL(url);
          };
        })
        .catch(fallbackError => {
          console.error('Both endpoints failed:', fallbackError);
          img.onerror();
        });
      });
    } else {
      // No token available - show error message
      console.error('No authentication token available');
      img.onerror();
    }
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

  const handleDownload = async () => {
    if (!selectedImage) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${getApiUrl()}/images/${selectedImage.id}/data`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        // Create a temporary download link
        const link = document.createElement('a');
        link.href = url;
        link.download = selectedImage.original_filename || `${selectedImage.modality}_${selectedImage.body_part}.dcm`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Clean up the URL
        URL.revokeObjectURL(url);
        
        toast.success('Image downloaded successfully!');
      } else {
        throw new Error('Failed to download image');
      }
    } catch (error) {
      console.error('Error downloading image:', error);
      toast.error('Failed to download image');
    }
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
                  {filteredPatientsForViewer.length > 0 ? (
                    filteredPatientsForViewer.map((patient) => (
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
                      <ThumbnailImage 
                        imageId={image.id}
                        thumbnailData={image.thumbnail_data}
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
                      <button
                        onClick={handleDownload}
                        className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                        title="Download Image"
                      >
                        <Download className="w-4 h-4" />
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
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-medium text-gray-700">Advanced Medical Image Processing</h4>
                      {isProcessing && (
                        <div className="flex items-center space-x-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                          <span className="text-xs text-blue-600">Processing...</span>
                        </div>
                      )}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Advanced Noise Reduction: {(viewerState.noiseThreshold * 100).toFixed(0)}%
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.01"
                          value={viewerState.noiseThreshold}
                          onChange={(e) => setViewerState(prev => ({...prev, noiseThreshold: parseFloat(e.target.value)}))}
                          className="w-full"
                          disabled={isProcessing}
                        />
                        <p className="text-xs text-gray-500 mt-1">Bilateral filtering with edge preservation & Gaussian smoothing</p>
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Intelligent Bone Suppression: {(viewerState.boneRemoval * 100).toFixed(0)}%
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.01"
                          value={viewerState.boneRemoval}
                          onChange={(e) => setViewerState(prev => ({...prev, boneRemoval: parseFloat(e.target.value)}))}
                          className="w-full"
                          disabled={isProcessing}
                        />
                        <p className="text-xs text-gray-500 mt-1">Adaptive thresholding with local statistics & morphological operations</p>
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Smart Soft Tissue Removal: {(viewerState.fleshRemoval * 100).toFixed(0)}%
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.01"
                          value={viewerState.fleshRemoval}
                          onChange={(e) => setViewerState(prev => ({...prev, fleshRemoval: parseFloat(e.target.value)}))}
                          className="w-full"
                          disabled={isProcessing}
                        />
                        <p className="text-xs text-gray-500 mt-1">Otsu thresholding with edge preservation & contrast enhancement</p>
                      </div>
                    </div>
                    
                    <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                      <h5 className="text-xs font-medium text-blue-800 mb-2">Algorithm Information:</h5>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-blue-700">
                        <div>
                          <strong>Noise Reduction:</strong> Uses bilateral filtering to preserve edges while removing noise, with additional Gaussian smoothing for heavy noise.
                        </div>
                        <div>
                          <strong>Bone Suppression:</strong> Employs adaptive thresholding based on local statistics to intelligently identify and suppress bone structures while preserving details.
                        </div>
                        <div>
                          <strong>Tissue Removal:</strong> Utilizes Otsu's automatic thresholding with edge detection to selectively remove soft tissue while enhancing bone structures.
                        </div>
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

{/* Save Annotated Image */}
                <div className="mt-4 flex justify-end">
                  <button
                    onClick={handleSaveAnnotatedImage}
                    className="bg-green-600 text-white px-4 py-2 rounded shadow hover:bg-green-700 transition flex items-center space-x-2"
                  >
                    <Download className="w-4 h-4" />
                    <span>Save Annotated Image</span>
                  </button>
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
      case 'examinations':
        return <PatientExaminationView />;
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