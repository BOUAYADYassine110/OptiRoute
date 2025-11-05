import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import LiveConditions from './LiveConditions';
import './LiveTracking.css';



function LiveTracking({ orderId, orderData }) {
  const [driverLocation, setDriverLocation] = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('pending');
  const [routeCoordinates, setRouteCoordinates] = useState([]);
  const [routeInfo, setRouteInfo] = useState(null);
  const [rerouteAlert, setRerouteAlert] = useState(null);
  
  console.log('LiveTracking rendered:', { orderId, orderData });

  useEffect(() => {
    if (!orderData) return;

    let isMounted = true;
    let movementInterval = null;
    let rerouteInterval = null;

    const fetchRoute = async () => {
      console.log('Fetching route for:', orderData);
      
      try {
        const response = await axios.post('/api/route/get', {
          start: orderData.pickup_location,
          end: orderData.delivery_location,
          order_id: orderId
        });
        
        console.log('Route response:', response.data);
        const data = response.data;
        
        if (!isMounted) return;
        
        setRouteInfo(data);
        
        if (data.route.coordinates && data.route.coordinates.length > 0) {
          // Handle both GeoJSON [lng, lat] and regular [lat, lng] formats
          const coords = data.route.coordinates.map(coord => {
            if (Array.isArray(coord) && coord.length >= 2) {
              // If first coordinate is longitude (< -50 or > 50), it's GeoJSON format
              if (Math.abs(coord[0]) > 50) {
                return [coord[1], coord[0]]; // Convert [lng, lat] to [lat, lng]
              } else {
                return [coord[0], coord[1]]; // Already [lat, lng]
              }
            }
            return coord;
          });
          console.log('Route loaded:', coords.length, 'points');
          setRouteCoordinates(coords);
          startDriverMovement(coords);
        } else {
          console.log('No coordinates, using fallback');
          const fallbackRoute = [
            [orderData.pickup_location.lat, orderData.pickup_location.lng],
            [orderData.delivery_location.lat, orderData.delivery_location.lng]
          ];
          setRouteCoordinates(fallbackRoute);
          startDriverMovement(fallbackRoute);
        }
      } catch (error) {
        console.error('Error fetching route:', error);
        if (!isMounted) return;
        const fallbackRoute = [
          [orderData.pickup_location.lat, orderData.pickup_location.lng],
          [orderData.delivery_location.lat, orderData.delivery_location.lng]
        ];
        setRouteCoordinates(fallbackRoute);
        startDriverMovement(fallbackRoute);
      }
    };

    const startDriverMovement = (coords) => {
      if (!coords || coords.length === 0) return;
      
      let currentProgress = 0;
      setStatus('picking_up');
      setDriverLocation({ lat: coords[0][0], lng: coords[0][1] });
      
      movementInterval = setInterval(() => {
        if (!isMounted) return;
        
        currentProgress += 1;

        if (currentProgress >= 100) {
          clearInterval(movementInterval);
          setStatus('delivered');
          setProgress(100);
          setDriverLocation({ lat: coords[coords.length - 1][0], lng: coords[coords.length - 1][1] });
          return;
        }

        setProgress(currentProgress);

        if (currentProgress < 30) {
          setStatus('picking_up');
        } else if (currentProgress >= 30 && currentProgress < 35) {
          setStatus('at_pickup');
        } else if (currentProgress >= 35 && currentProgress < 95) {
          setStatus('delivering');
        } else {
          setStatus('arriving');
        }

        const routeIndex = Math.floor((coords.length - 1) * (currentProgress / 100));
        const coord = coords[routeIndex];
        setDriverLocation({ lat: coord[0], lng: coord[1] });
      }, 1000);
    };
    
    fetchRoute();
    
    axios.post('/api/route/start-monitoring', {
      order_id: orderId,
      start: orderData.pickup_location,
      end: orderData.delivery_location
    }).catch(err => console.error('Monitoring failed:', err));
    
    rerouteInterval = setInterval(async () => {
      try {
        const res = await axios.get(`/api/route/check-reroute/${orderId}`);
        if (res.data.reroute_needed) {
          console.log('Reroute detected:', res.data.reason);
          const coords = res.data.new_route.coordinates.map(c => [c[1], c[0]]);
          setRouteCoordinates(coords);
          setRouteInfo(prev => ({ ...prev, route: res.data.new_route }));
          setRerouteAlert({
            reason: res.data.reason === 'faster_route' ? 'Faster route found!' : 'Weather alert - route updated',
            count: res.data.reroute_count
          });
          setTimeout(() => setRerouteAlert(null), 10000);
        }
      } catch (err) {
        console.error('Reroute check failed:', err);
      }
    }, 30000);

    return () => {
      isMounted = false;
      if (movementInterval) clearInterval(movementInterval);
      if (rerouteInterval) clearInterval(rerouteInterval);
      axios.post(`/api/route/stop-monitoring/${orderId}`).catch(() => {});
    };
  }, [orderId, orderData]);

  if (!orderData) {
    return (
      <div className="live-tracking-container">
        <div className="no-order">
          <p>No order selected for tracking</p>
        </div>
      </div>
    );
  }

  const driverIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  const pickupIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  const deliveryIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  const getStatusText = () => {
    switch (status) {
      case 'picking_up':
        return '🚗 Driver heading to pickup location';
      case 'at_pickup':
        return '📦 Driver at pickup - loading package';
      case 'delivering':
        return '🚚 Driver delivering your package';
      case 'arriving':
        return '🎯 Driver arriving at delivery location';
      case 'delivered':
        return '✅ Package delivered!';
      default:
        return '⏳ Waiting for driver assignment';
    }
  };

  const center = orderData.pickup_location;

  return (
    <div className="live-tracking-container">
      <div className="tracking-header">
        <h2>🚚 Live Tracking</h2>
        <div className="order-info">
          <span className="order-id">Order: {orderId}</span>
          <span className={`status-badge ${status}`}>{getStatusText()}</span>
        </div>
      </div>

      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        <span className="progress-text">{progress}% Complete</span>
      </div>

      {rerouteAlert && (
        <div className="reroute-alert">
          <strong>🔄 Route Updated:</strong> {rerouteAlert.reason}
        </div>
      )}

      <div className="tracking-map">
        <MapContainer
          center={[center.lat, center.lng]}
          zoom={13}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Pickup Marker */}
          <Marker position={[orderData.pickup_location.lat, orderData.pickup_location.lng]} icon={pickupIcon}>
            <Popup>
              <strong>📦 Pickup</strong><br />
              {orderData.pickup_location.address}
            </Popup>
          </Marker>

          {/* Delivery Marker */}
          <Marker position={[orderData.delivery_location.lat, orderData.delivery_location.lng]} icon={deliveryIcon}>
            <Popup>
              <strong>🎯 Delivery</strong><br />
              {orderData.delivery_location.address}
            </Popup>
          </Marker>

          {/* Driver Marker */}
          {driverLocation && (
            <Marker position={[driverLocation.lat, driverLocation.lng]} icon={driverIcon}>
              <Popup>
                <strong>🚚 Driver</strong><br />
                {getStatusText()}
              </Popup>
            </Marker>
          )}

          {/* Route Line - Real route or fallback */}
          <Polyline
            positions={routeCoordinates.length > 0 ? routeCoordinates : [
              [orderData.pickup_location.lat, orderData.pickup_location.lng],
              [orderData.delivery_location.lat, orderData.delivery_location.lng]
            ]}
            color={routeInfo?.traffic?.level > 70 ? '#ef4444' : routeInfo?.traffic?.level > 40 ? '#f59e0b' : '#10b981'}
            weight={5}
            opacity={0.8}
          />
        </MapContainer>
      </div>

      {/* Live Conditions */}
      <LiveConditions location={driverLocation || orderData.pickup_location} />

      <div className="tracking-details">
        <div className="detail-item">
          <span className="label">From:</span>
          <span className="value">{orderData.pickup_location.address}</span>
        </div>
        <div className="detail-item">
          <span className="label">To:</span>
          <span className="value">{orderData.delivery_location.address}</span>
        </div>
        {routeInfo && (
          <>
            <div className="detail-item">
              <span className="label">Distance:</span>
              <span className="value">{(routeInfo.route.distance / 1000).toFixed(2)} km</span>
            </div>
            <div className="detail-item">
              <span className="label">Est. Time:</span>
              <span className="value">{Math.round(routeInfo.route.adjusted_duration / 60)} min</span>
            </div>
            <div className="detail-item">
              <span className="label">🚦 Traffic:</span>
              <span className={`value traffic-${routeInfo.traffic.status}`}>
                {routeInfo.traffic.status.toUpperCase()} ({routeInfo.traffic.level}%)
              </span>
            </div>
            {routeInfo.weather.impact_score > 50 && (
              <div className="detail-item weather-warning">
                <span className="label">⚠️ Weather:</span>
                <span className="value">May cause delays</span>
              </div>
            )}
            {routeInfo.traffic.level > 70 && (
              <div className="detail-item traffic-warning">
                <span className="label">⚠️ Traffic:</span>
                <span className="value">Heavy traffic - expect delays</span>
              </div>
            )}
          </>
        )}
        {orderData.estimated_cost && (
          <div className="detail-item">
            <span className="label">Cost:</span>
            <span className="value">${orderData.estimated_cost}</span>
          </div>
        )}
        {orderData.notes && (
          <div className="detail-item">
            <span className="label">Notes:</span>
            <span className="value">{orderData.notes}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default LiveTracking;