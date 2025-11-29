// Alpine.js Stores for State Management
document.addEventListener('alpine:init', () => {
  // Main App Store
  Alpine.store('app', {
    // Current data
    currentReading: null,
    aqiData: null,
    schedulerStatus: null,
    sensorStatus: null,
    pm25Data: null,
    pm10Data: null,

    // Locations
    locations: [],
    selectedLocation: localStorage.getItem('selectedLocation') || null,

    // Settings
    refreshInterval: 30, // seconds
    pollingEnabled: true,

    // UI state
    loading: false,
    error: null,
    currentView: 'dashboard',
    sidebarOpen: window.innerWidth >= 768,
    darkMode: localStorage.getItem('darkMode') === 'true' || 
              (!localStorage.getItem('darkMode') && window.matchMedia('(prefers-color-scheme: dark)').matches),

    // Actions
    setCurrentReading(reading) {
      this.currentReading = reading;
    },

    setAqiData(data) {
      this.aqiData = data;
    },

    setSchedulerStatus(status) {
      this.schedulerStatus = status;
    },

    setSensorStatus(status) {
      this.sensorStatus = status;
    },

    setPm25Data(data) {
      this.pm25Data = data;
    },

    setPm10Data(data) {
      this.pm10Data = data;
    },

    setLocations(locations) {
      this.locations = locations;
    },

    setSelectedLocation(locationId) {
      this.selectedLocation = locationId;
      localStorage.setItem('selectedLocation', locationId);
    },

    setRefreshInterval(interval) {
      this.refreshInterval = interval;
    },

    setPollingEnabled(enabled) {
      this.pollingEnabled = enabled;
    },

    setLoading(loading) {
      this.loading = loading;
    },

    setError(error) {
      this.error = error;
      if (error) {
        setTimeout(() => {
          this.error = null;
        }, 5000);
      }
    },

    setCurrentView(view) {
      this.currentView = view;
    },

    toggleSidebar() {
      this.sidebarOpen = !this.sidebarOpen;
    },

    toggleDarkMode() {
      this.darkMode = !this.darkMode;
      localStorage.setItem('darkMode', this.darkMode);
      document.documentElement.classList.toggle('dark', this.darkMode);
    },

    reset() {
      this.currentReading = null;
      this.aqiData = null;
      this.schedulerStatus = null;
      this.sensorStatus = null;
      this.pm25Data = null;
      this.pm10Data = null;
      this.error = null;
    },

    init() {
      // Apply dark mode on initialization
      document.documentElement.classList.toggle('dark', this.darkMode);
      
      // Handle window resize for sidebar
      window.addEventListener('resize', () => {
        if (window.innerWidth >= 768) {
          this.sidebarOpen = true;
        }
      });
    }
  });

  // Polling Store
  Alpine.store('polling', {
    interval: null,
    isRunning: false,

    start() {
      if (this.isRunning) return;
      
      const app = Alpine.store('app');
      if (!app.pollingEnabled) return;

      this.isRunning = true;
      
      // Initial fetch
      this.fetchAllData();
      
      // Set up interval
      this.interval = setInterval(() => {
        if (app.pollingEnabled) {
          this.fetchAllData();
        }
      }, app.refreshInterval * 1000);
    },

    stop() {
      if (this.interval) {
        clearInterval(this.interval);
        this.interval = null;
      }
      this.isRunning = false;
    },

    async fetchAllData() {
      const app = Alpine.store('app');
      
      try {
        app.setLoading(true);
        app.setError(null);

        // Fetch data in parallel
        const promises = [];

        // Fetch latest reading if location is selected
        if (app.selectedLocation) {
          promises.push(
            window.apiClient.getLatestReading(app.selectedLocation)
              .then(data => app.setCurrentReading(data))
              .catch(err => console.warn('Failed to fetch latest reading:', err))
          );
        }

        // Fetch AQI data
        promises.push(
          window.apiClient.getAqiReading()
            .then(data => app.setAqiData(data))
            .catch(err => console.warn('Failed to fetch AQI data:', err))
        );

        // Fetch scheduler status
        promises.push(
          window.apiClient.getSchedulerStatus()
            .then(data => app.setSchedulerStatus(data))
            .catch(err => console.warn('Failed to fetch scheduler status:', err))
        );

        // Fetch locations
        promises.push(
          window.apiClient.getLocations()
            .then(data => {
              app.setLocations(data);
              // Set default location if none selected
              if (!app.selectedLocation && data.length > 0) {
                app.setSelectedLocation(data[0].name);
              }
            })
            .catch(err => console.warn('Failed to fetch locations:', err))
        );

        await Promise.allSettled(promises);

        // Calculate PM data from current reading
        if (app.currentReading) {
          app.setPm25Data({
            value: app.currentReading.pm25,
            unit: 'μg/m³',
            trend: 'stable',
            lastUpdated: app.currentReading.timestamp
          });

          app.setPm10Data({
            value: app.currentReading.pm10,
            unit: 'μg/m³',
            trend: 'stable',
            lastUpdated: app.currentReading.timestamp
          });
        }

      } catch (error) {
        app.setError(`Failed to fetch data: ${error.message}`);
      } finally {
        app.setLoading(false);
      }
    },

    restart() {
      this.stop();
      this.start();
    }
  });

  // Historical Data Store
  Alpine.store('history', {
    data: [],
    loading: false,
    error: null,

    async fetchHistoricalData(location, hours = 24) {
      this.loading = true;
      this.error = null;

      try {
        const data = await window.apiClient.getHistoricalData(location, hours);
        this.data = data;
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },

    clear() {
      this.data = [];
      this.error = null;
    }
  });

  // Control Store
  Alpine.store('control', {
    loading: false,
    error: null,
    success: null,

    async startScheduler(location, interval) {
      this.loading = true;
      this.error = null;
      this.success = null;

      try {
        await window.apiClient.startScheduler(location, interval);
        this.success = 'Scheduler started successfully';
        
        // Refresh scheduler status
        const pollingStore = Alpine.store('polling');
        await pollingStore.fetchAllData();
        
        setTimeout(() => {
          this.success = null;
        }, 3000);
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },

    async stopScheduler() {
      this.loading = true;
      this.error = null;
      this.success = null;

      try {
        await window.apiClient.stopScheduler();
        this.success = 'Scheduler stopped successfully';
        
        // Refresh scheduler status
        const pollingStore = Alpine.store('polling');
        await pollingStore.fetchAllData();
        
        setTimeout(() => {
          this.success = null;
        }, 3000);
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },

    async wakeSensor() {
      this.loading = true;
      this.error = null;
      this.success = null;

      try {
        await window.apiClient.wakeSensor();
        this.success = 'Sensor woken up successfully';
        
        // Refresh sensor status
        const pollingStore = Alpine.store('polling');
        await pollingStore.fetchAllData();
        
        setTimeout(() => {
          this.success = null;
        }, 3000);
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },

    async sleepSensor() {
      this.loading = true;
      this.error = null;
      this.success = null;

      try {
        await window.apiClient.sleepSensor();
        this.success = 'Sensor put to sleep successfully';
        
        // Refresh sensor status
        const pollingStore = Alpine.store('polling');
        await pollingStore.fetchAllData();
        
        setTimeout(() => {
          this.success = null;
        }, 3000);
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },

    clearMessages() {
      this.error = null;
      this.success = null;
    }
  });
});