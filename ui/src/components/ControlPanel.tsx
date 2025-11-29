import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Switch,
  Button,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  Alert,
  Chip,
  LinearProgress,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  Schedule as ScheduleIcon,
  Power as PowerIcon,
  PowerOff as PowerOffIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { SchedulerStatus } from '../store';
import apiClient from '../api';

interface ControlPanelProps {
  schedulerStatus: SchedulerStatus | null;
  loading?: boolean;
  onStatusUpdate?: () => void;
}

// Styled components
const StyledCard = styled(Card)(({ theme }) => ({
  minHeight: 300,
  background: `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${theme.palette.grey[50]} 100%)`,
  border: `1px solid ${theme.palette.divider}`,
  position: 'relative',
  overflow: 'hidden',
}));

const ControlSection = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2, 0),
  '&:not(:last-child)': {
    borderBottom: `1px solid ${theme.palette.divider}`,
  },
}));

const StatusChip = styled(Chip)<{ statusColor: string }>(({ statusColor }) => ({
  backgroundColor: statusColor,
  color: 'white',
  fontWeight: 600,
  fontSize: '0.75rem',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
}));

const ControlPanel: React.FC<ControlPanelProps> = ({ 
  schedulerStatus, 
  loading = false,
  onStatusUpdate 
}) => {
  const [schedulerEnabled, setSchedulerEnabled] = useState(schedulerStatus?.isRunning || false);
  const [sensorPower, setSensorPower] = useState(true); // Assume sensor is powered on
  const [interval, setInterval] = useState(schedulerStatus?.interval || 30);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSchedulerToggle = async () => {
    setActionLoading(true);
    setError(null);
    
    try {
      if (schedulerEnabled) {
        await apiClient.stopScheduler();
        setSchedulerEnabled(false);
      } else {
        await apiClient.startScheduler();
        setSchedulerEnabled(true);
      }
      
      if (onStatusUpdate) {
        onStatusUpdate();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle scheduler');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSensorPowerToggle = async () => {
    setActionLoading(true);
    setError(null);
    
    try {
      if (sensorPower) {
        await apiClient.sleepSensor();
        setSensorPower(false);
      } else {
        await apiClient.wakeSensor();
        setSensorPower(true);
      }
      
      if (onStatusUpdate) {
        onStatusUpdate();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle sensor power');
    } finally {
      setActionLoading(false);
    }
  };

  const handleIntervalChange = async (newInterval: number) => {
    setInterval(newInterval);
    // In a real implementation, this would update the scheduler interval
    // For now, we'll just update the local state
  };

  const handleRefresh = async () => {
    setActionLoading(true);
    setError(null);
    
    try {
      if (onStatusUpdate) {
        onStatusUpdate();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh status');
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusColor = (status: boolean): string => {
    return status ? '#4caf50' : '#f44336';
  };

  const getStatusText = (status: boolean): string => {
    return status ? 'Running' : 'Stopped';
  };

  if (loading) {
    return (
      <StyledCard>
        <CardContent sx={{ p: 3 }}>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={250}>
            <Typography variant="h6" color="text.secondary">
              Loading control panel...
            </Typography>
          </Box>
        </CardContent>
      </StyledCard>
    );
  }

  return (
    <StyledCard>
      <CardContent sx={{ p: 3 }}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6" color="text.secondary" fontWeight={600}>
            Control Panel
          </Typography>
          
          <Button
            variant="outlined"
            size="small"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={actionLoading}
          >
            Refresh
          </Button>
        </Box>

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Scheduler Controls */}
        <ControlSection>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Box display="flex" alignItems="center" gap={1}>
              <ScheduleIcon color="action" />
              <Typography variant="subtitle1" fontWeight={600}>
                Scheduler
              </Typography>
              <StatusChip
                label={getStatusText(schedulerEnabled)}
                statusColor={getStatusColor(schedulerEnabled)}
                size="small"
              />
            </Box>
            
            <FormControlLabel
              control={
                <Switch
                  checked={schedulerEnabled}
                  onChange={handleSchedulerToggle}
                  disabled={actionLoading}
                />
              }
              label="Enable"
            />
          </Box>

          <Box display="flex" alignItems="center" gap={2}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Interval</InputLabel>
              <Select
                value={interval}
                onChange={(e) => handleIntervalChange(Number(e.target.value))}
                label="Interval"
                disabled={!schedulerEnabled || actionLoading}
              >
                <MenuItem value={10}>10 seconds</MenuItem>
                <MenuItem value={30}>30 seconds</MenuItem>
                <MenuItem value={60}>1 minute</MenuItem>
                <MenuItem value={300}>5 minutes</MenuItem>
                <MenuItem value={600}>10 minutes</MenuItem>
              </Select>
            </FormControl>

            {schedulerStatus?.nextRun && (
              <Typography variant="body2" color="text.secondary">
                Next: {new Date(schedulerStatus.nextRun).toLocaleTimeString()}
              </Typography>
            )}
          </Box>
        </ControlSection>

        <Divider sx={{ my: 2 }} />

        {/* Sensor Power Controls */}
        <ControlSection>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Box display="flex" alignItems="center" gap={1}>
              {sensorPower ? (
                <PowerIcon color="action" />
              ) : (
                <PowerOffIcon color="action" />
              )}
              <Typography variant="subtitle1" fontWeight={600}>
                Sensor Power
              </Typography>
              <StatusChip
                label={sensorPower ? 'Active' : 'Sleeping'}
                statusColor={getStatusColor(sensorPower)}
                size="small"
              />
            </Box>
            
            <FormControlLabel
              control={
                <Switch
                  checked={sensorPower}
                  onChange={handleSensorPowerToggle}
                  disabled={actionLoading}
                />
              }
              label="Power"
            />
          </Box>

          <Box display="flex" gap={1}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<StartIcon />}
              onClick={() => handleSensorPowerToggle()}
              disabled={sensorPower || actionLoading}
              fullWidth
            >
              Wake Sensor
            </Button>
            <Button
              variant="outlined"
              size="small"
              startIcon={<StopIcon />}
              onClick={() => handleSensorPowerToggle()}
              disabled={!sensorPower || actionLoading}
              fullWidth
            >
              Sleep Sensor
            </Button>
          </Box>
        </ControlSection>

        {/* Action Loading Indicator */}
        {actionLoading && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Processing request...
            </Typography>
          </Box>
        )}
      </CardContent>
    </StyledCard>
  );
};

export default ControlPanel;