import { createTheme, Theme } from '@mui/material/styles';

// AQI color mapping based on EPA breakpoints
export const aqiColors = {
  good: '#00e400', // Green
  moderate: '#ffff00', // Yellow
  unhealthySensitive: '#ff7e00', // Orange
  unhealthy: '#ff0000', // Red
  veryUnhealthy: '#8f3f97', // Purple
  hazardous: '#7e0023', // Maroon
};

// Create theme function that supports dark mode
export const createAppTheme = (mode: 'light' | 'dark' = 'light'): Theme => {
  return createTheme({
    palette: {
      mode,
      primary: {
        main: '#1976d2',
      },
      secondary: {
        main: '#dc004e',
      },
      background: {
        default: mode === 'dark' ? '#121212' : '#f5f5f5',
        paper: mode === 'dark' ? '#1e1e1e' : '#ffffff',
      },
    },
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
      h4: {
        fontWeight: 600,
      },
      h5: {
        fontWeight: 600,
      },
      h6: {
        fontWeight: 600,
      },
    },
    components: {
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            boxShadow: mode === 'dark' 
              ? '0 2px 8px rgba(0,0,0,0.3)' 
              : '0 2px 8px rgba(0,0,0,0.1)',
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            textTransform: 'none',
            minHeight: 44, // Touch-friendly target size
            minWidth: 44,
          },
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            minWidth: 44, // Touch-friendly target size
            minHeight: 44,
          },
        },
      },
    },
  });
};

// Default theme (light mode)
export const theme = createAppTheme('light');

// Function to get AQI color based on value
export const getAqiColor = (aqi: number): string => {
  if (aqi <= 50) return aqiColors.good;
  if (aqi <= 100) return aqiColors.moderate;
  if (aqi <= 150) return aqiColors.unhealthySensitive;
  if (aqi <= 200) return aqiColors.unhealthy;
  if (aqi <= 300) return aqiColors.veryUnhealthy;
  return aqiColors.hazardous;
};

// Function to get AQI level text
export const getAqiLevel = (aqi: number): string => {
  if (aqi <= 50) return 'Good';
  if (aqi <= 100) return 'Moderate';
  if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
  if (aqi <= 200) return 'Unhealthy';
  if (aqi <= 300) return 'Very Unhealthy';
  return 'Hazardous';
};