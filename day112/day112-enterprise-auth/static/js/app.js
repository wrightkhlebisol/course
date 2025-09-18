// Global app functionality
class EnterpriseAuth {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.apiBase = '/api';
    }

    async makeRequest(endpoint, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(this.token && { Authorization: `Bearer ${this.token}` })
            },
            ...options
        };

        try {
            const response = await axios(endpoint, config);
            return response.data;
        } catch (error) {
            if (error.response?.status === 401) {
                this.logout();
            }
            throw error;
        }
    }

    logout() {
        localStorage.removeItem('auth_token');
        window.location.href = '/';
    }

    formatDateTime(timestamp) {
        return new Date(timestamp).toLocaleString();
    }

    showNotification(message, type = 'info') {
        // Simple notification system
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-md shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500' : 
            type === 'error' ? 'bg-red-500' : 'bg-blue-500'
        } text-white`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize global instance
window.enterpriseAuth = new EnterpriseAuth();

// Auto-refresh functionality for dashboards
document.addEventListener('DOMContentLoaded', function() {
    // Refresh data every 30 seconds if on dashboard
    if (window.location.pathname === '/' && window.enterpriseAuth.token) {
        setInterval(() => {
            if (typeof loadDashboardData === 'function') {
                loadDashboardData();
            }
        }, 30000);
    }
});
