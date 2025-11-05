import React, { useState } from 'react';
import axios from 'axios';
import './ChatOrder.css';

function ChatOrder({ onOrderCreated }) {
  const [messages, setMessages] = useState([
    { type: 'bot', text: '👋 Hi! I can help you create a delivery order. Just tell me where to pick up and deliver. For example: "I need to send a 2kg package from Empire State Building to Times Square"' }
  ]);
  const [input, setInput] = useState('');
  const [orderPreview, setOrderPreview] = useState(null);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { type: 'user', text: userMessage }]);
    setLoading(true);

    try {
      const response = await axios.post('/api/chat/process', {
        message: userMessage
      });

      const data = response.data;

      if (data.success) {
        setMessages(prev => [...prev, { type: 'bot', text: data.message }]);
        setOrderPreview(data.order_preview);
      } else {
        setMessages(prev => [...prev, { type: 'bot', text: data.message }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        type: 'bot', 
        text: '❌ Sorry, I had trouble processing that. Please try again.' 
      }]);
    }

    setLoading(false);
  };

  const confirmOrder = async () => {
    if (!orderPreview) return;

    setLoading(true);

    try {
      const response = await axios.post('/api/chat/confirm', {
        order_preview: orderPreview
      });

      const data = response.data;

      if (data.success) {
        setMessages(prev => [...prev, { type: 'bot', text: data.message }]);
        
        // Pass full order data to parent
        if (onOrderCreated) {
          const fullOrderData = {
            order_id: data.order_id,
            ...orderPreview
          };
          onOrderCreated(fullOrderData);
        }
        
        setOrderPreview(null);
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        type: 'bot', 
        text: '❌ Failed to create order. Please try again.' 
      }]);
    }

    setLoading(false);
  };

  const cancelOrder = () => {
    setOrderPreview(null);
    setMessages(prev => [...prev, { 
      type: 'bot', 
      text: 'Order cancelled. What else can I help you with?' 
    }]);
  };

  return (
    <div className="chat-order-container">
      <div className="chat-header">
        <h2>💬 Chat to Order</h2>
        <p>Describe your delivery in natural language</p>
      </div>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.type}`}>
            <div className="message-bubble">
              {msg.text.split('\\n').map((line, i) => (
                <React.Fragment key={i}>
                  {line}
                  {i < msg.text.split('\\n').length - 1 && <br />}
                </React.Fragment>
              ))}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message bot">
            <div className="message-bubble typing">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
      </div>

      {orderPreview && (
        <div className="order-preview-actions">
          <button onClick={confirmOrder} className="confirm-btn">
            ✅ Confirm Order
          </button>
          <button onClick={cancelOrder} className="cancel-btn">
            ❌ Cancel
          </button>
        </div>
      )}

      <div className="chat-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your delivery request..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>

      <div className="chat-examples">
        <small>💡 Try: "Send 5kg from Central Park to Brooklyn Bridge"</small>
      </div>
    </div>
  );
}

export default ChatOrder;