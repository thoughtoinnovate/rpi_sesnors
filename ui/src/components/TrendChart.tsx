import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  ToggleButton,
  ToggleButtonGroup,
  Button,
  IconButton,
  Tooltip,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import {
  Download as DownloadIcon,
  Fullscreen as FullscreenIcon,
} from '@mui/icons-material';

interface TrendData {
  time: string;
  pm25: number;
  pm10: number;
  aqi: number;
}

interface TrendChartProps {
  data: TrendData[] | null;
  loading?: boolean;
}

// Styled components
const StyledCard = styled(Card)(({ theme }) => ({
  minHeight: 400,
  background: `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${theme.palette.grey[50]} 100%)`,
  border: `1px solid ${theme.palette.divider}`,
  position: 'relative',
  overflow: 'hidden',
}));

const ChartContainer = styled(Box)(({ theme }) => ({
  width: '100%',
  height: 350,
  position: 'relative',
}));

// Generate mock trend data
const generateMockTrendData = (hours: number = 24): TrendData[] => {
  const data: TrendData[] = [];
  const now = new Date();
  
  for (let i = hours; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000);
    const basePm25 = 20 + Math.sin(i / 4) * 10;
    const basePm10 = 35 + Math.sin(i / 4) * 15;
    
    data.push({
      time: time.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }),
      pm25: Math.max(0, basePm25 + (Math.random() - 0.5) * 10),
      pm10: Math.max(0, basePm10 + (Math.random() - 0.5) * 15),
      aqi: Math.max(0, 50 + Math.sin(i / 3) * 30 + (Math.random() - 0.5) * 20),
    });
  }
  
  return data;
};

const TrendChart: React.FC<TrendChartProps> = ({ data, loading = false }) => {
  const [chartType, setChartType] = useState<'line' | 'area'>('line');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['pm25', 'pm10', 'aqi']);

  const handleChartTypeChange = (
    event: React.MouseEvent<HTMLElement>,
    newChartType: 'line' | 'area' | null,
  ) => {
    if (newChartType !== null) {
      setChartType(newChartType);
    }
  };

  const handleMetricChange = (
    event: React.MouseEvent<HTMLElement>,
    newMetrics: string[],
  ) => {
    setSelectedMetrics(newMetrics);
  };

  const handleExport = () => {
    // Export functionality will be implemented later
    console.log('Export chart data');
  };

  const handleFullscreen = () => {
    // Fullscreen functionality will be implemented later
    console.log('Toggle fullscreen');
  };

  const chartData = data || generateMockTrendData();

  if (loading) {
    return (
      <StyledCard>
        <CardContent sx={{ p: 3 }}>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={350}>
            <Typography variant="h6" color="text.secondary">
              Loading trend data...
            </Typography>
          </Box>
        </CardContent>
      </StyledCard>
    );
  }

  const ChartComponent = chartType === 'line' ? LineChart : AreaChart;
  const DataComponent = chartType === 'line' ? Line : Area;

  return (
    <StyledCard>
      <CardContent sx={{ p: 3 }}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6" color="text.secondary" fontWeight={600}>
            24-Hour Trend
          </Typography>
          
          <Box display="flex" gap={1}>
            <Tooltip title="Export Chart">
              <IconButton size="small" onClick={handleExport}>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Fullscreen">
              <IconButton size="small" onClick={handleFullscreen}>
                <FullscreenIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Controls */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <ToggleButtonGroup
            value={selectedMetrics}
            onChange={handleMetricChange}
            size="small"
            sx={{ gap: 1 }}
          >
            <ToggleButton value="pm25" sx={{ textTransform: 'none' }}>
              PM2.5
            </ToggleButton>
            <ToggleButton value="pm10" sx={{ textTransform: 'none' }}>
              PM10
            </ToggleButton>
            <ToggleButton value="aqi" sx={{ textTransform: 'none' }}>
              AQI
            </ToggleButton>
          </ToggleButtonGroup>

          <ToggleButtonGroup
            value={chartType}
            exclusive
            onChange={handleChartTypeChange}
            size="small"
          >
            <ToggleButton value="line" sx={{ textTransform: 'none' }}>
              Line
            </ToggleButton>
            <ToggleButton value="area" sx={{ textTransform: 'none' }}>
              Area
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {/* Chart */}
        <ChartContainer>
          <ResponsiveContainer width="100%" height="100%">
            <ChartComponent data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis 
                dataKey="time" 
                tick={{ fontSize: 12 }}
                interval="preserveStartEnd"
              />
              <YAxis 
                tick={{ fontSize: 12 }}
              />
              <RechartsTooltip
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e0e0e0',
                  borderRadius: 8,
                }}
              />
              <Legend />
              
              {selectedMetrics.includes('pm25') && (
                <DataComponent
                  type="monotone"
                  dataKey="pm25"
                  stroke="#ff9800"
                  fill="#ff9800"
                  strokeWidth={2}
                  name="PM2.5 (μg/m³)"
                  dot={false}
                />
              )}
              
              {selectedMetrics.includes('pm10') && (
                <DataComponent
                  type="monotone"
                  dataKey="pm10"
                  stroke="#2196f3"
                  fill="#2196f3"
                  strokeWidth={2}
                  name="PM10 (μg/m³)"
                  dot={false}
                />
              )}
              
              {selectedMetrics.includes('aqi') && (
                <DataComponent
                  type="monotone"
                  dataKey="aqi"
                  stroke="#4caf50"
                  fill="#4caf50"
                  strokeWidth={2}
                  name="AQI"
                  dot={false}
                />
              )}
            </ChartComponent>
          </ResponsiveContainer>
        </ChartContainer>

        {/* Summary Stats */}
        <Box display="flex" justifyContent="space-around" mt={2} pt={2} borderTop="1px solid #e0e0e0">
          {selectedMetrics.includes('pm25') && (
            <Box textAlign="center">
              <Typography variant="caption" color="text.secondary">
                PM2.5 Avg
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {(chartData.reduce((sum, d) => sum + d.pm25, 0) / chartData.length).toFixed(1)}
              </Typography>
            </Box>
          )}
          
          {selectedMetrics.includes('pm10') && (
            <Box textAlign="center">
              <Typography variant="caption" color="text.secondary">
                PM10 Avg
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {(chartData.reduce((sum, d) => sum + d.pm10, 0) / chartData.length).toFixed(1)}
              </Typography>
            </Box>
          )}
          
          {selectedMetrics.includes('aqi') && (
            <Box textAlign="center">
              <Typography variant="caption" color="text.secondary">
                AQI Avg
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {Math.round(chartData.reduce((sum, d) => sum + d.aqi, 0) / chartData.length)}
              </Typography>
            </Box>
          )}
        </Box>
      </CardContent>
    </StyledCard>
  );
};

export default TrendChart;