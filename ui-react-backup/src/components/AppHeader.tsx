import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Select,
  FormControl,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  LocationOn as LocationIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
} from '@mui/icons-material';
import { useAppStore } from '../store';

interface AppHeaderProps {
  onRefresh?: () => void;
  onMenuToggle?: () => void;
  darkMode?: boolean;
  onThemeToggle?: () => void;
}

const AppHeader: React.FC<AppHeaderProps> = ({ 
  onRefresh, 
  onMenuToggle, 
  darkMode = false,
  onThemeToggle 
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [locationMenuAnchor, setLocationMenuAnchor] = useState<null | HTMLElement>(null);
  
  const { 
    locations, 
    selectedLocation, 
    setSelectedLocation, 
    loading 
  } = useAppStore();

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLocationMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setLocationMenuAnchor(event.currentTarget);
  };

  const handleLocationMenuClose = () => {
    setLocationMenuAnchor(null);
  };

  const handleLocationSelect = (locationId: string) => {
    setSelectedLocation(locationId);
    handleLocationMenuClose();
  };

  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh();
    }
  };

  // Mock locations for now - will be populated from API
  const mockLocations = [
    { id: 'home', name: 'Home' },
    { id: 'office', name: 'Office' },
    { id: 'outdoor', name: 'Outdoor' },
  ];

   const currentLocations = locations.length > 0 ? locations : mockLocations;

  return (
    <AppBar position="sticky" elevation={2}>
      <Toolbar>
        {/* Mobile Menu Button */}
        {isMobile && (
          <IconButton
            edge="start"
            color="inherit"
            aria-label="menu"
            onClick={onMenuToggle}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
        )}

        {/* Logo/Title */}
        <Typography
          variant="h6"
          component="div"
          sx={{
            flexGrow: 1,
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: 1,
          }}
        >
          🌬️ PM25 Monitor
        </Typography>

        {/* Location Selector */}
        <Box sx={{ mr: 2 }}>
          {isMobile ? (
            <>
              <IconButton
                color="inherit"
                onClick={handleLocationMenuOpen}
                sx={{ mr: 1 }}
              >
                <LocationIcon />
              </IconButton>
              <Menu
                anchorEl={locationMenuAnchor}
                open={Boolean(locationMenuAnchor)}
                onClose={handleLocationMenuClose}
              >
                {currentLocations.map((location) => (
                  <MenuItem
                    key={location.id}
                    onClick={() => handleLocationSelect(location.id)}
                    selected={location.id === selectedLocation}
                  >
                    {location.name}
                  </MenuItem>
                ))}
              </Menu>
            </>
          ) : (
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <Select
                value={selectedLocation || ''}
                onChange={(e) => setSelectedLocation(e.target.value)}
                displayEmpty
                sx={{
                  color: 'white',
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255, 255, 255, 0.3)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255, 255, 255, 0.5)',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'white',
                  },
                  '& .MuiSvgIcon-root': {
                    color: 'white',
                  },
                }}
              >
                <MenuItem value="" disabled>
                  Select Location
                </MenuItem>
                {currentLocations.map((location) => (
                  <MenuItem key={location.id} value={location.id}>
                    {location.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
        </Box>

        {/* Refresh Button */}
        <IconButton
          color="inherit"
          onClick={handleRefresh}
          disabled={loading}
          sx={{ mr: 1 }}
          aria-label="Refresh data"
        >
          <RefreshIcon />
        </IconButton>

        {/* Dark Mode Toggle */}
        {onThemeToggle && (
          <IconButton
            color="inherit"
            onClick={onThemeToggle}
            sx={{ mr: 1 }}
            aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {darkMode ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>
        )}

        {/* Settings Menu */}
        <IconButton
          color="inherit"
          onClick={handleMenuOpen}
          aria-label="Settings menu"
        >
          <SettingsIcon />
        </IconButton>
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleMenuClose}>Settings</MenuItem>
          <MenuItem onClick={handleMenuClose}>About</MenuItem>
          <MenuItem onClick={handleMenuClose}>Help</MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default AppHeader;