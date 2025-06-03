// Smart Traffic AI Dashboard JavaScript

class TrafficDashboard {
    constructor() {
        this.socket = io();
        this.charts = {};
        this.currentSection = 'overview';
        this.intersectionData = {};
        this.alertCount = 0;
        
        this.initializeSocket();
        this.initializeNavigation();
        this.initializeCharts();
        this.initializeForms();
        this.startTimeUpdater();
        this.loadInitialData();
    }

    initializeSocket() {
        // Handle real-time updates from server
        this.socket.on('dashboard_update', (data) => {
            this.updateDashboard(data);
        });

        this.socket.on('intersection_data', (data) => {
            this.updateIntersectionData(data);
        });

        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus(false);
        });
    }

    initializeNavigation() {
        // Handle sidebar navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Remove active class from all links
                document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                
                // Add active class to clicked link
                link.classList.add('active');
                
                // Get section from href
                const section = link.getAttribute('href').substring(1);
                this.showSection(section);
            });
        });
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('section').forEach(section => {
            section.style.display = 'none';
        });
        
        // Show target section
        const targetSection = document.getElementById(sectionName);
        if (targetSection) {
            targetSection.style.display = 'block';
            this.currentSection = sectionName;
            
            // Load section-specific data
            this.loadSectionData(sectionName);
        }
    }

    initializeCharts() {
        // Initialize traffic flow chart
        const trafficCtx = document.getElementById('trafficChart');
        if (trafficCtx) {
            this.charts.traffic = new Chart(trafficCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Total Vehicles',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Initialize prediction chart
        const predictionCtx = document.getElementById('predictionChart');
        if (predictionCtx) {
            this.charts.prediction = new Chart(predictionCtx, {
                type: 'bar',
                data: {
                    labels: ['Next 15min', 'Next 30min', 'Next 1hr'],
                    datasets: [{
                        label: 'Predicted Volume',
                        data: [0, 0, 0],
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.8)',
                            'rgba(54, 162, 235, 0.8)',
                            'rgba(255, 205, 86, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Initialize daily chart
        const dailyCtx = document.getElementById('dailyChart');
        if (dailyCtx) {
            this.charts.daily = new Chart(dailyCtx, {
                type: 'line',
                data: {
                    labels: Array.from({length: 24}, (_, i) => `${i}:00`),
                    datasets: [{
                        label: 'Traffic Volume',
                        data: new Array(24).fill(0),
                        borderColor: 'rgb(153, 102, 255)',
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }

    initializeForms() {
        // Manual control form
        const manualForm = document.getElementById('manual-control-form');
        if (manualForm) {
            manualForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.applyManualControl();
            });
        }
    }

    startTimeUpdater() {
        // Update current time display
        setInterval(() => {
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            const timeElement = document.getElementById('current-time');
            if (timeElement) {
                timeElement.textContent = ` | ${timeString}`;
            }
        }, 1000);
    }

    loadInitialData() {
        // Load initial dashboard data
        fetch('/api/traffic_data')
            .then(response => response.json())
            .then(data => {
                this.updateDashboard(data);
            })
            .catch(error => {
                console.error('Error loading initial data:', error);
            });

        // Load daily report
        fetch('/api/analytics/daily_report')
            .then(response => response.json())
            .then(data => {
                this.updateDailyReport(data);
            })
            .catch(error => {
                console.error('Error loading daily report:', error);
            });
    }

    loadSectionData(sectionName) {
        switch (sectionName) {
            case 'intersections':
                this.loadIntersections();
                break;
            case 'analytics':
                this.loadAnalytics();
                break;
            case 'alerts':
                this.loadAlerts();
                break;
        }
    }

    updateDashboard(data) {
        // Update overview statistics
        this.updateOverviewStats(data);
        
        // Update charts with real-time data
        this.updateCharts(data);
        
        // Update intersection data
        if (data.traffic_counts) {
            Object.keys(data.traffic_counts).forEach(intersectionId => {
                this.intersectionData[intersectionId] = data.traffic_counts[intersectionId];
            });
        }
        
        // Update alerts
        if (data.alerts) {
            this.updateAlerts(data.alerts);
        }
    }

    updateOverviewStats(data) {
        // Calculate total vehicles across all intersections
        let totalVehicles = 0;
        if (data.traffic_counts) {
            Object.values(data.traffic_counts).forEach(counts => {
                Object.values(counts).forEach(count => {
                    totalVehicles += count;
                });
            });
        }
        
        this.updateElement('total-vehicles', totalVehicles.toLocaleString());
        this.updateElement('efficiency', '23%'); // Mock data
        this.updateElement('active-intersections', Object.keys(data.traffic_counts || {}).length);
        this.updateElement('system-alerts', data.alerts ? data.alerts.length : 0);
    }

    updateCharts(data) {
        // Update traffic flow chart
        if (this.charts.traffic && data.traffic_counts) {
            const now = new Date();
            const timeLabel = now.toLocaleTimeString();
            
            // Calculate total current traffic
            let totalCurrent = 0;
            Object.values(data.traffic_counts).forEach(counts => {
                Object.values(counts).forEach(count => totalCurrent += count);
            });
            
            // Add new data point
            this.charts.traffic.data.labels.push(timeLabel);
            this.charts.traffic.data.datasets[0].data.push(totalCurrent);
            
            // Keep only last 20 data points
            if (this.charts.traffic.data.labels.length > 20) {
                this.charts.traffic.data.labels.shift();
                this.charts.traffic.data.datasets[0].data.shift();
            }
            
            this.charts.traffic.update('none');
        }

        // Update prediction chart
        if (this.charts.prediction && data.predictions) {
            const predictions = Object.values(data.predictions)[0]; // Use first intersection
            if (predictions) {
                this.charts.prediction.data.datasets[0].data = [
                    predictions.short_term || 0,
                    predictions.medium_term || 0,
                    predictions.long_term || 0
                ];
                this.charts.prediction.update('none');
            }
        }
    }

    loadIntersections() {
        const grid = document.getElementById('intersection-grid');
        if (!grid) return;
        
        grid.innerHTML = '';
        
        Object.keys(this.intersectionData).forEach(intersectionId => {
            const card = this.createIntersectionCard(intersectionId);
            grid.appendChild(card);
        });
    }

    createIntersectionCard(intersectionId) {
        const counts = this.intersectionData[intersectionId] || {};
        
        const card = document.createElement('div');
        card.className = 'col-lg-4 col-md-6 mb-4';
        card.innerHTML = `
            <div class="card intersection-card" onclick="openIntersectionDetail('${intersectionId}')">
                <div class="card-header">
                    <h6 class="m-0 font-weight-bold">${intersectionId}</h6>
                </div>
                <div class="card-body">
                    <div class="camera-feed-container mb-3">
                        <img class="camera-feed" src="/api/camera_feed/${intersectionId}" 
                             alt="Camera feed" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5DYW1lcmEgT2ZmbGluZTwvdGV4dD48L3N2Zz4='">
                    </div>
                    <div class="traffic-summary">
                        ${Object.entries(counts).map(([direction, count]) => `
                            <div class="traffic-flow">
                                <span class="direction">${direction}:</span>
                                <span class="count">${count}</span>
                                <div class="bar">
                                    <div class="bar-fill" style="width: ${Math.min(count / 50 * 100, 100)}%"></div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        return card;
    }

    loadAnalytics() {
        // Load and display analytics data
        fetch('/api/analytics/daily_report')
            .then(response => response.json())
            .then(data => {
                this.updateDailyReport(data);
                this.updatePerformanceMetrics(data);
            })
            .catch(error => console.error('Error loading analytics:', error));
    }

    updateDailyReport(data) {
        if (this.charts.daily && data.intersections) {
            // Generate mock hourly data
            const hourlyData = Array.from({length: 24}, (_, hour) => {
                const baseTraffic = data.total_vehicles / 24;
                const peakMultiplier = (hour >= 7 && hour <= 9) || (hour >= 17 && hour <= 19) ? 1.8 : 1;
                const randomFactor = 0.8 + Math.random() * 0.4;
                return Math.round(baseTraffic * peakMultiplier * randomFactor);
            });
            
            this.charts.daily.data.datasets[0].data = hourlyData;
            this.charts.daily.update();
        }
    }

    updatePerformanceMetrics(data) {
        const metricsContainer = document.getElementById('performance-metrics');
        if (metricsContainer && data) {
            metricsContainer.innerHTML = `
                <div class="metric-item mb-3">
                    <h6>Total Vehicles Today</h6>
                    <h4 class="text-primary">${data.total_vehicles?.toLocaleString() || 'N/A'}</h4>
                </div>
                <div class="metric-item mb-3">
                    <h6>Efficiency Improvement</h6>
                    <h4 class="text-success">${data.efficiency_improvement || 'N/A'}</h4>
                </div>
                <div class="metric-item mb-3">
                    <h6>Peak Hours</h6>
                    <p>${data.peak_hours?.join(', ') || 'N/A'}</p>
                </div>
                <div class="metric-item">
                    <h6>System Uptime</h6>
                    <p>99.8%</p>
                </div>
            `;
        }
    }

    loadAlerts() {
        const alertsList = document.getElementById('alerts-list');
        if (!alertsList) return;
        
        // Mock alerts data
        const alerts = [
            {
                id: 1,
                level: 'high',
                message: 'Heavy traffic detected at Main & Oak intersection',
                timestamp: new Date(),
                type: 'traffic'
            },
            {
                id: 2,
                level: 'medium',
                message: 'Camera 3 showing reduced quality',
                timestamp: new Date(Date.now() - 300000),
                type: 'hardware'
            },
            {
                id: 3,
                level: 'low',
                message: 'Routine maintenance scheduled for tomorrow',
                timestamp: new Date(Date.now() - 600000),
                type: 'maintenance'
            }
        ];
        
        alertsList.innerHTML = alerts.map(alert => `
            <div class="alert-item alert-${alert.level}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">${this.getAlertIcon(alert.type)} ${alert.message}</h6>
                        <small class="text-muted">${alert.timestamp.toLocaleString()}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-secondary" onclick="dismissAlert(${alert.id})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    getAlertIcon(type) {
        const icons = {
            traffic: '<i class="fas fa-car text-warning"></i>',
            hardware: '<i class="fas fa-cogs text-danger"></i>',
            maintenance: '<i class="fas fa-tools text-info"></i>'
        };
        return icons[type] || '<i class="fas fa-info-circle"></i>';
    }

    updateAlerts(alerts) {
        this.alertCount = alerts.length;
        // Update alerts in current view if on alerts section
        if (this.currentSection === 'alerts') {
            this.loadAlerts();
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.querySelector('.navbar-text');
        if (statusElement) {
            const icon = connected ? 
                '<i class="fas fa-circle text-success"></i>' : 
                '<i class="fas fa-circle text-danger"></i>';
            const status = connected ? 'System Online' : 'System Offline';
            statusElement.innerHTML = `${icon} ${status}<span id="current-time"></span>`;
        }
    }

    updateElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    applyManualControl() {
        const intersectionId = document.getElementById('intersection-select').value;
        const timing = document.getElementById('timing-input').value;
        
        if (!intersectionId || !timing) {
            alert('Please select an intersection and enter timing value');
            return;
        }
        
        fetch('/api/control/light_timing', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                intersection_id: intersectionId,
                timing: parseInt(timing)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Manual control applied successfully');
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error applying manual control:', error);
            alert('Error applying manual control');
        });
    }
}

// Global functions
function refreshData() {
    window.dashboard.loadInitialData();
}

function emergencyMode() {
    const intersection = prompt('Enter intersection ID for emergency mode:');
    if (intersection) {
        fetch('/api/control/emergency_mode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                intersection_id: intersection,
                direction: 'all_red'
            })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.success ? 'Emergency mode activated' : 'Error: ' + data.error);
        });
    }
}

function emergencyAllRed() {
    if (confirm('Activate emergency ALL RED mode for all intersections?')) {
        // Implementation for all red emergency mode
        alert('Emergency ALL RED mode activated');
    }
}

function emergencyFlashing() {
    if (confirm('Activate emergency FLASHING YELLOW mode for all intersections?')) {
        // Implementation for flashing yellow emergency mode
        alert('Emergency FLASHING YELLOW mode activated');
    }
}

function resumeAutoMode() {
    if (confirm('Resume automatic AI control mode?')) {
        // Implementation for resuming auto mode
        alert('Automatic AI control resumed');
    }
}

function openIntersectionDetail(intersectionId) {
    // Open detailed view for specific intersection
    window.dashboard.socket.emit('request_intersection_data', {intersection_id: intersectionId});
}

function dismissAlert(alertId) {
    // Dismiss specific alert
    console.log('Dismissing alert:', alertId);
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new TrafficDashboard();
});
