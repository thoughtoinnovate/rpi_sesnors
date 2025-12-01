const FREQUENCY_OPTIONS = ["5s", "15s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "4h"];
const RETENTION_OPTIONS = ["10s", "30s", "1m", "5m", "15m", "30m", "1h", "6h", "12h", "1d", "3d", "7d", "30d", "90d"];
const WINDOW_LOOKUP = {
    "1h": 60 * 60 * 1000,
    "1d": 24 * 60 * 60 * 1000,
    "1w": 7 * 24 * 60 * 60 * 1000,
    "1m": 30 * 24 * 60 * 60 * 1000,
};

const PARTICLE_LABELS = {
    particles_0_3um: "0.3um",
    particles_0_5um: "0.5um",
    particles_1_0um: "1.0um",
    particles_2_5um: "2.5um",
    particles_5_0um: "5.0um",
    particles_10um: "10um",
};

const AQI_PM25_BREAKPOINTS = [
    { cLow: 0.0, cHigh: 12.0, aqiLow: 0, aqiHigh: 50 },
    { cLow: 12.1, cHigh: 35.4, aqiLow: 51, aqiHigh: 100 },
    { cLow: 35.5, cHigh: 55.4, aqiLow: 101, aqiHigh: 150 },
    { cLow: 55.5, cHigh: 150.4, aqiLow: 151, aqiHigh: 200 },
    { cLow: 150.5, cHigh: 250.4, aqiLow: 201, aqiHigh: 300 },
    { cLow: 250.5, cHigh: 350.4, aqiLow: 301, aqiHigh: 400 },
    { cLow: 350.5, cHigh: 500.4, aqiLow: 401, aqiHigh: 500 },
];

const AQI_PM10_BREAKPOINTS = [
    { cLow: 0, cHigh: 54, aqiLow: 0, aqiHigh: 50 },
    { cLow: 55, cHigh: 154, aqiLow: 51, aqiHigh: 100 },
    { cLow: 155, cHigh: 254, aqiLow: 101, aqiHigh: 150 },
    { cLow: 255, cHigh: 354, aqiLow: 151, aqiHigh: 200 },
    { cLow: 355, cHigh: 424, aqiLow: 201, aqiHigh: 300 },
    { cLow: 425, cHigh: 504, aqiLow: 301, aqiHigh: 400 },
    { cLow: 505, cHigh: 604, aqiLow: 401, aqiHigh: 500 },
];

const defaultConfigForm = () => ({
    name: "",
    location: "",
    type: "atmospheric",
    frequency: "5m",
    retention: "",
    enabled: true,
    powersave: false,
});

const descriptorForAqi = (value) => {
    if (value == null) {
        return "No data";
    }
    if (value <= 50) return "Good";
    if (value <= 100) return "Moderate";
    if (value <= 150) return "Unhealthy (SG)";
    if (value <= 200) return "Unhealthy";
    if (value <= 300) return "Very Unhealthy";
    return "Hazardous";
};

const classForAqi = (value) => {
    if (value == null) return "";
    if (value <= 50) return "good";
    if (value <= 100) return "moderate";
    return "unhealthy";
};

const interpolateAqi = (value, segments) => {
    if (value == null || Number.isNaN(value)) {
        return null;
    }
    let chosen = segments[segments.length - 1];
    for (const seg of segments) {
        if (value <= seg.cHigh) {
            chosen = seg;
            break;
        }
    }
    const { cLow, cHigh, aqiLow, aqiHigh } = chosen;
    const constrained = Math.min(Math.max(value, cLow), cHigh);
    const result = ((aqiHigh - aqiLow) / (cHigh - cLow)) * (constrained - cLow) + aqiLow;
    return Math.round(result);
};

const computeAqi = (pm25, pm10) => {
    const pm25Aqi = interpolateAqi(pm25, AQI_PM25_BREAKPOINTS);
    const pm10Aqi = interpolateAqi(pm10, AQI_PM10_BREAKPOINTS);
    const safePm25 = pm25Aqi != null ? pm25Aqi : 0;
    const safePm10 = pm10Aqi != null ? pm10Aqi : 0;
    return Math.max(safePm25, safePm10);
};

window.dashboardApp = () => ({
        currentView: "dashboard",
        sidebarOpen: false,
        dashboardMode: "atmosphere",
        aqiMethod: "us_epa",
        readingLabel: "Atmospheric sample",
        snapshot: null,
        lastSnapshotAt: null,
        aqiValue: null,
        aqiDescriptor: "No data",
        aqiClass: "",
        schedulerStatus: { running: false, config_name: null, powersave: false },
        schedulerConfigs: [],
        selectedConfigId: "",
        startConfigId: "",
        configForm: defaultConfigForm(),
        frequencyOptions: FREQUENCY_OPTIONS,
        retentionOptions: RETENTION_OPTIONS,
        schedulerMessage: "",
        configMessage: "",
        cleanupMessage: "",
        cleanup: { location: "", before: "" },
        recentReadings: [],
        particleLabels: PARTICLE_LABELS,
        reportFilters: { location: "", metric: "aqi", window: "1d" },
        reportSummary: { count: 0, average: "--", min: "--", max: "--" },
        reportTitle: "AQI - All locations",
        reportsMessage: "",
        locationOptions: [],
        reportsChart: null,
        sensorStatus: {},
        powerMessage: "",
        powerBusy: false,
        systemInfo: {},
        banner: "",
        timers: [],
        aqiMethodOptions: {
            us_epa: "US EPA",
            purpleair: "PurpleAir",
            local: "Browser",
        },

        init() {
            this.refreshAll();
            this.startPolling();
        },

        startPolling() {
            this.timers.push(setInterval(() => this.refreshSnapshot(), 30000));
            this.timers.push(setInterval(() => this.fetchSchedulerStatus(), 45000));
            this.timers.push(setInterval(() => this.fetchSystemInfo(), 60000));
        },

        toggleSidebar() {
            this.sidebarOpen = !this.sidebarOpen;
        },

        setCurrentView(view) {
            this.currentView = view;
            if (this.sidebarOpen && window.innerWidth < 900) {
                this.sidebarOpen = false;
            }
            this.$nextTick(() => {
                if (view === "reports") {
                    this.loadReport();
                } else if (view === "system") {
                    this.fetchSystemInfo();
                } else if (view === "hardware") {
                    this.refreshSensorStatus();
                }
            });
        },

        refreshAll() {
            this.refreshSnapshot();
            this.fetchSchedulerStatus();
            this.fetchSchedulerConfigs();
            this.fetchRecentReadings();
            this.refreshSensorStatus();
            this.fetchSystemInfo();
        },

        async api(path, options = {}) {
            const init = {
                method: options.method || "GET",
                headers: options.headers || {},
            };
            if (options.body) {
                init.headers["Content-Type"] = "application/json";
                init.body = JSON.stringify(options.body);
            }
            const response = await fetch(path, init);
            const text = await response.text();
            let data = null;
            if (text) {
                try {
                    data = JSON.parse(text);
                } catch {
                    data = text;
                }
            }
            if (!response.ok) {
                const message = data && data.error ? data.error : response.statusText;
                throw new Error(message || "Request failed");
            }
            return data;
        },

        showBanner(message) {
            this.banner = message;
            setTimeout(() => {
                this.banner = "";
            }, 4000);
        },

        async refreshSnapshot() {
            try {
                this.snapshot = await this.api("/api/snapshot");
                this.lastSnapshotAt = new Date();
                this.computeDashboardValues();
            } catch (error) {
                this.showBanner(`Snapshot error: ${error.message}`);
            }
        },

        computeDashboardValues() {
            const modeKey = this.dashboardMode === "atmosphere" ? "atmospheric" : "standard";
            const serverGroup =
                this.aqiMethod !== "local" && this.snapshot && this.snapshot.aqi
                    ? this.snapshot.aqi[this.aqiMethod]
                    : null;
            const serverAqi = serverGroup && serverGroup[modeKey] && serverGroup[modeKey].aqi;
            if (serverAqi != null) {
                this.aqiValue = serverAqi;
                this.aqiDescriptor = descriptorForAqi(this.aqiValue);
                this.aqiClass = classForAqi(this.aqiValue);
                return;
            }
            if (!this.snapshot) {
                this.aqiValue = null;
                this.aqiDescriptor = "No data";
                this.aqiClass = "";
                return;
            }
            const key = this.dashboardMode === "atmosphere" ? "pm_atmosphere" : "pm_standard";
            const pmGroup = this.snapshot[key] || {};
            const value = computeAqi(pmGroup.pm2_5, pmGroup.pm10);
            this.aqiValue = Number.isFinite(value) ? value : null;
            this.aqiDescriptor = descriptorForAqi(this.aqiValue);
            this.aqiClass = classForAqi(this.aqiValue);
        },

        updateDashboardMode() {
            this.readingLabel = this.dashboardMode === "atmosphere" ? "Atmospheric sample" : "Standard sample";
            this.computeDashboardValues();
        },

        aqiLabel() {
            return this.dashboardMode === "atmosphere" ? "Atmos AQI" : "Standard AQI";
        },

        aqiMethodLabel() {
            return this.aqiMethodOptions[this.aqiMethod] || "AQI";
        },

        displayAqiValue() {
            return this.aqiValue != null ? this.aqiValue : "--";
        },

        formatPmValue(key) {
            if (!this.snapshot) return "--";
            const group = this.dashboardMode === "atmosphere" ? this.snapshot.pm_atmosphere : this.snapshot.pm_standard;
            if (!group) return "--";
            const value = group[key];
            return value != null ? `${value} ug/m3` : "--";
        },

        formatParticleValue(key) {
            if (!this.snapshot || !this.snapshot.particle_counts) return "--";
            const value = this.snapshot.particle_counts[key];
            return value != null ? value.toString() : "--";
        },

        async fetchSchedulerStatus() {
            try {
                this.schedulerStatus = await this.api("/api/scheduler/status");
            } catch (error) {
                this.schedulerMessage = `Status error: ${error.message}`;
            }
        },

        async fetchSchedulerConfigs() {
            try {
                const configs = await this.api("/api/schedules");
                this.schedulerConfigs = configs;
                this.updateLocationOptions(configs.map((cfg) => cfg.location));
                if (!this.startConfigId && configs.length) {
                    this.startConfigId = configs[0].id;
                }
                if (!this.reportFilters.location && this.locationOptions.length) {
                    this.reportFilters.location = this.locationOptions[0];
                }
            } catch (error) {
                this.configMessage = `Load error: ${error.message}`;
            }
        },

        async fetchRecentReadings() {
            try {
                this.recentReadings = await this.api("/api/readings?limit=10");
                this.updateLocationOptions(this.recentReadings.map((item) => item.location));
            } catch (error) {
                this.schedulerMessage = `Readings error: ${error.message}`;
            }
        },

        async startScheduler() {
            if (!this.startConfigId) return;
            try {
                await this.api("/api/scheduler/start", {
                    method: "POST",
                    body: { config_id: Number(this.startConfigId) },
                });
                this.schedulerMessage = "Scheduler starting";
                await this.fetchSchedulerStatus();
                this.showBanner("Scheduler start requested");
            } catch (error) {
                const message = String(error.message || "");
                if (message.toLowerCase().includes("already running")) {
                    this.schedulerMessage = "Scheduler already running. Stop it before starting another config.";
                } else {
                    this.schedulerMessage = `Start failed: ${message}`;
                }
                this.showBanner(this.schedulerMessage);
            }
        },

        async stopScheduler() {
            try {
                await this.api("/api/scheduler/stop", { method: "POST" });
                this.schedulerMessage = "Scheduler stopped";
                await this.fetchSchedulerStatus();
                this.showBanner("Scheduler stopped");
            } catch (error) {
                this.schedulerMessage = `Stop failed: ${error.message}`;
            }
        },

        populateForm() {
            if (!this.selectedConfigId) {
                this.configForm = defaultConfigForm();
                return;
            }
            const cfg = this.schedulerConfigs.find((item) => item.id === Number(this.selectedConfigId));
            if (!cfg) return;
            this.configForm = {
                name: cfg.name,
                location: cfg.location,
                type: cfg.type,
                frequency: cfg.frequency_label,
                retention: cfg.retention_label || "",
                enabled: Boolean(cfg.enabled),
                powersave: Boolean(cfg.powersave),
            };
        },

        resetConfigForm() {
            this.selectedConfigId = "";
            this.configForm = defaultConfigForm();
            this.configMessage = "";
        },

        async saveConfig() {
            const payload = {
                name: this.configForm.name,
                location: this.configForm.location,
                type: this.configForm.type,
                frequency: this.configForm.frequency,
                enabled: this.configForm.enabled,
                powersave: this.configForm.powersave,
            };
            if (this.configForm.retention) {
                payload.retention = this.configForm.retention;
            }
            try {
                if (this.selectedConfigId) {
                    await this.api(`/api/schedules/${this.selectedConfigId}`, { method: "PUT", body: payload });
                    this.configMessage = "Config updated";
                } else {
                    await this.api("/api/schedules", { method: "POST", body: payload });
                    this.configMessage = "Config created";
                }
                await this.fetchSchedulerConfigs();
                this.populateForm();
            } catch (error) {
                this.configMessage = `Save failed: ${error.message}`;
            }
        },

        async deleteConfig() {
            if (!this.selectedConfigId) return;
            if (!window.confirm("Delete this scheduler config?")) return;
            try {
                await this.api(`/api/schedules/${this.selectedConfigId}`, { method: "DELETE" });
                this.configMessage = "Config deleted";
                this.resetConfigForm();
                await this.fetchSchedulerConfigs();
            } catch (error) {
                this.configMessage = `Delete failed: ${error.message}`;
            }
        },

        clearCleanup() {
            this.cleanup = { location: "", before: "" };
            this.cleanupMessage = "";
        },

        async deleteReadings() {
            const params = new URLSearchParams();
            if (this.cleanup.before) params.set("before", this.cleanup.before);
            if (this.cleanup.location) params.set("location", this.cleanup.location);
            const query = params.toString();
            const path = query ? `/api/readings?${query}` : "/api/readings";
            try {
                const result = await this.api(path, { method: "DELETE" });
                this.cleanupMessage = `Deleted ${result.deleted} rows`;
                await this.fetchRecentReadings();
            } catch (error) {
                this.cleanupMessage = `Delete failed: ${error.message}`;
            }
        },

        async loadReport() {
            const windowMs = WINDOW_LOOKUP[this.reportFilters.window] || WINDOW_LOOKUP["1d"];
            const since = new Date(Date.now() - windowMs).toISOString();
            const params = new URLSearchParams({ limit: "500", since });
            const locationFilter = (this.reportFilters.location || "").trim();
            this.reportFilters.location = locationFilter;
            if (locationFilter) {
                params.set("location", locationFilter);
            }
            try {
                const readings = await this.api(`/api/readings?${params.toString()}`);
                this.processReport(readings);
                this.reportsMessage = "";
            } catch (error) {
                this.reportsMessage = `Report error: ${error.message}`;
            }
        },

        processReport(readings) {
            const metric = this.reportFilters.metric;
            const rows = readings.slice().sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            this.updateLocationOptions(rows.map((row) => row.location));
            const locationFilter = (this.reportFilters.location || "").trim();
            const grouped = new Map();
            for (const row of rows) {
                if (!row.timestamp) continue;
                const ts = new Date(row.timestamp);
                if (Number.isNaN(ts.getTime())) continue;
                let value = null;
                if (metric === "aqi") {
                    value = computeAqi(row.pm2_5, row.pm10);
                } else if (metric === "pm2_5") {
                    value = row.pm2_5;
                } else if (metric === "pm10") {
                    value = row.pm10;
                } else if (metric === "pm1_0") {
                    value = row.pm1;
                }
                if (value == null || Number.isNaN(value)) continue;
                const loc = row.location || "unknown";
                const bucketKey = locationFilter ? loc : loc;
                if (locationFilter && loc !== locationFilter) {
                    continue;
                }
                if (!grouped.has(bucketKey)) {
                    grouped.set(bucketKey, []);
                }
                grouped.get(bucketKey).push({ label: ts.toLocaleString(), value });
            }
            const datasets = [];
            const chartLabels = new Set();
            const palette = ["#60a5fa", "#f87171", "#34d399", "#fbbf24", "#c084fc", "#f472b6"];
            let colorIndex = 0;
            grouped.forEach((points, loc) => {
                const sortedPoints = points.sort((a, b) => new Date(a.label) - new Date(b.label));
                const labels = sortedPoints.map((p) => p.label);
                labels.forEach((l) => chartLabels.add(l));
                datasets.push({
                    label: loc,
                    data: sortedPoints.map((p) => p.value),
                    borderColor: palette[colorIndex % palette.length],
                    backgroundColor: `${palette[colorIndex % palette.length]}33`,
                    tension: 0.25,
                    pointRadius: 2,
                    fill: false,
                });
                colorIndex += 1;
            });
            const flattenedValues = datasets.flatMap((ds) => ds.data);
            if (flattenedValues.length === 0) {
                this.reportSummary = { count: 0, average: "--", min: "--", max: "--" };
                this.updateReportChart([], []);
                this.reportsMessage = "No data for current selection.";
            } else {
                const total = flattenedValues.reduce((sum, value) => sum + value, 0);
                const avg = total / flattenedValues.length;
                const min = Math.min(...flattenedValues);
                const max = Math.max(...flattenedValues);
                this.reportSummary = {
                    count: flattenedValues.length,
                    average: avg.toFixed(1),
                    min: min.toFixed(1),
                    max: max.toFixed(1),
                };
                const labelsArray = Array.from(chartLabels).sort((a, b) => new Date(a) - new Date(b));
                if (datasets.length === 1) {
                    datasets[0].fill = true;
                    datasets[0].backgroundColor = `${datasets[0].borderColor}33`;
                }
                this.updateReportChart(labelsArray, datasets);
                this.reportsMessage = "";
            }
            const metricLabel = metric.toUpperCase().replace("_", ".");
            const locationLabel = locationFilter || "All locations";
            const windowLabel = this.reportWindowLabel();
            this.reportTitle = `${metricLabel} - ${locationLabel} (${windowLabel})`;
        },

        updateReportSummary(data) {
            if (!data.length) {
                this.reportSummary = { count: 0, average: "--", min: "--", max: "--" };
                return;
            }
            const total = data.reduce((sum, value) => sum + value, 0);
            const avg = total / data.length;
            const min = Math.min(...data);
            const max = Math.max(...data);
            this.reportSummary = {
                count: data.length,
                average: avg.toFixed(1),
                min: min.toFixed(1),
                max: max.toFixed(1),
            };
        },

        updateReportChart(labels, datasets) {
            const canvas = this.$refs.reportChart;
            if (!canvas) {
                return;
            }
            if (this.reportsChart) {
                this.reportsChart.destroy();
                this.reportsChart = null;
            }
            if (!labels.length || !datasets.length) {
                const ctx = canvas.getContext("2d");
                if (ctx) {
                    const width = canvas.clientWidth || canvas.width || 0;
                    const height = canvas.clientHeight || canvas.height || 0;
                    canvas.width = width;
                    canvas.height = height;
                    ctx.clearRect(0, 0, width, height);
                }
                return;
            }
            this.reportsChart = new Chart(canvas.getContext("2d"), {
                type: "line",
                data: {
                    labels,
                    datasets,
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            ticks: { color: "#9db0d5" },
                            grid: { color: "rgba(157, 176, 213, 0.1)" },
                        },
                        y: {
                            ticks: { color: "#9db0d5" },
                            grid: { color: "rgba(157, 176, 213, 0.1)" },
                        },
                    },
                    plugins: {
                        legend: { labels: { color: "#cbd5ff" } },
                    },
                },
            });
        },

        reportWindowLabel() {
            const map = { "1h": "Hour", "1d": "Day", "1w": "Week", "1m": "Month" };
            return map[this.reportFilters.window] || "Custom";
        },

        formatMinMax(min, max) {
            if (min === "--") return "--";
            return `${min} / ${max}`;
        },

        async refreshSensorStatus() {
            try {
                this.sensorStatus = await this.api("/api/status");
            } catch (error) {
                this.showBanner(`Sensor status error: ${error.message}`);
            }
        },

        sensorConnectionLabel() {
            if (!this.sensorStatus || !this.sensorStatus.config) return "--";
            const cfg = this.sensorStatus.config;
            const address = Number(cfg.i2c_address).toString(16).padStart(2, "0");
            return `${cfg.bus} / 0x${address}`;
        },

        async setPowerMode(mode) {
            this.powerBusy = true;
            const endpoint = mode === "low" ? "/api/power/low" : "/api/power/wake";
            try {
                await this.api(endpoint, { method: "POST" });
                this.powerMessage = mode === "low" ? "Entering power save" : "Waking sensor";
                this.showBanner(this.powerMessage);
            } catch (error) {
                this.powerMessage = `Power command failed: ${error.message}`;
            } finally {
                this.powerBusy = false;
            }
        },

        async fetchSystemInfo() {
            try {
                this.systemInfo = await this.api("/api/system/info");
            } catch (error) {
                this.showBanner(`System info error: ${error.message}`);
            }
        },

        formatTimestamp(value, fallback = "--") {
            if (!value) return fallback;
            const date = value instanceof Date ? value : new Date(value);
            if (Number.isNaN(date.getTime())) return fallback;
            return date.toLocaleString();
        },

        formatJson(obj) {
            if (!obj) return "No data yet.";
            return JSON.stringify(obj, null, 2);
        },

        formatBytes(value) {
            if (!value && value !== 0) return "--";
            const units = ["B", "KB", "MB", "GB", "TB"];
            let val = value;
            let idx = 0;
            while (val >= 1024 && idx < units.length - 1) {
                val /= 1024;
                idx += 1;
            }
            return `${val.toFixed(1)} ${units[idx]}`;
        },

        formatDuration(seconds) {
            if (!seconds && seconds !== 0) return "--";
            const hrs = Math.floor(seconds / 3600);
            const mins = Math.floor((seconds % 3600) / 60);
            return `${hrs}h ${mins}m`;
        },

        formatTemperature(value) {
            if (value == null) return "--";
            return `${value.toFixed(1)} degC`;
        },

        formatLoad(load) {
            if (!load) return "--";
            const one = load["1m"] != null ? load["1m"].toFixed(2) : "0.00";
            const five = load["5m"] != null ? load["5m"].toFixed(2) : "0.00";
            const fifteen = load["15m"] != null ? load["15m"].toFixed(2) : "0.00";
            return `${one}, ${five}, ${fifteen}`;
        },

        updateLocationOptions(locations) {
            const set = new Set(this.locationOptions);
            locations
                .filter((loc) => typeof loc === "string" && loc.trim().length > 0)
                .forEach((loc) => set.add(loc.trim()));
            this.locationOptions = Array.from(set).sort((a, b) => a.localeCompare(b));
        },
});
