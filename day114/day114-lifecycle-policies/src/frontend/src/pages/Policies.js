import React, { useState, useEffect } from 'react';
import { Play, Pause, AlertCircle, CheckCircle } from 'lucide-react';

const Policies = () => {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPolicies();
  }, []);

  const fetchPolicies = async () => {
    try {
      const response = await fetch('/api/policies');
      const data = await response.json();
      setPolicies(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching policies:', error);
    }
  };

  if (loading) {
    return <div className="loading-container">Loading policies...</div>;
  }

  return (
    <div className="policies-page">
      <header className="page-header">
        <h1>Lifecycle Policies</h1>
        <p>Manage automated data lifecycle policies</p>
      </header>

      <div className="policies-grid">
        {policies.map((policy) => (
          <div key={policy.id} className="policy-card">
            <div className="policy-header">
              <h3>{policy.name}</h3>
              <div className={`policy-status ${policy.enabled ? 'active' : 'inactive'}`}>
                {policy.enabled ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                {policy.enabled ? 'Active' : 'Inactive'}
              </div>
            </div>
            
            <div className="policy-details">
              <div className="policy-info">
                <span className="label">Log Type:</span>
                <span className="value">{policy.log_type}</span>
              </div>
              <div className="policy-info">
                <span className="label">Rule Type:</span>
                <span className="value">{policy.rule_type}</span>
              </div>
              <div className="policy-info">
                <span className="label">Executions:</span>
                <span className="value">{policy.statistics.total_executions}</span>
              </div>
              <div className="policy-info">
                <span className="label">Success Rate:</span>
                <span className="value">{(policy.statistics.success_rate * 100).toFixed(1)}%</span>
              </div>
              <div className="policy-info">
                <span className="label">Cost Savings:</span>
                <span className="value cost-savings">${policy.statistics.cost_savings.toFixed(2)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Policies;
