import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Grow,
  LinearProgress,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  Power as PowerIcon,
  PowerOff as PowerOffIcon,
  Thermostat as ThermostatIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { SensorStatus } from '../store';

interface SensorStatusCardProps {
  status: SensorStatus | null;
  loading?: boolean;
}

// Styled components
const StyledCard = styled(Card)(({ theme }) => ({
  minHeight: 200,
  background: `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${theme.palette.grey[50]} 100%)`,
  border: `1px solid ${theme.palette.divider}`,
  position: 'relative',
  overflow: 'hidden',
}));

const StatusChip = styled(Chip)<{ statusColor: string }>(({ statusColor }) => ({
  backgroundColor: statusColor,
  color: 'white',
  fontWeight: 600,
  fontSize: '0.75rem',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
}));

const StatusItem = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  padding: theme.spacing(1, 0),
  borderBottom: `1px solid ${theme.palette.divider}`,
  '&:last-child': {
    borderBottom: 'none',
  },
}));

const getStatusColor = (status: boolean): string => {
  return status ? '#4caf50' : '#f44336';
};

const getStatusText = (status: boolean): string => {
  return status ? 'Connected' : 'Disconnected';
};

const getPowerStatusText = (sleeping: boolean): string => {
  return sleeping ? 'Sleeping' : 'Active';
};

const getWarmupProgress = (warmedUp: boolean): number => {
  return warmedUp ? 100 : Math.floor(Math.random() * 80) + 10; // Mock progress
};

const SensorStatusCard: React.FC<SensorStatusCardProps> = ({ 
  status, 
  loading = false 
}) => {
  if (loading || !status) {
    return (
      <StyledCard>
        <CardContent sx={{ p: 3 }}>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={160}>
            <Typography variant="h6" color="text.secondary">
              Loading sensor status...
            </Typography>
          </Box>
        </CardContent>
      </StyledCard>
    );
  }

  const connectionColor = getStatusColor(status.connected);
  const powerColor = status.sleeping ? '#ff9800' : '#4caf50';
  const warmupProgress = getWarmupProgress(status.warmedUp);
  const warmupColor = status.warmedUp ? '#4caf50' : '#ff9800';

  return (
    <Grow in={true} timeout={600}>
      <StyledCard>
        <CardContent sx={{ p: 3 }}>
          <Box display="flex" flexDirection="column" gap={2}>
            {/* Header */}
            <Typography variant="h6" color="text.secondary" fontWeight={600}>
              Sensor Status
            </Typography>

            {/* Connection Status */}
            <StatusItem>
              {status.connected ? (
                <WifiIcon sx={{ color: connectionColor }} />
              ) : (
                <WifiOffIcon sx={{ color: connectionColor }} />
              )}
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Connection
                </Typography>
                <Typography variant="body1" fontWeight={600}>
                  {getStatusText(status.connected)}
                </Typography>
              </Box>
              <StatusChip
                label={getStatusText(status.connected)}
                statusColor={connectionColor}
                size="small"
              />
            </StatusItem>

            {/* Power Status */}
            <StatusItem>
              {status.sleeping ? (
                <PowerOffIcon sx={{ color: powerColor }} />
              ) : (
                <PowerIcon sx={{ color: powerColor }} />
              )}
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Power State
                </Typography>
                <Typography variant="body1" fontWeight={600}>
                  {getPowerStatusText(status.sleeping)}
                </Typography>
              </Box>
              <StatusChip
                label={getPowerStatusText(status.sleeping)}
                statusColor={powerColor}
                size="small"
              />
            </StatusItem>

            {/* Warmup Status */}
            <StatusItem>
              <ThermostatIcon sx={{ color: warmupColor }} />
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Warmup Status
                </Typography>
                <Typography variant="body1" fontWeight={600}>
                  {status.warmedUp ? 'Ready' : 'Warming up'}
                </Typography>
                {!status.warmedUp && (
                  <Box sx={{ mt: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={warmupProgress}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'grey.200',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: warmupColor,
                          borderRadius: 3,
                        },
                      }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {warmupProgress}% complete
                    </Typography>
                  </Box>
                )}
              </Box>
              <StatusChip
                label={status.warmedUp ? 'Ready' : 'Warming'}
                statusColor={warmupColor}
                size="small"
              />
            </StatusItem>

            {/* Last Reading */}
            <StatusItem>
              <ScheduleIcon sx={{ color: 'text.secondary' }} />
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Last Reading
                </Typography>
                <Typography variant="body1" fontWeight={600}>
                  {new Date(status.lastReading).toLocaleString()}
                </Typography>
              </Box>
            </StatusItem>
          </Box>
        </CardContent>
      </StyledCard>
    </Grow>
  );
};

export default SensorStatusCard;