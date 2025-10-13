import React, { useState, useEffect } from 'react';
import axios from 'axios';

function PolicyManager() {
  const [policies, setPolicies] = useState({});
  const [activePolicy, setActivePolicy] = useState(null);

  useEffect(() => {
    loadPolicies();
  }, []);

  const loadPolicies = async () => {
    try {
      const [policiesRes, activeRes] = await Promise.all([
        axios.get('http://localhost:8000/api/policies'),
        axios.get('http://localhost:8000/api/policies/active')
      ]);
      setPolicies(policiesRes.data);
      setActivePolicy(activeRes.data);
    } catch (error) {
      console.error('Failed to load policies:', error);
    }
  };

  const changePolicy = async (policyName) => {
    try {
      await axios.post('http://localhost:8000/api/policies/set', {
        policy_name: policyName
      });
      loadPolicies();
    } catch (error) {
      console.error('Failed to change policy:', error);
    }
  };

  return (
    <div className="policy-manager">
      <h3>Optimization Policies</h3>
      <div className="policy-grid">
        {Object.entries(policies).map(([key, policy]) => (
          <div 
            key={key} 
            className={`policy-card ${activePolicy?.name === policy.name ? 'active' : ''}`}
            onClick={() => changePolicy(key)}
          >
            <h4>{policy.name}</h4>
            <div className="policy-details">
              <p>Hot → Warm: {policy.tier_transition_days.hot_to_warm} days</p>
              <p>Warm → Cold: {policy.tier_transition_days.warm_to_cold} days</p>
              <p>Retention: {policy.retention_days} days</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PolicyManager;
