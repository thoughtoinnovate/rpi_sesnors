Based on the API analysis, here's a comprehensive plan for a reactive, Material Design webapp optimized for RPi3:

## API Insights for Reactivity
- **Real-time endpoints**: `/api/latest/{location}`, `/sensor/aqi/sensor/reading`, `/api/scheduler/status`
- **Historical data**: `/api/history/{location}?hours=24`, `/api/stats/{location}?days=7`
- **Control endpoints**: Scheduler start/stop, sensor power management
- **Rich data**: AQI with color coding, PM levels, particle analysis, health recommendations

## Technology Stack (RPi3 Optimized)
- **Framework**: React 18 with Vite (fast builds, small bundle)
- **UI Library**: Material-UI (MUI) v5 with Emotion styling
- **State Management**: Zustand (lightweight, simple)
- **Charts**: Recharts (lightweight, React-native)
- **HTTP Client**: Axios with request cancellation
- **Real-time**: Polling with `setInterval` (30-60s) + exponential backoff on errors

## Modern Material UI Layout

### Desktop Layout (Grid)
```
┌─────────────────────────────────────────────────────────────┐
│ AppBar: Logo | Location Selector | Refresh | Settings | Menu │
├─────────────────────────────────────────────────────────────┤
│ Sidebar │ Main Content Area                                │
│ - Nav   │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ - Stats │ │   AQI Card  │ │ PM2.5 Card  │ │ PM10 Card   │ │
│ - Logs  │ │   (Large)   │ │   (Medium)  │ │   (Medium)  │ │
│         │ └─────────────┘ └─────────────┘ └─────────────┘ │
│         │ ┌─────────────────────────────────────────────────┐ │
│         │ │           24h Trend Chart                     │ │
│         │ └─────────────────────────────────────────────────┘ │
│         │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│         │ │ Sensor Stat │ │ Particle    │ │ Health      │ │
│         │ │ Card        │ │ Analysis    │ │ Advisory    │ │
│         │ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Mobile Layout (Stack)
```
┌─────────────────────────┐
│ AppBar: ☰ | Location   │
├─────────────────────────┤
│ ┌─────────────────────┐ │
│ │     AQI Card        │ │
│ │   (Large Display)   │ │
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │   PM2.5/PM10 Cards  │ │
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │    Trend Chart      │ │
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │  Sensor/Health Info │ │
│ └─────────────────────┘ │
│ Bottom Nav: Dashboard │ History │ Control │ Settings │
└─────────────────────────┘
```

## Key Components & Features

### 1. AQI Dashboard Card
- **Large AQI number** with color-coded background (Green/Yellow/Orange/Red/Purple)
- **Animated transitions** when AQI level changes
- **Health message** and recommendations
- **Last updated timestamp** with live indicator

### 2. Real-time Data Cards
- **PM2.5/PM10 levels** with trend arrows
- **Particle size distribution** (donut chart)
- **Sensor status** (connected, warmed up, sleeping)
- **Scheduler status** with toggle switch

### 3. Interactive Charts
- **24h trend line** for PM2.5/PM10/AQI
- **Bar chart** for AQI level distribution
- **Responsive design** with touch interactions
- **Export functionality** (PNG/CSV)

### 4. Control Panel
- **Location selector** (dropdown with search)
- **Scheduler controls** (start/stop, interval setting)
- **Sensor power management** (sleep/wake/cycle)
- **Refresh interval** selector

### 5. Responsive Features
- **Breakpoints**: xs(0), sm(600), md(900), lg(1200), xl(1536)
- **Adaptive layouts**: Grid (desktop) → Stack (mobile)
- **Touch-friendly** controls for mobile
- **Progressive loading** for charts

## RPi3 Performance Optimizations
- **Bundle splitting**: Code chunks by route
- **Tree shaking**: Remove unused MUI components
- **Image optimization**: WebP format, lazy loading
- **Service worker**: Cache static assets, API responses
- **Debounced polling**: Prevent API spam
- **Memory management**: Cleanup intervals, cancel requests

## Material Design 3 Implementation
- **Dynamic Color**: Extract from AQI colors
- **Typography Scale**: Roboto font family
- **Elevation Shadows**: Card depth hierarchy
- **Motion**: Smooth transitions, micro-interactions
- **Density**: Compact mode for mobile displays

This architecture ensures a responsive, modern Material UI that performs well on RPi3 while providing real-time air quality monitoring across all devices.