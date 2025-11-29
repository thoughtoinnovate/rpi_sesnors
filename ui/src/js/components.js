// Reusable Alpine.js Components
document.addEventListener('alpine:init', () => {
  // Loading Spinner Component
  Alpine.data('loadingSpinner', () => ({
    size: 'w-6 h-6',
    
    init() {
      this.size = this.$el.dataset.size || this.size;
    }
  }));

  // AQI Card Component
  Alpine.data('aqiCard', () => ({
    getAqiLevel(aqi) {
      if (aqi <= 50) return { level: 'Good', class: 'aqi-good', color: '#00e400' };
      if (aqi <= 100) return { level: 'Moderate', class: 'aqi-moderate', color: '#ffff00' };
      if (aqi <= 150) return { level: 'Unhealthy for Sensitive Groups', class: 'aqi-usg-sensitive', color: '#ff7e00' };
      if (aqi <= 200) return { level: 'Unhealthy', class: 'aqi-unhealthy', color: '#ff0000' };
      if (aqi <= 300) return { level: 'Very Unhealthy', class: 'aqi-very-unhealthy', color: '#8f3f97' };
      return { level: 'Hazardous', class: 'aqi-hazardous', color: '#7e0023' };
    },

    getHealthMessage(aqi) {
      if (aqi <= 50) return 'Air quality is satisfactory';
      if (aqi <= 100) return 'Air quality is acceptable';
      if (aqi <= 150) return 'Sensitive groups may experience health effects';
      if (aqi <= 200) return 'Everyone may begin to experience health effects';
      if (aqi <= 300) return 'Health warnings of emergency conditions';
      return 'Emergency conditions: entire population affected';
    }
  }));

  // PM Card Component
  Alpine.data('pmCard', () => ({
    getTrendIcon(trend) {
      switch (trend) {
        case 'up': return '↑';
        case 'down': return '↓';
        default: return '→';
      }
    },

    getTrendClass(trend) {
      switch (trend) {
        case 'up': return 'trend-up';
        case 'down': return 'trend-down';
        default: return 'trend-stable';
      }
    },

    getQualityLevel(pm25, pm10) {
      const pm25Level = this.getPm25Level(pm25);
      const pm10Level = this.getPm10Level(pm10);
      return pm25Level.value > pm10Level.value ? pm25Level : pm10Level;
    },

    getPm25Level(pm25) {
      if (pm25 <= 12) return { level: 'Good', class: 'text-green-600' };
      if (pm25 <= 35.4) return { level: 'Moderate', class: 'text-yellow-600' };
      if (pm25 <= 55.4) return { level: 'Unhealthy for Sensitive', class: 'text-orange-600' };
      if (pm25 <= 150.4) return { level: 'Unhealthy', class: 'text-red-600' };
      if (pm25 <= 250.4) return { level: 'Very Unhealthy', class: 'text-purple-600' };
      return { level: 'Hazardous', class: 'text-red-900' };
    },

    getPm10Level(pm10) {
      if (pm10 <= 54) return { level: 'Good', class: 'text-green-600' };
      if (pm10 <= 154) return { level: 'Moderate', class: 'text-yellow-600' };
      if (pm10 <= 254) return { level: 'Unhealthy for Sensitive', class: 'text-orange-600' };
      if (pm10 <= 354) return { level: 'Unhealthy', class: 'text-red-600' };
      if (pm10 <= 424) return { level: 'Very Unhealthy', class: 'text-purple-600' };
      return { level: 'Hazardous', class: 'text-red-900' };
    }
  }));

  // Sensor Status Component
  Alpine.data('sensorStatus', () => ({
    getStatusClass(status) {
      if (status.connected && status.warmedUp && !status.sleeping) {
        return 'status-online';
      }
      if (!status.connected) {
        return 'status-offline';
      }
      return 'status-warning';
    },

    getStatusText(status) {
      if (!status.connected) return 'Offline';
      if (status.sleeping) return 'Sleeping';
      if (!status.warmedUp) return 'Warming Up';
      return 'Online';
    },

    getStatusIcon(status) {
      if (!status.connected) return '⚠️';
      if (status.sleeping) return '😴';
      if (!status.warmedUp) return '🔄';
      return '✅';
    }
  }));

  // Chart Component
  Alpine.data('chart', (canvasId, type = 'line') => ({
    chart: null,
    canvasId,
    type,

    init() {
      this.initChart();
    },

    initChart() {
      const canvas = document.getElementById(this.canvasId);
      if (!canvas) return;

      const ctx = canvas.getContext('2d');
      
      // Default chart configuration
      const config = {
        type: this.type,
        data: {
          labels: [],
          datasets: []
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'top'
            }
          },
          scales: {
            x: {
              display: true,
              title: {
                display: true,
                text: 'Time'
              }
            },
            y: {
              display: true,
              title: {
                display: true,
                text: 'Value'
              }
            }
          }
        }
      };

      this.chart = new Chart(ctx, config);
    },

    updateData(data, datasets) {
      if (!this.chart) return;

      this.chart.data.labels = data.map(item => 
        new Date(item.timestamp).toLocaleTimeString()
      );
      
      this.chart.data.datasets = datasets;
      this.chart.update();
    },

    destroy() {
      if (this.chart) {
        this.chart.destroy();
        this.chart = null;
      }
    }
  }));

  // Mobile Navigation Component
  Alpine.data('mobileNav', () => ({
    open: false,

    toggle() {
      this.open = !this.open;
    },

    close() {
      this.open = false;
    }
  }));

  // Form Input Component
  Alpine.data('formInput', () => ({
    value: '',
    error: '',
    touched: false,

    validate() {
      this.touched = true;
      // Add validation logic based on input type
      this.error = '';
    },

    clearError() {
      this.error = '';
    }
  }));

  // Notification Component
  Alpine.data('notification', () => ({
    show: false,
    message: '',
    type: 'info', // info, success, warning, error
    timeout: 5000,

    showNotification(message, type = 'info', timeout = 5000) {
      this.message = message;
      this.type = type;
      this.timeout = timeout;
      this.show = true;

      if (timeout > 0) {
        setTimeout(() => {
          this.hide();
        }, timeout);
      }
    },

    hide() {
      this.show = false;
    }
  }));

  // Modal Component
  Alpine.data('modal', () => ({
    open: false,

    show() {
      this.open = true;
      document.body.style.overflow = 'hidden';
    },

    hide() {
      this.open = false;
      document.body.style.overflow = '';
    },

    toggle() {
      if (this.open) {
        this.hide();
      } else {
        this.show();
      }
    }
  }));

  // Dropdown Component
  Alpine.data('dropdown', () => ({
    open: false,

    toggle() {
      this.open = !this.open;
    },

    close() {
      this.open = false;
    },

    show() {
      this.open = true;
    }
  }));

  // Tab Component
  Alpine.data('tabs', () => ({
    activeTab: 0,

    setActiveTab(index) {
      this.activeTab = index;
    },

    isActive(index) {
      return this.activeTab === index;
    }
  }));
});