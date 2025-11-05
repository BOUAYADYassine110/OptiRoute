import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './LiveConditions.css';



function LiveConditions({ location }) {
  const [conditions, setConditions] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!location) return;

    const fetchConditions = async () => {
      setLoading(true);
      try {
        const response = await axios.post('/api/conditions/live', {
          lat: location.lat,
          lng: location.lng
        });
        setConditions(response.data);
      } catch (error) {
        console.error('Error fetching conditions:', error);
      }
      setLoading(false);
    };

    fetchConditions();
    const interval = setInterval(fetchConditions, 60000); // Update every 60s

    return () => clearInterval(interval);
  }, [location?.lat, location?.lng]);

  if (!conditions) return null;

  const getWeatherIcon = (weather) => {
    const icons = {
      'Clear': '☀️',
      'Clouds': '☁️',
      'Rain': '🌧️',
      'Snow': '❄️',
      'Thunderstorm': '⛈️',
      'Fog': '🌫️'
    };
    return icons[weather] || '🌤️';
  };

  const getTrafficColor = (level) => {
    if (level < 30) return '#4CAF50';
    if (level < 70) return '#ff9800';
    return '#f44336';
  };

  return (
    <div className="live-conditions">
      <div className="condition-card weather-card">
        <div className="card-header">
          <span className="icon">{getWeatherIcon(conditions.weather?.condition || 'Clear')}</span>
          <span className="title">Weather</span>
        </div>
        <div className="card-body">
          <div className="main-stat">{Math.round(conditions.weather?.temp || 20)}°C</div>
          <div className="sub-stat">{conditions.weather?.condition || 'Clear'}</div>
          <div className="details">
            <span>💨 {Math.round(conditions.weather?.wind_speed || 0)} m/s</span>
            <span>💧 {conditions.weather?.humidity || 60}%</span>
          </div>
          {conditions.weather_impact > 50 && (
            <div className="alert">⚠️ Weather may affect delivery</div>
          )}
        </div>
      </div>

      <div className="condition-card traffic-card">
        <div className="card-header">
          <span className="icon">🚦</span>
          <span className="title">Traffic</span>
        </div>
        <div className="card-body">
          <div className="traffic-bar">
            <div 
              className="traffic-fill" 
              style={{ 
                width: `${conditions.traffic_level}%`,
                background: getTrafficColor(conditions.traffic_level)
              }}
            ></div>
          </div>
          <div className="main-stat">{conditions.traffic_status.toUpperCase()}</div>
          <div className="sub-stat">Level: {conditions.traffic_level}/100</div>
        </div>
      </div>
    </div>
  );
}

export default LiveConditions;