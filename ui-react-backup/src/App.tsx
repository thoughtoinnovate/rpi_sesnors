import React, { useState, useMemo, Suspense, lazy } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Container, Box, Alert, useMediaQuery, CircularProgress } from '@mui/material';
import { createAppTheme } from './theme';
import { useAppStore } from './store';
import { usePolling } from './hooks/usePolling';
import { usePmData } from './hooks/usePmData';
import { useSensorStatus } from './hooks/useSensorStatus';
import { useSchedulerStatus } from './hooks/useSchedulerStatus';
import AppHeader from './components/AppHeader';
import AppSidebar from './components/AppSidebar';
import MobileBottomNav from './components/MobileBottomNav';
import './App.css';

// Lazy load views for code splitting
const Dashboard = lazy(() => import('./views/Dashboard'));
const History = lazy(() => import('./views/History'));
const Control = lazy(() => import('./views/Control'));
const About = lazy(() => import('./views/About'));

// Loading fallback component
const LoadingFallback: React.FC = () => (
  <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
    <CircularProgress />
  </Box>
);

function App() {
  // Dark mode detection
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  const [darkMode, setDarkMode] = useState(prefersDarkMode);
  
  // Create theme based on mode
  const theme = useMemo(() => createAppTheme(darkMode ? 'dark' : 'light'), [darkMode]);
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);
  const [currentView, setCurrentView] = useState('dashboard');
  
   const { error } = useAppStore();

  // Start polling for real-time data
  usePolling({
    enabled: true,
    interval: 30000, // 30 seconds
  });

  // Generate PM data
  usePmData();

  // Generate sensor status
  useSensorStatus();

  // Generate scheduler status
  useSchedulerStatus();

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleViewChange = (view: string) => {
    setCurrentView(view);
  };

  const handleRefresh = () => {
    // Trigger immediate refresh
    window.location.reload();
  };

  const handleThemeToggle = () => {
    setDarkMode(!darkMode);
  };

  // Render current view
  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'history':
        return <History />;
      case 'control':
        return <Control />;
      case 'about':
        return <About />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      
      {/* Header */}
      <AppHeader
        onRefresh={handleRefresh}
        onMenuToggle={handleMenuToggle}
        darkMode={darkMode}
        onThemeToggle={handleThemeToggle}
      />

      {/* Sidebar - Desktop */}
      {!isMobile && (
        <AppSidebar
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          currentView={currentView}
          onViewChange={handleViewChange}
        />
      )}

      {/* Sidebar - Mobile (Drawer) */}
      {isMobile && (
        <AppSidebar
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          currentView={currentView}
          onViewChange={handleViewChange}
        />
      )}

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, sm: 3 },
          pb: { xs: 10, sm: 3 }, // Extra padding bottom for mobile bottom nav
          ml: !isMobile && sidebarOpen ? '280px' : 0,
          transition: theme.transitions.create(['margin-left'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Container maxWidth="xl">
          {/* Error Display */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Lazy-loaded Views with Suspense */}
          <Suspense fallback={<LoadingFallback />}>
            {renderView()}
          </Suspense>
        </Container>
      </Box>

      {/* Mobile Bottom Navigation */}
      {isMobile && (
        <MobileBottomNav
          currentView={currentView}
          onViewChange={handleViewChange}
        />
      )}
    </ThemeProvider>
  );
}

export default App