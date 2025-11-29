import React from 'react';
import {
  BottomNavigation,
  BottomNavigationAction,
  Paper,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

interface MobileBottomNavProps {
  currentView: string;
  onViewChange: (view: string) => void;
}

const MobileBottomNav: React.FC<MobileBottomNavProps> = ({
  currentView,
  onViewChange,
}) => {
  return (
    <Paper
      sx={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        borderTop: 1,
        borderColor: 'divider',
      }}
      elevation={3}
    >
      <BottomNavigation
        value={currentView}
        onChange={(_event, newValue) => {
          onViewChange(newValue);
        }}
        showLabels
      >
        <BottomNavigationAction
          label="Dashboard"
          value="dashboard"
          icon={<DashboardIcon />}
        />
        <BottomNavigationAction
          label="History"
          value="history"
          icon={<HistoryIcon />}
        />
        <BottomNavigationAction
          label="Control"
          value="control"
          icon={<SettingsIcon />}
        />
        <BottomNavigationAction
          label="About"
          value="about"
          icon={<InfoIcon />}
        />
      </BottomNavigation>
    </Paper>
  );
};

export default MobileBottomNav;
