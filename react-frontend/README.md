# OptiroRoute React Frontend

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd react-frontend
npm install
```

### 2. Start Backend Server
In the main project directory:
```bash
cd ..
pip install -r requirements-minimal.txt
python simple_start.py
```

### 3. Start React Frontend
In the react-frontend directory:
```bash
npm start
```

The app will open at `http://localhost:3000`

## 📋 Features

- ✅ Create delivery orders with pickup/delivery locations
- ✅ Real-time order tracking with WebSocket
- ✅ Interactive map with Leaflet
- ✅ Live status updates
- ✅ Multi-agent system visualization

## 🗺️ Using the App

1. **Create Order**: Fill in pickup and delivery addresses
2. **Add Coordinates**: Optionally add lat/lng for precise locations
3. **Submit**: Click "Create Order" to send to the system
4. **Track**: Watch your order appear on the map in real-time
5. **Monitor**: See status updates as agents process your order

## 🔧 Configuration

Backend API URL is set in `src/App.js`:
```javascript
const API_URL = 'http://localhost:5000';
```

## 📦 Dependencies

- React 18
- Axios (HTTP client)
- Socket.IO (Real-time communication)
- Leaflet (Interactive maps)
- React-Leaflet (React wrapper for Leaflet)

## 🎨 Customization

Edit components in `src/components/`:
- `OrderForm.js` - Order creation form
- `OrderList.js` - Order list display
- `MapView.js` - Interactive map view