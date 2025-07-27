import React, { useState, useEffect, useContext, createContext } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserInfo();
    }
  }, [token]);
  
  const fetchUserInfo = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user info:', error);
      logout();
    }
  };
  
  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token } = response.data;
      setToken(access_token);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      await fetchUserInfo();
      return true;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };
  
  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/auth/register`, userData);
      const { access_token } = response.data;
      setToken(access_token);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      await fetchUserInfo();
      return true;
    } catch (error) {
      console.error('Registration error:', error);
      return false;
    }
  };
  
  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };
  
  return (
    <AuthContext.Provider value={{ user, login, register, logout, token }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Login/Register Component
const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    email: '',
    phone_number: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    let success = false;
    if (isLogin) {
      success = await login(formData.email, formData.password);
    } else {
      success = await register({
        ...formData,
        age: parseInt(formData.age)
      });
    }
    
    if (!success) {
      alert(isLogin ? 'Login failed!' : 'Registration failed!');
    }
    
    setLoading(false);
  };
  
  return (
    <div className="auth-page">
      <div className="auth-container">
        <h2>{isLogin ? 'Sign In' : 'Sign Up'}</h2>
        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <>
              <input
                type="text"
                placeholder="Full Name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
              <input
                type="number"
                placeholder="Age"
                value={formData.age}
                onChange={(e) => setFormData({...formData, age: e.target.value})}
                required
              />
              <input
                type="tel"
                placeholder="Phone Number (+1234567890)"
                value={formData.phone_number}
                onChange={(e) => setFormData({...formData, phone_number: e.target.value})}
                required
              />
            </>
          )}
          <input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Loading...' : (isLogin ? 'Sign In' : 'Sign Up')}
          </button>
        </form>
        <p>
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button onClick={() => setIsLogin(!isLogin)}>
            {isLogin ? 'Sign Up' : 'Sign In'}
          </button>
        </p>
      </div>
    </div>
  );
};

// Settings Component
const SettingsPage = () => {
  const { user, logout } = useAuth();
  const [settings, setSettings] = useState({
    weather_alerts: true,
    maintenance_reminders: true,
    damage_alerts: true,
    sms_enabled: true,
    email_enabled: true
  });
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (user?.notification_settings) {
      setSettings(user.notification_settings);
    }
  }, [user]);
  
  const updateSettings = async () => {
    setLoading(true);
    try {
      await axios.put(`${API}/auth/settings`, { notification_settings: settings });
      alert('Settings updated successfully!');
    } catch (error) {
      console.error('Error updating settings:', error);
      alert('Failed to update settings!');
    }
    setLoading(false);
  };
  
  const deleteAccount = async () => {
    if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      try {
        await axios.delete(`${API}/auth/delete-account`);
        alert('Account deleted successfully!');
        logout();
      } catch (error) {
        console.error('Error deleting account:', error);
        alert('Failed to delete account!');
      }
    }
  };
  
  return (
    <div className="settings-page">
      <div className="settings-container">
        <h2>Settings</h2>
        
        <div className="user-info">
          <h3>User Information</h3>
          <p><strong>Name:</strong> {user?.name}</p>
          <p><strong>Email:</strong> {user?.email}</p>
          <p><strong>Phone:</strong> {user?.phone_number}</p>
          <p><strong>Age:</strong> {user?.age}</p>
        </div>
        
        <div className="notification-settings">
          <h3>Notification Settings</h3>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.weather_alerts}
                onChange={(e) => setSettings({...settings, weather_alerts: e.target.checked})}
              />
              Weather Alerts
            </label>
          </div>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.maintenance_reminders}
                onChange={(e) => setSettings({...settings, maintenance_reminders: e.target.checked})}
              />
              Maintenance Reminders
            </label>
          </div>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.damage_alerts}
                onChange={(e) => setSettings({...settings, damage_alerts: e.target.checked})}
              />
              Damage Alerts
            </label>
          </div>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.sms_enabled}
                onChange={(e) => setSettings({...settings, sms_enabled: e.target.checked})}
              />
              SMS Notifications
            </label>
          </div>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.email_enabled}
                onChange={(e) => setSettings({...settings, email_enabled: e.target.checked})}
              />
              Email Notifications
            </label>
          </div>
        </div>
        
        <div className="settings-actions">
          <button onClick={updateSettings} disabled={loading} className="btn-primary">
            {loading ? 'Updating...' : 'Update Settings'}
          </button>
          <button onClick={logout} className="btn-secondary">
            Logout
          </button>
          <button onClick={deleteAccount} className="btn-danger">
            Delete Account
          </button>
        </div>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('planner');
  const [location, setLocation] = useState({
    latitude: '',
    longitude: '',
    address: '',
    city: '',
    state: '',
    country: ''
  });
  const [nativeSpecies, setNativeSpecies] = useState([]);
  const [plotDesign, setPlotDesign] = useState({
    plot_size: '',
    unit_type: 'meter',
    planting_method: 'ground',
    soil_type: 'loam',
    selected_species: []
  });
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState([]);
  const [weather, setWeather] = useState(null);
  const [soilGuidance, setSoilGuidance] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [design3D, setDesign3D] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  
  const fetchNativeSpecies = async (lat, lng) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/species/native?latitude=${lat}&longitude=${lng}&limit=20`);
      setNativeSpecies(response.data.species);
    } catch (error) {
      console.error('Error fetching native species:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchWeatherData = async (locationId) => {
    try {
      const response = await axios.get(`${API}/weather/${locationId}`);
      setWeather(response.data);
    } catch (error) {
      console.error('Error fetching weather data:', error);
    }
  };
  
  const fetchSoilGuidance = async (soilType) => {
    try {
      const response = await axios.get(`${API}/soil/guidance?soil_type=${soilType}`);
      setSoilGuidance(response.data);
    } catch (error) {
      console.error('Error fetching soil guidance:', error);
    }
  };
  
  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API}/alerts`);
      setAlerts(response.data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };
  
  const useCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setLocation({
            ...location,
            latitude: latitude.toString(),
            longitude: longitude.toString()
          });
          fetchNativeSpecies(latitude, longitude);
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('Unable to get your location. Please enter coordinates manually.');
        }
      );
    } else {
      alert('Geolocation is not supported by this browser.');
    }
  };
  
  const handleLocationSubmit = async (e) => {
    e.preventDefault();
    if (location.latitude && location.longitude) {
      await fetchNativeSpecies(location.latitude, location.longitude);
      await fetchWeatherData('mock-location-id');
    }
  };
  
  const handleSpeciesSelect = (speciesId) => {
    if (plotDesign.selected_species.includes(speciesId)) {
      setPlotDesign({
        ...plotDesign,
        selected_species: plotDesign.selected_species.filter(id => id !== speciesId)
      });
    } else {
      setPlotDesign({
        ...plotDesign,
        selected_species: [...plotDesign.selected_species, speciesId]
      });
    }
  };
  
  const handleSoilTypeChange = (soilType) => {
    setPlotDesign({
      ...plotDesign,
      soil_type: soilType
    });
    fetchSoilGuidance(soilType);
  };
  
  const createPlotDesign = async () => {
    try {
      const plotData = {
        location_id: 'location-123',
        plot_size: parseFloat(plotDesign.plot_size),
        unit_type: plotDesign.unit_type,
        planting_method: plotDesign.planting_method,
        soil_type: plotDesign.soil_type,
        selected_species: plotDesign.selected_species
      };
      
      const response = await axios.post(`${API}/plots`, plotData);
      console.log('Plot created:', response.data);
      setDesign3D(response.data.visualization_3d);
      alert('Plot design created successfully!');
    } catch (error) {
      console.error('Error creating plot:', error);
      alert('Failed to create plot design!');
    }
  };
  
  const simulateIssues = async () => {
    try {
      const response = await axios.post(`${API}/simulate-plantation-issues`);
      alert('Plantation issues simulated! Check your phone for SMS alerts.');
      fetchAlerts();
    } catch (error) {
      console.error('Error simulating issues:', error);
      alert('Failed to simulate issues!');
    }
  };
  
  useEffect(() => {
    if (user) {
      fetchAlerts();
    }
  }, [user]);
  
  const PlantCard = ({ species, isSelected, onSelect }) => (
    <div 
      className={`plant-card ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect(species.id)}
    >
      <div className="plant-info">
        <h3 className="plant-name">{species.common_name}</h3>
        <p className="scientific-name">{species.scientific_name}</p>
        <div className="plant-details">
          <span className="plant-type">{species.plant_type}</span>
          <span className="height">{species.height_range}</span>
          <span className="layer">Layer {species.miyawaki_layer}</span>
        </div>
        <div className="benefits">
          {species.benefits.map((benefit, index) => (
            <span key={index} className="benefit-tag">{benefit}</span>
          ))}
        </div>
      </div>
    </div>
  );
  
  const WeatherCard = ({ weather }) => (
    <div className="weather-card">
      <h3>Current Weather</h3>
      <div className="weather-info">
        <div className="weather-stat">
          <span className="label">Temperature:</span>
          <span className="value">{weather.temperature}°C</span>
        </div>
        <div className="weather-stat">
          <span className="label">Humidity:</span>
          <span className="value">{weather.humidity}%</span>
        </div>
        <div className="weather-stat">
          <span className="label">Rainfall:</span>
          <span className="value">{weather.rainfall}mm</span>
        </div>
        <div className="weather-stat">
          <span className="label">Condition:</span>
          <span className="value">{weather.weather_condition}</span>
        </div>
      </div>
      
      {weather.alerts && weather.alerts.length > 0 && (
        <div className="weather-alerts">
          <h4>Weather Alerts:</h4>
          {weather.alerts.map((alert, index) => (
            <div key={index} className={`alert-item ${alert.severity}`}>
              <span className="alert-type">{alert.type}</span>
              <span className="alert-message">{alert.message}</span>
            </div>
          ))}
        </div>
      )}
      
      <div className="planting-advice">
        <h4>Planting Advice:</h4>
        <p>{weather.planting_advice}</p>
      </div>
    </div>
  );
  
  const SoilGuidanceCard = ({ guidance }) => (
    <div className="soil-guidance-card">
      <h3>Soil Preparation Guide</h3>
      <div className="guidance-section">
        <h4>Preparation Steps:</h4>
        <ul>
          {guidance.guidance.preparation.map((step, index) => (
            <li key={index}>{step}</li>
          ))}
        </ul>
      </div>
      <div className="guidance-section">
        <h4>Miyawaki Tips:</h4>
        <ul>
          {guidance.miyawaki_tips.map((tip, index) => (
            <li key={index}>{tip}</li>
          ))}
        </ul>
      </div>
    </div>
  );
  
  const Design3DCard = ({ design }) => (
    <div className="design-3d-card">
      <h3>3D Forest Visualization</h3>
      <div className="plot-info">
        <h4>Plot Information:</h4>
        <p><strong>Area:</strong> {design.plot_dimensions.area_meters} m²</p>
        <p><strong>Dimensions:</strong> {design.plot_dimensions.estimated_length}m × {design.plot_dimensions.estimated_width}m</p>
        <p><strong>Total Plants:</strong> {design.planting_structure.total_plants}</p>
        <p><strong>Density:</strong> {design.planting_structure.density_per_sqm} plants/m²</p>
      </div>
      
      <div className="layer-distribution">
        <h4>Forest Layers:</h4>
        {Object.entries(design.layers).map(([layerName, layerData]) => (
          <div key={layerName} className="layer-item">
            <div className="layer-info">
              <span className="layer-name">{layerName.replace('_', ' ')}</span>
              <span className="layer-height">{layerData.height_range}</span>
              <span className="layer-count">{layerData.plant_count} plants</span>
            </div>
            <div className="layer-bar">
              <div 
                className="layer-fill"
                style={{
                  width: `${layerData.species_ratio * 100}%`,
                  backgroundColor: layerData.color
                }}
              ></div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="growth-timeline">
        <h4>Growth Timeline:</h4>
        {Object.entries(design.growth_timeline).map(([period, description]) => (
          <div key={period} className="timeline-item">
            <strong>{period.replace('_', ' ')}:</strong> {description}
          </div>
        ))}
      </div>
    </div>
  );
  
  if (!user) {
    return (
      <AuthProvider>
        <AuthPage />
      </AuthProvider>
    );
  }
  
  if (showSettings) {
    return (
      <AuthProvider>
        <SettingsPage />
        <button onClick={() => setShowSettings(false)} className="back-btn">
          Back to App
        </button>
      </AuthProvider>
    );
  }
  
  return (
    <div className="app">
      <header className="app-header">
        <div className="hero-section">
          <div className="hero-content">
            <h1>Miyawaki Forest Planner</h1>
            <p>Create dense, native forests using the revolutionary Miyawaki method</p>
            <div className="user-welcome">
              <span>Welcome, {user.name}!</span>
              <button onClick={() => setShowSettings(true)} className="settings-btn">
                Settings
              </button>
            </div>
          </div>
          <div className="hero-image">
            <img src="https://images.unsplash.com/photo-1508713714273-c20710bbfcfc?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2Mzl8MHwxfHNlYXJjaHwxfHxkZW5zZSUyMGZvcmVzdHxlbnwwfHx8Z3JlZW58MTc1MzYwOTU5Mnww&ixlib=rb-4.1.0&q=85" alt="Dense Forest" />
          </div>
        </div>
      </header>
      
      <nav className="nav-tabs">
        <button 
          className={activeTab === 'planner' ? 'active' : ''}
          onClick={() => setActiveTab('planner')}
        >
          Forest Planner
        </button>
        <button 
          className={activeTab === 'monitoring' ? 'active' : ''}
          onClick={() => setActiveTab('monitoring')}
        >
          Monitoring
        </button>
        <button 
          className={activeTab === 'learning' ? 'active' : ''}
          onClick={() => setActiveTab('learning')}
        >
          Learning Hub
        </button>
      </nav>
      
      <main className="main-content">
        {activeTab === 'planner' && (
          <div className="planner-section">
            <div className="location-form">
              <h2>1. Enter Your Location</h2>
              <form onSubmit={handleLocationSubmit}>
                <div className="form-row">
                  <input
                    type="number"
                    placeholder="Latitude"
                    value={location.latitude}
                    onChange={(e) => setLocation({...location, latitude: e.target.value})}
                    required
                  />
                  <input
                    type="number"
                    placeholder="Longitude"
                    value={location.longitude}
                    onChange={(e) => setLocation({...location, longitude: e.target.value})}
                    required
                  />
                  <button type="button" onClick={useCurrentLocation} className="location-btn">
                    📍 Use Current Location
                  </button>
                </div>
                <div className="form-row">
                  <input
                    type="text"
                    placeholder="Address"
                    value={location.address}
                    onChange={(e) => setLocation({...location, address: e.target.value})}
                  />
                  <input
                    type="text"
                    placeholder="City"
                    value={location.city}
                    onChange={(e) => setLocation({...location, city: e.target.value})}
                  />
                </div>
                <div className="form-row">
                  <input
                    type="text"
                    placeholder="State"
                    value={location.state}
                    onChange={(e) => setLocation({...location, state: e.target.value})}
                  />
                  <input
                    type="text"
                    placeholder="Country"
                    value={location.country}
                    onChange={(e) => setLocation({...location, country: e.target.value})}
                  />
                </div>
                <button type="submit" className="btn-primary">
                  Find Native Species
                </button>
              </form>
            </div>
            
            {nativeSpecies.length > 0 && (
              <div className="species-section">
                <h2>2. Select Native Species</h2>
                <div className="species-grid">
                  {nativeSpecies.map(species => (
                    <PlantCard
                      key={species.id}
                      species={species}
                      isSelected={plotDesign.selected_species.includes(species.id)}
                      onSelect={handleSpeciesSelect}
                    />
                  ))}
                </div>
              </div>
            )}
            
            {plotDesign.selected_species.length > 0 && (
              <div className="plot-design-section">
                <h2>3. Design Your Plot</h2>
                <div className="plot-form">
                  <div className="form-group">
                    <label>Plot Size:</label>
                    <div className="size-input-group">
                      <input
                        type="number"
                        value={plotDesign.plot_size}
                        onChange={(e) => setPlotDesign({...plotDesign, plot_size: e.target.value})}
                        placeholder="e.g., 100"
                      />
                      <select
                        value={plotDesign.unit_type}
                        onChange={(e) => setPlotDesign({...plotDesign, unit_type: e.target.value})}
                      >
                        <option value="meter">Square Meters</option>
                        <option value="feet">Square Feet</option>
                        <option value="inch">Square Inches</option>
                      </select>
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Planting Method:</label>
                    <select
                      value={plotDesign.planting_method}
                      onChange={(e) => setPlotDesign({...plotDesign, planting_method: e.target.value})}
                    >
                      <option value="ground">Ground Planting</option>
                      <option value="terrace">Terrace Planting</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Soil Type:</label>
                    <select
                      value={plotDesign.soil_type}
                      onChange={(e) => handleSoilTypeChange(e.target.value)}
                    >
                      <option value="clay">Clay</option>
                      <option value="sandy">Sandy</option>
                      <option value="loam">Loam</option>
                      <option value="rocky">Rocky</option>
                    </select>
                  </div>
                  <button onClick={createPlotDesign} className="btn-primary">
                    Create Plot Design & Generate 3D View
                  </button>
                </div>
              </div>
            )}
            
            <div className="info-cards">
              {weather && <WeatherCard weather={weather} />}
              {soilGuidance && <SoilGuidanceCard guidance={soilGuidance} />}
              {design3D && <Design3DCard design={design3D} />}
            </div>
          </div>
        )}
        
        {activeTab === 'monitoring' && (
          <div className="monitoring-section">
            <h2>Project Monitoring</h2>
            
            <div className="monitoring-actions">
              <button onClick={simulateIssues} className="btn-primary">
                🚨 Simulate Plantation Issues (Demo)
              </button>
            </div>
            
            <div className="monitoring-grid">
              <div className="monitoring-card">
                <h3>Recent Alerts</h3>
                {alerts.length > 0 ? (
                  alerts.slice(0, 3).map(alert => (
                    <div key={alert.id} className={`alert-item ${alert.severity}`}>
                      <span className="alert-type">{alert.alert_type}</span>
                      <span className="alert-message">{alert.message}</span>
                      <span className="alert-status">{alert.sms_sent ? '📱 SMS Sent' : '⏳ Pending'}</span>
                    </div>
                  ))
                ) : (
                  <p>No alerts yet. Your plantation is healthy!</p>
                )}
              </div>
              
              <div className="monitoring-card">
                <h3>IoT Sensors (Simulated)</h3>
                <p>Real-time monitoring of your plantation</p>
                <div className="sensor-data">
                  <div className="sensor-item">
                    <span className="sensor-label">Soil Moisture:</span>
                    <span className="sensor-value">65%</span>
                  </div>
                  <div className="sensor-item">
                    <span className="sensor-label">Temperature:</span>
                    <span className="sensor-value">24°C</span>
                  </div>
                  <div className="sensor-item">
                    <span className="sensor-label">Light Level:</span>
                    <span className="sensor-value">85%</span>
                  </div>
                </div>
              </div>
              
              <div className="monitoring-card">
                <h3>Growth Progress</h3>
                <p>Track your forest's development over time</p>
                <div className="progress-bar">
                  <div className="progress-fill" style={{width: '35%'}}></div>
                </div>
                <p>35% of expected 3-year growth achieved</p>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'learning' && (
          <div className="learning-section">
            <h2>Learning & Awareness Hub</h2>
            <div className="learning-grid">
              <div className="learning-card">
                <h3>What is Miyawaki Method?</h3>
                <p>The Miyawaki method is a revolutionary technique for creating dense, native forests that grow 10x faster and are 30x more dense than conventional forests.</p>
                <img src="https://images.unsplash.com/photo-1599220144359-d4b723bd476d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODB8MHwxfHNlYXJjaHwzfHxtaXlhd2FraSUyMGZvcmVzdHxlbnwwfHx8Z3JlZW58MTc1MzYwOTU4Nnww&ixlib=rb-4.1.0&q=85" alt="Miyawaki Forest" />
              </div>
              
              <div className="learning-card">
                <h3>Benefits of Miyawaki Forests</h3>
                <ul>
                  <li>100% native species</li>
                  <li>Rapid growth (10x faster)</li>
                  <li>30x more dense vegetation</li>
                  <li>Self-sustaining after 3 years</li>
                  <li>Improved air quality</li>
                  <li>Enhanced biodiversity</li>
                  <li>Natural disaster protection</li>
                </ul>
              </div>
              
              <div className="learning-card">
                <h3>Success Stories</h3>
                <div className="case-study">
                  <h4>Urban Forest in Tokyo</h4>
                  <p>500 sq meters • 98% success rate</p>
                  <p>Transformed a concrete area into a thriving urban forest in just 3 years.</p>
                </div>
                <div className="case-study">
                  <h4>Bangalore Tech Park</h4>
                  <p>2000 sq meters • 96% success rate</p>
                  <p>Corporate campus forest improving employee wellbeing and air quality.</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
      
      <footer className="app-footer">
        <p>&copy; 2025 Miyawaki Forest Planner. Building sustainable forests for a greener future.</p>
      </footer>
    </div>
  );
};

export default () => (
  <AuthProvider>
    <App />
  </AuthProvider>
);