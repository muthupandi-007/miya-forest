import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
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
    planting_method: 'ground',
    soil_type: 'loam',
    selected_species: []
  });
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState([]);
  const [weather, setWeather] = useState(null);
  const [soilGuidance, setSoilGuidance] = useState(null);

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
        user_id: 'user-123',
        location_id: 'location-123',
        plot_size: parseFloat(plotDesign.plot_size),
        planting_method: plotDesign.planting_method,
        soil_type: plotDesign.soil_type,
        selected_species: plotDesign.selected_species
      };
      
      const response = await axios.post(`${API}/plots`, plotData);
      console.log('Plot created:', response.data);
      alert('Plot design created successfully!');
    } catch (error) {
      console.error('Error creating plot:', error);
    }
  };

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

  return (
    <div className="app">
      <header className="app-header">
        <div className="hero-section">
          <div className="hero-content">
            <h1>Miyawaki Forest Planner</h1>
            <p>Create dense, native forests using the revolutionary Miyawaki method</p>
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
                    <label>Plot Size (square meters):</label>
                    <input
                      type="number"
                      value={plotDesign.plot_size}
                      onChange={(e) => setPlotDesign({...plotDesign, plot_size: e.target.value})}
                      placeholder="e.g., 100"
                    />
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
                    Create Plot Design
                  </button>
                </div>
              </div>
            )}

            <div className="info-cards">
              {weather && <WeatherCard weather={weather} />}
              {soilGuidance && <SoilGuidanceCard guidance={soilGuidance} />}
            </div>
          </div>
        )}

        {activeTab === 'monitoring' && (
          <div className="monitoring-section">
            <h2>Project Monitoring</h2>
            <div className="monitoring-grid">
              <div className="monitoring-card">
                <h3>Weather Alerts</h3>
                <p>Real-time weather monitoring and alerts for your plantation</p>
                <div className="alert-item">
                  <span className="alert-type">Weather Alert</span>
                  <span className="alert-message">Heavy rain expected. Check drainage.</span>
                </div>
              </div>
              
              <div className="monitoring-card">
                <h3>IoT Sensors</h3>
                <p>Soil moisture, temperature, and growth monitoring</p>
                <div className="sensor-data">
                  <div className="sensor-item">
                    <span className="sensor-label">Soil Moisture:</span>
                    <span className="sensor-value">65%</span>
                  </div>
                  <div className="sensor-item">
                    <span className="sensor-label">Temperature:</span>
                    <span className="sensor-value">24°C</span>
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

export default App;