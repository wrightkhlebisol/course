import { useState, useEffect, useRef } from 'react';

const useWebSocket = (url) => {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const ws = useRef(null);
  
  useEffect(() => {
    const connect = () => {
      try {
        ws.current = new WebSocket(url);
        
        ws.current.onopen = () => {
          setConnected(true);
          console.log('WebSocket connected');
        };
        
        ws.current.onmessage = (event) => {
          const message = JSON.parse(event.data);
          setLastMessage(message);
        };
        
        ws.current.onclose = () => {
          setConnected(false);
          console.log('WebSocket disconnected');
          
          // Reconnect after 3 seconds
          setTimeout(connect, 3000);
        };
        
        ws.current.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
      } catch (error) {
        console.error('WebSocket connection error:', error);
        setTimeout(connect, 3000);
      }
    };
    
    connect();
    
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url]);
  
  const sendMessage = (message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  };
  
  return { connected, lastMessage, sendMessage };
};

export default useWebSocket;
