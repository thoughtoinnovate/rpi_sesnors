import React from 'react';
import { Box, Typography } from '@mui/material';
import { useAppStore } from '../store';
import AqiCard from '../components/AqiCard';
import PmCard from '../components/PmCard';
import SensorStatusCard from '../components/SensorStatusCard';
import TrendChart from '../components/TrendChart';

const Dashboard: React.FC = () => {
  const { aqiData, pm25Data, pm10Data, sensorStatus, loading } = useAppStore();

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Air Quality Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Real-time air quality monitoring for RPi3
      </Typography>

      {/* Main Dashboard Layout */}
      <Box sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' },
        gap: 3,
        mt: 4,
      }}>
        <Box>
          <AqiCard data={aqiData} loading={loading} />
          
          {/* Trend Chart */}
          <Box sx={{ mt: 3 }}>
            <TrendChart data={null} loading={loading} />
          </Box>
        </Box>

        {/* PM Cards */}
        <Box sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}>
          <PmCard
            title="PM2.5"
            data={pm25Data}
            loading={loading}
            color="#ff9800"
          />
          <PmCard
            title="PM10"
            data={pm10Data}
            loading={loading}
            color="#2196f3"
          />
          <SensorStatusCard
            status={sensorStatus}
            loading={loading}
          />
        </Box>
      </Box>
    </Box>
  );
};

export default Dashboard;
