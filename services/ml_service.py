"""
Machine Learning Service - scikit-learn integration
"""

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import pickle
import os
from datetime import datetime

class MLService:
    def __init__(self):
        self.traffic_model = None
        self.delivery_time_model = None
        self.cost_model = None
        self.scaler = StandardScaler()
        self.models_dir = 'models'
        
        # Create models directory
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
        
        # Load existing models
        self._load_models()
    
    def train_traffic_prediction_model(self, traffic_data):
        """Train traffic prediction model using scikit-learn"""
        if len(traffic_data) < 10:
            print("Not enough data for training traffic model")
            return
        
        # Prepare features: [hour, day_of_week, weather_impact]
        X = []
        y = []
        
        for record in traffic_data:
            features = [
                record['hour'],
                record['day_of_week'],
                record.get('weather_impact', 0)
            ]
            X.append(features)
            y.append(record['traffic_level'])
        
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.traffic_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.traffic_model.fit(X_scaled, y)
        
        # Calculate accuracy
        y_pred = self.traffic_model.predict(X_scaled)
        mae = mean_absolute_error(y, y_pred)
        
        print(f"Traffic model trained - MAE: {mae:.2f}")
        
        # Save model
        self._save_model(self.traffic_model, 'traffic_model.pkl')
        self._save_model(self.scaler, 'scaler.pkl')
    
    def predict_traffic(self, hour, day_of_week, weather_impact=0):
        """Predict traffic using trained model"""
        if self.traffic_model is None:
            # Fallback to simple rules
            if 7 <= hour <= 9 or 17 <= hour <= 19:
                return 70 + weather_impact * 0.3
            elif 22 <= hour or hour <= 6:
                return 20 + weather_impact * 0.1
            else:
                return 40 + weather_impact * 0.2
        
        features = np.array([[hour, day_of_week, weather_impact]])
        features_scaled = self.scaler.transform(features)
        prediction = self.traffic_model.predict(features_scaled)[0]
        
        return max(0, min(100, prediction))
    
    def train_delivery_time_model(self, delivery_data):
        """Train delivery time prediction model"""
        if len(delivery_data) < 10:
            print("Not enough data for training delivery time model")
            return
        
        # Features: [distance, weight, traffic_level, weather_impact, hour]
        X = []
        y = []
        
        for record in delivery_data:
            features = [
                record['distance'],
                record['weight'],
                record.get('traffic_level', 50),
                record.get('weather_impact', 0),
                record['hour']
            ]
            X.append(features)
            y.append(record['actual_time'])
        
        X = np.array(X)
        y = np.array(y)
        
        # Train model
        self.delivery_time_model = LinearRegression()
        self.delivery_time_model.fit(X, y)
        
        # Calculate accuracy
        y_pred = self.delivery_time_model.predict(X)
        mae = mean_absolute_error(y, y_pred)
        
        print(f"Delivery time model trained - MAE: {mae:.2f} minutes")
        
        # Save model
        self._save_model(self.delivery_time_model, 'delivery_time_model.pkl')
    
    def predict_delivery_time(self, distance, weight, traffic_level=50, weather_impact=0, hour=12):
        """Predict delivery time using trained model"""
        if self.delivery_time_model is None:
            # Fallback calculation
            base_time = distance * 3  # 3 minutes per km
            traffic_factor = 1 + (traffic_level / 200)  # 1.0 to 1.5
            weather_factor = 1 + (weather_impact / 500)  # 1.0 to 1.2
            return base_time * traffic_factor * weather_factor
        
        features = np.array([[distance, weight, traffic_level, weather_impact, hour]])
        prediction = self.delivery_time_model.predict(features)[0]
        
        return max(5, prediction)  # Minimum 5 minutes
    
    def train_cost_optimization_model(self, cost_data):
        """Train cost optimization model"""
        if len(cost_data) < 10:
            print("Not enough data for training cost model")
            return
        
        # Features: [distance, weight, urgency, traffic_level, agent_performance]
        X = []
        y = []
        
        for record in cost_data:
            features = [
                record['distance'],
                record['weight'],
                record.get('urgency', 1),  # 1=normal, 2=high, 3=urgent
                record.get('traffic_level', 50),
                record.get('agent_performance', 0.8)
            ]
            X.append(features)
            y.append(record['optimal_cost'])
        
        X = np.array(X)
        y = np.array(y)
        
        # Train model
        self.cost_model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.cost_model.fit(X, y)
        
        # Calculate accuracy
        y_pred = self.cost_model.predict(X)
        mae = mean_absolute_error(y, y_pred)
        
        print(f"Cost model trained - MAE: ${mae:.2f}")
        
        # Save model
        self._save_model(self.cost_model, 'cost_model.pkl')
    
    def predict_optimal_cost(self, distance, weight, urgency=1, traffic_level=50, agent_performance=0.8):
        """Predict optimal cost using trained model"""
        if self.cost_model is None:
            # Fallback calculation
            base_cost = 5 + (distance * 2) + (weight * 1)
            urgency_factor = 1 + (urgency - 1) * 0.2
            traffic_factor = 1 + (traffic_level / 200)
            return base_cost * urgency_factor * traffic_factor
        
        features = np.array([[distance, weight, urgency, traffic_level, agent_performance]])
        prediction = self.cost_model.predict(features)[0]
        
        return max(5, prediction)  # Minimum $5
    
    def update_models_with_feedback(self, feedback_data):
        """Update models with new feedback data"""
        # Separate data by type
        traffic_data = [d for d in feedback_data if d['type'] == 'traffic']
        delivery_data = [d for d in feedback_data if d['type'] == 'delivery']
        cost_data = [d for d in feedback_data if d['type'] == 'cost']
        
        # Retrain models if enough new data
        if len(traffic_data) >= 5:
            self.train_traffic_prediction_model(traffic_data)
        
        if len(delivery_data) >= 5:
            self.train_delivery_time_model(delivery_data)
        
        if len(cost_data) >= 5:
            self.train_cost_optimization_model(cost_data)
    
    def get_model_performance(self):
        """Get performance metrics of trained models"""
        return {
            'traffic_model': {
                'trained': self.traffic_model is not None,
                'type': 'RandomForestRegressor' if self.traffic_model else None
            },
            'delivery_time_model': {
                'trained': self.delivery_time_model is not None,
                'type': 'LinearRegression' if self.delivery_time_model else None
            },
            'cost_model': {
                'trained': self.cost_model is not None,
                'type': 'RandomForestRegressor' if self.cost_model else None
            }
        }
    
    def _save_model(self, model, filename):
        """Save model to disk"""
        filepath = os.path.join(self.models_dir, filename)
        with open(filepath, 'wb') as f:
            pickle.dump(model, f)
    
    def _load_models(self):
        """Load existing models from disk"""
        try:
            # Load traffic model
            traffic_path = os.path.join(self.models_dir, 'traffic_model.pkl')
            if os.path.exists(traffic_path):
                with open(traffic_path, 'rb') as f:
                    self.traffic_model = pickle.load(f)
            
            # Load scaler
            scaler_path = os.path.join(self.models_dir, 'scaler.pkl')
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            
            # Load delivery time model
            delivery_path = os.path.join(self.models_dir, 'delivery_time_model.pkl')
            if os.path.exists(delivery_path):
                with open(delivery_path, 'rb') as f:
                    self.delivery_time_model = pickle.load(f)
            
            # Load cost model
            cost_path = os.path.join(self.models_dir, 'cost_model.pkl')
            if os.path.exists(cost_path):
                with open(cost_path, 'rb') as f:
                    self.cost_model = pickle.load(f)
            
            print("ML models loaded successfully")
            
        except Exception as e:
            print(f"Error loading models: {e}")

# Global ML service instance
ml_service = MLService()