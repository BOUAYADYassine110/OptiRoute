import React, { useState, useEffect } from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import OrderForm from './components/OrderForm';
import OrderList from './components/OrderList';
import MapView from './components/MapView';
import ChatOrder from './components/ChatOrder';
import LiveTracking from './components/LiveTracking';
import AgentDashboard from './components/AgentDashboard';
import './App.css';

const API_URL = 'http://localhost:5001';

// Set up axios defaults
axios.defaults.baseURL = API_URL;
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function App() {
  const [orders, setOrders] = useState([]);
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [trackingOrder, setTrackingOrder] = useState(null);
  const [user, setUser] = useState(null);
  const [agents, setAgents] = useState([]);

  useEffect(() => {
    // Check for existing auth
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    if (token && userData) {
      setUser(JSON.parse(userData));
    } else {
      // Auto-login for demo
      setUser({username: 'demo', role: 'client'});
      localStorage.setItem('user', JSON.stringify({username: 'demo', role: 'client'}));
    }

    const newSocket = io(API_URL);
    
    newSocket.on('connect', () => {
      console.log('Connected to server');
      setConnected(true);
    });

    newSocket.on('disconnect', () => {
      console.log('Disconnected from server');
      setConnected(false);
    });

    newSocket.on('order_update', (data) => {
      console.log('Order update:', data);
      updateOrderStatus(data);
    });

    newSocket.on('agent_status', (data) => {
      console.log('Agent status:', data);
      updateAgentStatus(data);
    });

    setSocket(newSocket);
    loadAgents();

    return () => newSocket.close();
  }, []);

  const updateOrderStatus = (orderData) => {
    setOrders(prevOrders => 
      prevOrders.map(order => 
        order.order_id === orderData.order_id 
          ? { ...order, ...orderData }
          : order
      )
    );
  };

  const updateAgentStatus = (agentData) => {
    setAgents(prevAgents => 
      prevAgents.map(agent => 
        agent.agent_id === agentData.agent_id 
          ? { ...agent, ...agentData }
          : agent
      )
    );
  };

  const loadAgents = async () => {
    try {
      const response = await axios.get('/api/agents/delivery');
      setAgents(response.data.agents || []);
    } catch (error) {
      console.error('Error loading agents:', error);
      // Set mock agents as fallback
      setAgents(['delivery_001', 'delivery_002', 'delivery_003']);
    }
  };

  const handleLogin = async (credentials) => {
    try {
      const response = await axios.post('/api/auth/login', credentials);
      const { access_token, user } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user || credentials));
      setUser(user || credentials);
      
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const handleCreateOrder = async (orderData) => {
    try {
      const response = await axios.post('/api/orders/create', orderData);
      
      if (response.data.order_id) {
        const newOrder = {
          ...orderData,
          order_id: response.data.order_id,
          status: 'pending',
          created_at: new Date().toISOString()
        };
        
        setOrders(prevOrders => [...prevOrders, newOrder]);
        alert('Order created successfully!');
        return true;
      }
    } catch (error) {
      console.error('Error creating order:', error);
      alert('Failed to create order: ' + (error.response?.data?.error || error.message));
      return false;
    }
  };

  const handleChatOrderCreated = (orderData) => {
    console.log('Chat order created:', orderData);
    
    // Add order to list
    const newOrder = {
      ...orderData,
      status: 'pending',
      created_at: new Date().toISOString()
    };
    
    setOrders(prevOrders => [...prevOrders, newOrder]);
    
    // Set for tracking
    setTrackingOrder(newOrder);
    setActiveTab('tracking');
  };

  const handleTrackOrder = (order) => {
    setTrackingOrder(order);
    setActiveTab('tracking');
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🚚 OptiroRoute Client</h1>
        <div className="header-tabs">
          <button 
            className={activeTab === 'chat' ? 'active' : ''}
            onClick={() => setActiveTab('chat')}
          >
            💬 Chat Order
          </button>
          <button 
            className={activeTab === 'form' ? 'active' : ''}
            onClick={() => setActiveTab('form')}
          >
            📋 Form Order
          </button>
          <button 
            className={activeTab === 'tracking' ? 'active' : ''}
            onClick={() => setActiveTab('tracking')}
          >
            📍 Track Order
          </button>
          <button 
            className={activeTab === 'agents' ? 'active' : ''}
            onClick={() => setActiveTab('agents')}
          >
            🤖 Agents
          </button>
        </div>
        <div className="header-right">
          {user && (
            <div className="user-info">
              <span>👤 {user.username}</span>
              <button onClick={handleLogout} className="logout-btn">Logout</button>
            </div>
          )}
          <div className="connection-status">
            <span className={`status-dot ${connected ? 'connected' : 'disconnected'}`}></span>
            <span>{connected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </header>

      <div className="App-content">
        {activeTab === 'chat' && (
          <>
            <div className="left-panel">
              <ChatOrder onOrderCreated={handleChatOrderCreated} />
            </div>
            <div className="right-panel">
              <MapView orders={orders} />
            </div>
          </>
        )}

        {activeTab === 'form' && (
          <>
            <div className="left-panel">
              <OrderForm onSubmit={handleCreateOrder} />
              <OrderList orders={orders} onTrack={handleTrackOrder} />
            </div>
            <div className="right-panel">
              <MapView orders={orders} />
            </div>
          </>
        )}

        {activeTab === 'tracking' && (
          <div className="tracking-panel">
            {!trackingOrder ? (
              <div style={{padding: '2rem', textAlign: 'center'}}>
                <h2>📍 No Order Selected</h2>
                <p>Create an order first, then click "Track Live" button</p>
                <button 
                  onClick={() => {
                    // Test order for debugging
                    const testOrder = {
                      order_id: 'TEST_' + Date.now(),
                      pickup_location: {
                        address: 'Empire State Building, New York',
                        lat: 40.748817,
                        lng: -73.985428
                      },
                      delivery_location: {
                        address: 'Times Square, New York',
                        lat: 40.758896,
                        lng: -73.985130
                      },
                      weight: 2.5,
                      estimated_cost: 11.40,
                      estimated_time: 4
                    };
                    setTrackingOrder(testOrder);
                  }}
                  style={{
                    padding: '0.75rem 1.5rem',
                    background: '#667eea',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    marginTop: '1rem'
                  }}
                >
                  🎯 Test Tracking (Demo)
                </button>
              </div>
            ) : (
              <LiveTracking orderId={trackingOrder.order_id} orderData={trackingOrder} />
            )}
          </div>
        )}

        {activeTab === 'agents' && (
          <AgentDashboard agents={agents} socket={socket} />
        )}
      </div>

      {false && ( // Disabled login modal for demo
        <div className="login-modal">
          <div className="login-form">
            <h2>🔐 Login Required</h2>
            <form onSubmit={async (e) => {
              e.preventDefault();
              const formData = new FormData(e.target);
              const success = await handleLogin({
                username: formData.get('username'),
                password: formData.get('password')
              });
              if (!success) {
                alert('Login failed. Try: client1/password, delivery1/password, or manager1/password');
              }
            }}>
              <input name="username" placeholder="Username" required />
              <input name="password" type="password" placeholder="Password" required />
              <button type="submit">Login</button>
            </form>
            <p>Demo credentials: client1/password, delivery1/password, manager1/password</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;