import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './MapView.css';

// Fix Leaflet default icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

function MapView({ orders }) {
  const defaultCenter = [40.7128, -74.0060]; // New York
  const defaultZoom = 12;

  // Create custom icons
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

  return (
    <div className="map-view-container">
      <div className="map-header">
        <h2>🗺️ Live Tracking</h2>
        <span className="order-count">{orders.length} active orders</span>
      </div>
      
      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {orders.map((order) => (
          <React.Fragment key={order.order_id}>
            {/* Pickup Marker */}
            <Marker
              position={[order.pickup_location.lat, order.pickup_location.lng]}
              icon={pickupIcon}
            >
              <Popup>
                <div className="popup-content">
                  <strong>📦 Pickup</strong>
                  <p>{order.order_id}</p>
                  <p>{order.pickup_location.address}</p>
                  <p className="status-badge">{order.status}</p>
                </div>
              </Popup>
            </Marker>

            {/* Delivery Marker */}
            <Marker
              position={[order.delivery_location.lat, order.delivery_location.lng]}
              icon={deliveryIcon}
            >
              <Popup>
                <div className="popup-content">
                  <strong>🎯 Delivery</strong>
                  <p>{order.order_id}</p>
                  <p>{order.delivery_location.address}</p>
                  <p className="status-badge">{order.status}</p>
                </div>
              </Popup>
            </Marker>

            {/* Route Line */}
            <Polyline
              positions={[
                [order.pickup_location.lat, order.pickup_location.lng],
                [order.delivery_location.lat, order.delivery_location.lng]
              ]}
              color="#667eea"
              weight={3}
              opacity={0.6}
              dashArray="10, 10"
            />
          </React.Fragment>
        ))}
      </MapContainer>
    </div>
  );
}

export default MapView;