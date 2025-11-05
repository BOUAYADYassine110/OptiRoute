import React, { useState } from 'react';
import './OrderForm.css';

function OrderForm({ onSubmit }) {
  const [formData, setFormData] = useState({
    pickup_address: '',
    pickup_lat: '',
    pickup_lng: '',
    delivery_address: '',
    delivery_lat: '',
    delivery_lng: '',
    weight: 1,
    notes: ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const orderData = {
      order_id: 'ORD_' + Date.now(),
      pickup_location: {
        address: formData.pickup_address,
        lat: parseFloat(formData.pickup_lat) || 40.7128,
        lng: parseFloat(formData.pickup_lng) || -74.0060
      },
      delivery_location: {
        address: formData.delivery_address,
        lat: parseFloat(formData.delivery_lat) || 40.7589,
        lng: parseFloat(formData.delivery_lng) || -73.9851
      },
      weight: parseFloat(formData.weight),
      notes: formData.notes
    };

    const success = await onSubmit(orderData);
    
    if (success) {
      setFormData({
        pickup_address: '',
        pickup_lat: '',
        pickup_lng: '',
        delivery_address: '',
        delivery_lat: '',
        delivery_lng: '',
        weight: 1,
        notes: ''
      });
    }
  };

  return (
    <div className="order-form-container">
      <h2>📦 Create New Order</h2>
      <form onSubmit={handleSubmit} className="order-form">
        <div className="form-section">
          <h3>Pickup Location</h3>
          <input
            type="text"
            name="pickup_address"
            placeholder="Pickup Address *"
            value={formData.pickup_address}
            onChange={handleChange}
            required
          />
          <div className="coords-row">
            <input
              type="number"
              step="any"
              name="pickup_lat"
              placeholder="Latitude"
              value={formData.pickup_lat}
              onChange={handleChange}
            />
            <input
              type="number"
              step="any"
              name="pickup_lng"
              placeholder="Longitude"
              value={formData.pickup_lng}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="form-section">
          <h3>Delivery Location</h3>
          <input
            type="text"
            name="delivery_address"
            placeholder="Delivery Address *"
            value={formData.delivery_address}
            onChange={handleChange}
            required
          />
          <div className="coords-row">
            <input
              type="number"
              step="any"
              name="delivery_lat"
              placeholder="Latitude"
              value={formData.delivery_lat}
              onChange={handleChange}
            />
            <input
              type="number"
              step="any"
              name="delivery_lng"
              placeholder="Longitude"
              value={formData.delivery_lng}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="form-section">
          <h3>Package Details</h3>
          <input
            type="number"
            step="0.1"
            name="weight"
            placeholder="Weight (kg)"
            value={formData.weight}
            onChange={handleChange}
            min="0.1"
          />
          <textarea
            name="notes"
            placeholder="Special instructions (optional)"
            value={formData.notes}
            onChange={handleChange}
            rows="3"
          />
        </div>

        <button type="submit" className="submit-btn">
          Create Order
        </button>
      </form>
    </div>
  );
}

export default OrderForm;