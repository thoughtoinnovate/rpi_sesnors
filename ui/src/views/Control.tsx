import React from 'react';
import { Box, Typography } from '@mui/material';
import { useAppStore } from '../store';
import ControlPanel from '../components/ControlPanel';

const Control: React.FC = () => {
  const { schedulerStatus, loading } = useAppStore();

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Control Panel
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Manage sensor operations and data collection settings
      </Typography>
      
      <Box sx={{ mt: 3, maxWidth: 600 }}>
        <ControlPanel
          schedulerStatus={schedulerStatus}
          loading={loading}
        />
      </Box>
    </Box>
  );
};

export default Control;
