# Changelog

All notable changes to the ChangeDetection.io Home Assistant integration will be documented in this file.

## [1.1.0] - 2026-09-16

### Added
- **Exponential Backoff Strategy**: Implements intelligent retry logic to prevent flooding Home Assistant when ChangeDetection.io is unavailable
  - Waits 1 hour after first error, then exponentially increases (2h, 4h, 8h, 24h max)
  - Effectively limits checks to ~1 per day when service is down
  - Respects connection availability before making API requests
- **Connection Error Tracking**: New `ChangeDetectionConnectionError` exception class to distinguish connection failures from API errors
- **Enhanced Service Error Handling**: All service calls now properly handle and report connection unavailability
- **Improved Logging**: Debug logs for backoff status, clear warnings when service is unavailable

### Fixed
- **Repository URL**: Updated README with correct repository URL (`https://github.com/dapuzz/changedetection`)
- **Flood Prevention**: Integration no longer sends repeated requests to ChangeDetection.io when it's unavailable
- **Error Handling**: Coordinator gracefully skips updates during backoff period without raising UpdateFailed errors repeatedly
- **Device Creation**: Added safe fallback for systeminfo data when device is initially created

### Improved
- **Robustness**: Better error differentiation between transient connection issues and API errors
- **User Experience**: Clear error messages inform users when ChangeDetection.io is temporarily unavailable
- **Code Quality**: Enhanced type hints and documentation throughout API client

### Technical Details
- API Client (`api.py`):
  - Added `is_connection_available()` method for backoff checking
  - Added `record_connection_error()` and `reset_connection_error()` methods for error tracking
  - Enhanced `_request()` to respect backoff strategy before making requests
  - Improved timeout and connection error handling

- Integration (`__init__.py`):
  - Updated `async_update_data()` to check connection availability
  - Enhanced all 20+ service handlers with connection error handling
  - Better logging of backoff status and API errors

## [1.0.0] - 2026-09-15

### Initial Release
- Core integration for ChangeDetection.io in Home Assistant
- Sensor platform for monitoring watches and system info
- Button platform for triggering rechecks
- Full service API including:
  - Watch management (create, update, delete, pause, mute)
  - Tag management (create, update, delete)
  - Snapshot and diff retrieval
  - Bulk import functionality
  - Search capabilities
  - Notification management
- Configuration flow for easy setup
