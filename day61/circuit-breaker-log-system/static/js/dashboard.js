// Circuit Breaker Dashboard JavaScript
class CircuitBreakerDashboard {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 5000;
        this.chartData = {
            states: [],
            successRates: [],
            timestamps: []
        };
        
        this.initializeWebSocket();
        this.setupEventListeners();
        this.setupCharts();
    }
    
    initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/metrics`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            this.ws.onopen = this.onWebSocketOpen.bind(this);
            this.ws.onmessage = this.onWebSocketMessage.bind(this);
            this.ws.onclose = this.onWebSocketClose.bind(this);
            this.ws.onerror = this.onWebSocketError.bind(this);
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    onWebSocketOpen() {
        console.log('WebSocket connected');
        this.updateConnectionStatus(true);
        this.reconnectAttempts = 0;
    }
    
    onWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.updateDashboard(data);
            this.updateCharts(data);
        } catch (error) {
            console.error('Error processing WebSocket message:', error);
        }
    }
    
    onWebSocketClose() {
        console.log('WebSocket disconnected');
        this.updateConnectionStatus(false);
        this.attemptReconnect();
    }
    
    onWebSocketError(error) {
        console.error('WebSocket error:', error);
        this.updateConnectionStatus(false);
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.initializeWebSocket();
            }, this.reconnectDelay);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        const lastUpdateElement = document.getElementById('last-update');
        
        if (connected) {
            statusElement.textContent = 'Connected';
            statusElement.className = 'status-indicator online';
            lastUpdateElement.textContent = new Date().toLocaleTimeString();
        } else {
            statusElement.textContent = 'Disconnected';
            statusElement.className = 'status-indicator offline';
        }
    }
    
    updateDashboard(data) {
        // Update system overview
        const globalStats = data.circuit_breakers.global_stats;
        document.getElementById('total-circuits').textContent = globalStats.total_circuits;
        document.getElementById('open-circuits').textContent = globalStats.open_circuits;
        document.getElementById('total-calls').textContent = globalStats.total_calls;
        
        // Calculate overall success rate
        const totalCalls = globalStats.total_calls;
        const totalFailures = globalStats.total_failures;
        const successRate = totalCalls > 0 ? ((totalCalls - totalFailures) / totalCalls * 100).toFixed(1) : 0;
        document.getElementById('success-rate').textContent = `${successRate}%`;
        
        // Update processing stats
        const processingStats = data.processing;
        document.getElementById('total-processed').textContent = processingStats.total_processed;
        document.getElementById('processing-success-rate').textContent = `${processingStats.success_rate.toFixed(1)}%`;
        document.getElementById('fallback-responses').textContent = processingStats.fallback_responses;
        
        // Update circuit breaker cards
        this.updateCircuitBreakerCards(data.circuit_breakers.circuit_breakers);
        
        // Update last update time
        document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
    }
    
    updateCircuitBreakerCards(circuitBreakers) {
        const container = document.getElementById('circuit-breakers');
        container.innerHTML = '';
        
        for (const [name, stats] of Object.entries(circuitBreakers)) {
            const card = this.createCircuitBreakerCard(name, stats);
            container.appendChild(card);
        }
    }
    
    createCircuitBreakerCard(name, stats) {
        const card = document.createElement('div');
        card.className = 'circuit-card fade-in';
        
        const stateClass = stats.state.toLowerCase();
        const stateColor = {
            'closed': '#34a853',
            'open': '#ea4335',
            'half_open': '#fbbc04'
        }[stateClass] || '#5f6368';
        
        card.innerHTML = `
            <div class="circuit-header">
                <div class="circuit-name">${name}</div>
                <div class="circuit-state ${stateClass}">${stats.state.replace('_', '-')}</div>
            </div>
            <div class="circuit-stats">
                <div class="circuit-stat">
                    <span class="circuit-stat-label">Total Calls:</span>
                    <span class="circuit-stat-value">${stats.total_calls}</span>
                </div>
                <div class="circuit-stat">
                    <span class="circuit-stat-label">Success Rate:</span>
                    <span class="circuit-stat-value">${stats.success_rate}%</span>
                </div>
                <div class="circuit-stat">
                    <span class="circuit-stat-label">Failures:</span>
                    <span class="circuit-stat-value">${stats.failed_calls}</span>
                </div>
                <div class="circuit-stat">
                    <span class="circuit-stat-label">Timeouts:</span>
                    <span class="circuit-stat-value">${stats.timeouts}</span>
                </div>
            </div>
        `;
        
        return card;
    }
    
    setupCharts() {
        // Initialize state chart
        const stateChartLayout = {
            title: 'Circuit Breaker States',
            height: 300,
            showlegend: true,
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: { family: 'Inter, sans-serif' }
        };
        
        Plotly.newPlot('state-chart', [], stateChartLayout);
        
        // Initialize success rate chart
        const successChartLayout = {
            title: 'Success Rate Over Time',
            height: 300,
            xaxis: { title: 'Time' },
            yaxis: { title: 'Success Rate (%)', range: [0, 100] },
            showlegend: false,
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: { family: 'Inter, sans-serif' }
        };
        
        Plotly.newPlot('success-chart', [], successChartLayout);
    }
    
    updateCharts(data) {
        // Update state chart
        this.updateStateChart(data.circuit_breakers.circuit_breakers);
        
        // Update success rate chart
        this.updateSuccessChart(data.circuit_breakers.global_stats);
    }
    
    updateStateChart(circuitBreakers) {
        const states = { 'CLOSED': 0, 'OPEN': 0, 'HALF_OPEN': 0 };
        
        for (const stats of Object.values(circuitBreakers)) {
            states[stats.state]++;
        }
        
        const data = [{
            values: Object.values(states),
            labels: Object.keys(states),
            type: 'pie',
            marker: {
                colors: ['#34a853', '#ea4335', '#fbbc04']
            }
        }];
        
        Plotly.redraw('state-chart', data);
    }
    
    updateSuccessChart(globalStats) {
        const timestamp = new Date().toLocaleTimeString();
        const successRate = globalStats.total_calls > 0 ? 
            ((globalStats.total_calls - globalStats.total_failures) / globalStats.total_calls * 100) : 0;
        
        // Keep only last 20 data points
        if (this.chartData.timestamps.length >= 20) {
            this.chartData.timestamps.shift();
            this.chartData.successRates.shift();
        }
        
        this.chartData.timestamps.push(timestamp);
        this.chartData.successRates.push(successRate);
        
        const data = [{
            x: this.chartData.timestamps,
            y: this.chartData.successRates,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#1a73e8' },
            marker: { color: '#1a73e8' }
        }];
        
        Plotly.redraw('success-chart', data);
    }
    
    setupEventListeners() {
        // Simulate failures button
        document.getElementById('simulate-failures').addEventListener('click', async () => {
            const button = document.getElementById('simulate-failures');
            button.disabled = true;
            button.textContent = 'Simulating...';
            
            try {
                const response = await fetch('/api/simulate/failures', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ duration: 30 })
                });
                
                if (response.ok) {
                    this.showNotification('Failure simulation started (30 seconds)', 'info');
                    setTimeout(() => {
                        this.showNotification('Failure simulation completed', 'success');
                        button.disabled = false;
                        button.textContent = 'Simulate Failures';
                    }, 30000);
                } else {
                    throw new Error('Failed to start simulation');
                }
            } catch (error) {
                console.error('Error starting failure simulation:', error);
                this.showNotification('Failed to start simulation', 'error');
                button.disabled = false;
                button.textContent = 'Simulate Failures';
            }
        });
        
        // Process logs button
        document.getElementById('process-logs').addEventListener('click', async () => {
            try {
                const response = await fetch('/api/process/logs', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ count: 10 })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    this.showNotification(`Processed ${result.processed} test logs`, 'success');
                } else {
                    throw new Error('Failed to process logs');
                }
            } catch (error) {
                console.error('Error processing logs:', error);
                this.showNotification('Failed to process logs', 'error');
            }
        });
        
        // Reset stats button
        document.getElementById('reset-stats').addEventListener('click', () => {
            this.chartData = {
                states: [],
                successRates: [],
                timestamps: []
            };
            this.setupCharts();
            this.showNotification('Statistics reset', 'info');
        });
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem;
            border-radius: 8px;
            color: white;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;
        
        const colors = {
            info: '#1a73e8',
            success: '#34a853',
            error: '#ea4335',
            warning: '#fbbc04'
        };
        
        notification.style.backgroundColor = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CircuitBreakerDashboard();
});

// Add CSS for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);
