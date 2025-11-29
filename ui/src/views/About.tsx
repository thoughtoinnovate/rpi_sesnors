import React from 'react';
import { Box, Typography } from '@mui/material';

const About: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        About
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        PM25 Sensor Dashboard v1.0.0
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Real-time air quality monitoring for Raspberry Pi 3
      </Typography>
    </Box>
  );
};

export default About;
