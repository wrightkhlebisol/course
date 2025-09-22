import React, { useState, useEffect } from 'react';
import { Download, Calendar, TrendingUp } from 'lucide-react';

const Reports = () => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    fetchReport();
  }, [days]);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/compliance-report?days=${days}`);
      const data = await response.json();
      setReport(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching report:', error);
    }
  };

  if (loading) {
    return <div className="loading-container">Generating report...</div>;
  }

  return (
    <div className="reports-page">
      <header className="page-header">
        <h1>Compliance Reports</h1>
        <div className="report-controls">
          <select value={days} onChange={(e) => setDays(parseInt(e.target.value))}>
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
      </header>

      {report && (
        <div className="report-content">
          <div className="report-summary">
            <div className="summary-item">
              <TrendingUp className="w-8 h-8 text-green-500" />
              <div>
                <h3>Policy Actions</h3>
                <p className="metric">{report.total_policy_actions}</p>
              </div>
            </div>
            <div className="summary-item">
              <Calendar className="w-8 h-8 text-blue-500" />
              <div>
                <h3>Success Rate</h3>
                <p className="metric">{(report.success_rate * 100).toFixed(1)}%</p>
              </div>
            </div>
            <div className="summary-item">
              <Download className="w-8 h-8 text-orange-500" />
              <div>
                <h3>Cost Savings</h3>
                <p className="metric cost-savings">${report.total_cost_savings}</p>
              </div>
            </div>
          </div>

          <div className="action-breakdown">
            <h3>Action Breakdown</h3>
            <div className="action-grid">
              {Object.entries(report.action_breakdown).map(([action, stats]) => (
                <div key={action} className="action-card">
                  <h4>{action.replace(/_/g, ' ').toUpperCase()}</h4>
                  <div className="action-stats">
                    <div>Total: {stats.count}</div>
                    <div>Success: {stats.success}</div>
                    <div>Rate: {((stats.success / stats.count) * 100).toFixed(1)}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;
