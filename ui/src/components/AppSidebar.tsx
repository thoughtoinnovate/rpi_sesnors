import React, { useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  Typography,
  Divider,
  IconButton,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Info as InfoIcon,
  Close as CloseIcon,
} from '@mui/icons-material';

interface AppSidebarProps {
  open: boolean;
  onClose: () => void;
  currentView?: string;
  onViewChange?: (view: string) => void;
}

const AppSidebar: React.FC<AppSidebarProps> = ({
  open,
  onClose,
  currentView = 'dashboard',
  onViewChange,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const menuItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: <DashboardIcon />,
    },
    {
      id: 'history',
      label: 'History',
      icon: <HistoryIcon />,
    },
    {
      id: 'control',
      label: 'Control Panel',
      icon: <SettingsIcon />,
    },
    {
      id: 'about',
      label: 'About',
      icon: <InfoIcon />,
    },
  ];

  const handleItemClick = (itemId: string) => {
    if (onViewChange) {
      onViewChange(itemId);
    }
    if (isMobile) {
      onClose();
    }
  };

  return (
    <Drawer
      anchor="left"
      open={open}
      onClose={onClose}
      variant={isMobile ? 'temporary' : 'persistent'}
      sx={{
        '& .MuiDrawer-paper': {
          width: 280,
          boxSizing: 'border-box',
          borderRight: '1px solid',
          borderColor: 'divider',
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
          🌬️ PM25 Monitor
        </Typography>
        {isMobile && (
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        )}
      </Box>

      {/* Navigation Menu */}
      <List sx={{ flex: 1, py: 1 }}>
        {menuItems.map((item) => (
          <ListItem
            key={item.id}
            button
            selected={currentView === item.id}
            onClick={() => handleItemClick(item.id)}
            sx={{
              mx: 1,
              my: 0.5,
              borderRadius: 1,
              '&.Mui-selected': {
                backgroundColor: 'primary.main',
                color: 'primary.contrastText',
                '&:hover': {
                  backgroundColor: 'primary.dark',
                },
                '& .MuiListItemIcon-root': {
                  color: 'primary.contrastText',
                },
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText
              primary={item.label}
              primaryTypographyProps={{
                fontWeight: currentView === item.id ? 600 : 400,
              }}
            />
          </ListItem>
        ))}
      </List>

      {/* Footer */}
      <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <Typography variant="caption" color="text.secondary">
          PM25 Sensor Dashboard v1.0.0
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          Real-time air quality monitoring
        </Typography>
      </Box>
    </Drawer>
  );
};

export default AppSidebar;