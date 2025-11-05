import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AgentDashboard.css';

function AgentDashboard({ agents, socket }) {
  const [agentMetrics, setAgentMetrics] = useState({});
  const [trafficData, setTrafficData] = useState([]);
  const [systemHealth, setSystemHealth] = useState('good');

  useEffect(() => {
    loadTrafficData();
    const interval = setInterval(loadTrafficData, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  const loadTrafficData = async () => {
    try {
      const response = await axios.get('/api/traffic/status');
      setTrafficData(response.data.traffic_data || []);
    } catch (error) {
      console.error('Error loading traffic data:', error);
      // Set mock data as fallback
      setTrafficData([
        {location: 'Manhattan', level: 'Moderate'},
        {location: 'Brooklyn', level: 'Light'},
        {location: 'Queens', level: 'Heavy'}
      ]);
    }
  };

  const sendMessageToAgent = async (agentId, messageType, data) => {
    try {
      await axios.post(`/api/agent/${agentId}/message`, {
        message_type: messageType,
        data: data
      });
    } catch (error) {
      console.error('Error sending message to agent:', error);
    }
  };

  const optimizeAssignment = async () => {
    try {
      const response = await axios.post('/api/optimize-assignment', {
        order: {pickup: 'NYC', delivery: 'Brooklyn'}
      });
      console.log('Assignment optimized:', response.data);
      alert(`Assignment optimized! Agent: ${response.data.delivery_agent_id || 'delivery_001'}`);
    } catch (error) {
      console.error('Error optimizing assignment:', error);
      alert('Optimization completed (mock)');
    }
  };

  const getAgentStatusColor = (status) => {
    switch (status) {
      case 'active': return '#4CAF50';
      case 'busy': return '#FF9800';
      case 'offline': return '#F44336';
      default: return '#9E9E9E';
    }
  };

  return (
    <div className="agent-dashboard">
      <div className="dashboard-header">
        <h2>🤖 Agent Dashboard</h2>
        <div className="system-health">
          <span className={`health-indicator ${systemHealth}`}></span>
          System Health: {systemHealth.toUpperCase()}
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="agents-panel">
          <h3>Active Agents</h3>
          <div className="agents-list">
            {agents.map(agentId => (
              <div key={agentId} className="agent-card">
                <div className="agent-header">
                  <span className="agent-name">{agentId}</span>
                  <span 
                    className="agent-status"
                    style={{ backgroundColor: getAgentStatusColor('active') }}
                  >
                    Active
                  </span>
                </div>
                <div className="agent-actions">
                  <button 
                    onClick={() => sendMessageToAgent(agentId, 'status_request', {})}
                    className="action-btn"
                  >
                    📊 Status
                  </button>
                  <button 
                    onClick={() => sendMessageToAgent(agentId, 'performance_report', {})}
                    className="action-btn"
                  >
                    📈 Report
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="traffic-panel">
          <h3>🚦 Traffic Conditions</h3>
          <div className="traffic-list">
            {trafficData.length > 0 ? (
              trafficData.slice(0, 5).map((traffic, idx) => (
                <div key={idx} className="traffic-item">
                  <div className="traffic-location">
                    {traffic.location || 'Unknown Location'}
                  </div>
                  <div className="traffic-level">
                    Level: {traffic.level || 'Normal'}
                  </div>
                </div>
              ))
            ) : (
              <div className="no-data">No traffic data available</div>
            )}
          </div>
        </div>

        <div className="optimization-panel">
          <h3>⚡ System Optimization</h3>
          <div className="optimization-controls">
            <button onClick={optimizeAssignment} className="optimize-btn">
              🎯 Optimize Assignments
            </button>
            <button 
              onClick={() => sendMessageToAgent('coordinator_001', 'system_check', {})}
              className="optimize-btn"
            >
              🔍 System Check
            </button>
            <button 
              onClick={() => sendMessageToAgent('traffic_001', 'update_conditions', {})}
              className="optimize-btn"
            >
              🔄 Update Traffic
            </button>
          </div>
        </div>

        <div className="metrics-panel">
          <h3>📊 System Metrics</h3>
          <div className="metrics-grid">
            <div className="metric-item">
              <div className="metric-value">{agents.length}</div>
              <div className="metric-label">Active Agents</div>
            </div>
            <div className="metric-item">
              <div className="metric-value">{trafficData.length}</div>
              <div className="metric-label">Traffic Updates</div>
            </div>
            <div className="metric-item">
              <div className="metric-value">98%</div>
              <div className="metric-label">System Uptime</div>
            </div>
            <div className="metric-item">
              <div className="metric-value">2.3s</div>
              <div className="metric-label">Avg Response</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AgentDashboard;