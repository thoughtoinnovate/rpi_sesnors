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
import { getAqiColor, getAqiLevel } from '../theme';
import { AqiData } from '../store';

interface AqiCardProps {
  data: AqiData | null;
  loading?: boolean;
}

// Styled components
const StyledCard = styled(Card)<{ aqiColor: string }>(({ aqiColor }) => ({
  minHeight: 200,
  background: `linear-gradient(135deg, ${aqiColor}15 0%, ${aqiColor}08 100%)`,
  border: `2px solid ${aqiColor}30`,
  position: 'relative',
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '4px',
    background: aqiColor,
  },
}));

const AqiValue = styled(Typography)<{ aqiColor: string }>(({ aqiColor, theme }) => ({
  fontSize: 'clamp(2.5rem, 8vw, 4rem)', // Responsive font size
  fontWeight: 700,
  color: aqiColor,
  lineHeight: 1,
  textShadow: '0 2px 4px rgba(0,0,0,0.1)',
  [theme.breakpoints.down('sm')]: {
    fontSize: '2.5rem',
  },
}));

const LiveIndicator = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  marginTop: theme.spacing(1),
}));

const PulsingDot = styled(Box)<{ color: string }>(({ color }) => ({
  width: 8,
  height: 8,
  borderRadius: '50%',
  backgroundColor: color,
  animation: 'pulse 2s infinite',
  '@keyframes pulse': {
    '0%': {
      transform: 'scale(0.8)',
      opacity: 1,
    },
    '50%': {
      transform: 'scale(1.2)',
      opacity: 0.7,
    },
    '100%': {
      transform: 'scale(0.8)',
      opacity: 1,
    },
  },
}));

// Health messages based on AQI level
const getHealthMessage = (aqi: number): string => {
  if (aqi <= 50) return 'Air quality is good. Enjoy outdoor activities!';
  if (aqi <= 100) return 'Air quality is acceptable. Sensitive individuals should consider limiting prolonged outdoor exertion.';
  if (aqi <= 150) return 'Members of sensitive groups may experience health effects. The general public is not likely to be affected.';
  if (aqi <= 200) return 'Everyone may begin to experience health effects. Members of sensitive groups may experience more serious health effects.';
  if (aqi <= 300) return 'Health alert: everyone may experience more serious health effects.';
  return 'Health warning of emergency conditions. The entire population is more likely to be affected.';
};

const AqiCard: React.FC<AqiCardProps> = React.memo(({ data, loading = false }) => {
  if (loading || !data) {
    return (
      <StyledCard aqiColor="#e0e0e0">
        <CardContent sx={{ p: 3 }}>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={160}>
            <Typography variant="h6" color="text.secondary">
              Loading AQI data...
            </Typography>
          </Box>
        </CardContent>
      </StyledCard>
    );
  }

  const aqiColor = getAqiColor(data.aqi);
  const aqiLevel = getAqiLevel(data.aqi);
  const healthMessage = getHealthMessage(data.aqi);

  return (
    <Grow in={true} timeout={600}>
      <StyledCard aqiColor={aqiColor}>
        <CardContent sx={{ p: 3 }}>
          <Box display="flex" flexDirection="column" alignItems="center" textAlign="center">
            {/* AQI Value */}
            <Fade in={true} timeout={800}>
              <AqiValue aqiColor={aqiColor} variant="h1">
                {data.aqi}
              </AqiValue>
            </Fade>

            {/* AQI Level */}
            <Chip
              label={aqiLevel}
              sx={{
                mt: 1,
                mb: 2,
                backgroundColor: aqiColor,
                color: 'white',
                fontWeight: 600,
                fontSize: '0.875rem',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}
            />

            {/* Health Message */}
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                mb: 2,
                lineHeight: 1.4,
                maxWidth: 300,
              }}
            >
              {healthMessage}
            </Typography>

            {/* Live Indicator */}
            <LiveIndicator>
              <PulsingDot color={aqiColor} />
              <Typography variant="caption" color="text.secondary">
                Live • Updated {new Date(data.timestamp).toLocaleTimeString()}
              </Typography>
            </LiveIndicator>
          </Box>
        </CardContent>
      </StyledCard>
    </Grow>
  );
});

AqiCard.displayName = 'AqiCard';

export default AqiCard;