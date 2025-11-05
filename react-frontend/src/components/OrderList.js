import React from 'react';
import './OrderList.css';

function OrderList({ orders, onTrack }) {
  const getStatusColor = (status) => {
    const colors = {
      pending: '#ff9800',
      assigned: '#2196F3',
      in_transit: '#9C27B0',
      delivered: '#4CAF50',
      failed: '#f44336'
    };
    return colors[status] || '#666';
  };

  const getStatusIcon = (status) => {
    const icons = {
      pending: '⏳',
      assigned: '📋',
      in_transit: '🚚',
      delivered: '✅',
      failed: '❌'
    };
    return icons[status] || '📦';
  };

  return (
    <div className="order-list-container">
      <h2>📋 My Orders ({orders.length})</h2>
      
      {orders.length === 0 ? (
        <div className="empty-state">
          <p>No orders yet</p>
          <p className="empty-hint">Create your first order above!</p>
        </div>
      ) : (
        <div className="orders-list">
          {orders.map((order) => (
            <div key={order.order_id} className="order-card">
              <div className="order-header">
                <span className="order-id">{order.order_id}</span>
                <span 
                  className="order-status"
                  style={{ 
                    background: getStatusColor(order.status),
                    color: 'white',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.8rem'
                  }}
                >
                  {getStatusIcon(order.status)} {order.status}
                </span>
              </div>
              
              <div className="order-details">
                <button 
                  className="track-btn"
                  onClick={() => onTrack && onTrack(order)}
                >
                  📍 Track Live
                </button>
                
                <div className="location-info">
                  <span className="location-label">📍 From:</span>
                  <span className="location-text">{order.pickup_location.address}</span>
                </div>
                
                <div className="location-info">
                  <span className="location-label">🎯 To:</span>
                  <span className="location-text">{order.delivery_location.address}</span>
                </div>
                
                <div className="order-meta">
                  <span>⚖️ {order.weight} kg</span>
                  {order.assigned_agent && (
                    <span>🚚 {order.assigned_agent}</span>
                  )}
                </div>
                
                {order.notes && (
                  <div className="order-notes">
                    💬 {order.notes}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default OrderList;