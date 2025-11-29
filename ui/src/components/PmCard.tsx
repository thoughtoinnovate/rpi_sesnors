import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Fade,
  Grow,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
} from '@mui/icons-material';

interface PmData {
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  trendValue?: number;
  lastUpdated: string;
}

interface PmCardProps {
  title: string;
  data: PmData | null;
  loading?: boolean;
  color?: string;
  icon?: React.ReactNode;
}

// Styled components
const StyledCard = styled(Card)<{ cardColor: string }>(({ theme, cardColor }) => ({
  minHeight: 180,
  background: `linear-gradient(135deg, ${cardColor}08 0%, ${cardColor}04 100%)`,
  border: `1px solid ${cardColor}20`,
  position: 'relative',
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '3px',
    background: cardColor,
  },
}));

const ValueDisplay = styled(Typography)<{ valueColor: string }>(({ valueColor }) => ({
  fontSize: '2.5rem',
  fontWeight: 700,
  color: valueColor,
  lineHeight: 1,
}));

const TrendChip = styled(Chip)<{ trendColor: string }>(({ trendColor }) => ({
  backgroundColor: trendColor,
  color: 'white',
  fontWeight: 600,
  fontSize: '0.75rem',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
}));

// Get trend icon
const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
  switch (trend) {
    case 'up':
      return <TrendingUpIcon />;
    case 'down':
      return <TrendingDownIcon />;
    case 'stable':
      return <TrendingFlatIcon />;
    default:
      return <TrendingFlatIcon />;
  }
};

// Get trend color
const getTrendColor = (trend: 'up' | 'down' | 'stable'): string => {
  switch (trend) {
    case 'up':
      return '#f44336'; // Red
    case 'down':
      return '#4caf50'; // Green
    case 'stable':
      return '#ff9800'; // Orange
    default:
      return '#9e9e9e'; // Grey
  }
};

// Get PM level status
const getPmLevel = (value: number, type: 'pm25' | 'pm10'): { level: string; color: string } => {
  if (type === 'pm25') {
    if (value <= 12) return { level: 'Good', color: '#4caf50' };
    if (value <= 35) return { level: 'Moderate', color: '#ff9800' };
    if (value <= 55) return { level: 'Unhealthy for Sensitive', color: '#ff5722' };
    if (value <= 150) return { level: 'Unhealthy', color: '#f44336' };
    if (value <= 250) return { level: 'Very Unhealthy', color: '#9c27b0' };
    return { level: 'Hazardous', color: '#795548' };
  } else {
    if (value <= 54) return { level: 'Good', color: '#4caf50' };
    if (value <= 154) return { level: 'Moderate', color: '#ff9800' };
    if (value <= 254) return { level: 'Unhealthy for Sensitive', color: '#ff5722' };
    if (value <= 354) return { level: 'Unhealthy', color: '#f44336' };
    if (value <= 424) return { level: 'Very Unhealthy', color: '#9c27b0' };
    return { level: 'Hazardous', color: '#795548' };
  }
};

const PmCard: React.FC<PmCardProps> = React.memo(({ 
  title, 
  data, 
  loading = false, 
  color = '#1976d2',
  icon 
}) => {
  if (loading || !data) {
    return (
      <StyledCard cardColor="#e0e0e0">
        <CardContent sx={{ p: 3 }}>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={140}>
            <Typography variant="h6" color="text.secondary">
              Loading {title} data...
            </Typography>
          </Box>
        </CardContent>
      </StyledCard>
    );
  }

  const trendColor = getTrendColor(data.trend);
  const trendIcon = getTrendIcon(data.trend);
  const pmLevel = getPmLevel(data.value, title.toLowerCase().includes('2.5') ? 'pm25' : 'pm10');

  return (
    <Grow in={true} timeout={600}>
      <StyledCard cardColor={color}>
        <CardContent sx={{ p: 3 }}>
          <Box display="flex" flexDirection="column" alignItems="center" textAlign="center">
            {/* Header */}
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              {icon}
              <Typography variant="h6" color="text.secondary" fontWeight={600}>
                {title}
              </Typography>
            </Box>

            {/* Value Display */}
            <Fade in={true} timeout={800}>
              <Box>
                <ValueDisplay valueColor={color} variant="h2">
                  {data.value}
                </ValueDisplay>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {data.unit}
                </Typography>
              </Box>
            </Fade>

            {/* Level Status */}
            <Chip
              label={pmLevel.level}
              size="small"
              sx={{
                mb: 2,
                backgroundColor: pmLevel.color,
                color: 'white',
                fontWeight: 600,
                fontSize: '0.75rem',
              }}
            />

            {/* Trend Indicator */}
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <TrendChip
                icon={trendIcon}
                label={data.trend}
                trendColor={trendColor}
                size="small"
              />
              {data.trendValue && (
                <Typography variant="caption" color="text.secondary">
                  {data.trendValue > 0 ? '+' : ''}{data.trendValue}%
                </Typography>
              )}
            </Box>

            {/* Last Updated */}
            <Typography variant="caption" color="text.secondary">
              Updated {new Date(data.lastUpdated).toLocaleTimeString()}
            </Typography>
          </Box>
        </CardContent>
      </StyledCard>
    </Grow>
  );
});

PmCard.displayName = 'PmCard';

export default PmCard;