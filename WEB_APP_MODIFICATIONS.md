# Web App Modifications Summary

## Overview
Modified the CostMinimizer web application to:
1. Use the `App` class directly instead of MCP wrapper
2. Stream logs in real-time using Server-Sent Events (SSE)
3. Display logs in the **reports-status** panel (not credentials-status)
4. Provide Excel file download functionality

## Changes Made

### Backend (src/CostMinimizer/web/app.py)

#### 1. Removed MCP Dependency
- Removed import of `CostMinimizerTools` from MCP module
- Now directly uses `App` class from `CostMinimizer.CostMinimizer`

#### 2. Added SSE Log Streaming
- Created `SSELogHandler` class to capture logs and send to queue
- Added `log_queues` dictionary to store per-session log queues
- Modified `/api/run-reports` to:
  - Generate unique session ID for each report run
  - Start report generation in background thread
  - Return session ID immediately for SSE connection

#### 3. New Endpoints
- **`/api/stream-logs/<session_id>`**: SSE endpoint that streams logs in real-time
  - Sends log messages as they occur
  - Extracts Excel file path from logs
  - Sends completion/error messages
  - Includes keepalive messages to maintain connection

- **`/api/download-report/<path:filepath>`**: Download endpoint for Excel files
  - Validates file type (must be .xlsx)
  - Checks file existence
  - Sends file as attachment

#### 4. Background Report Execution
- `execute_reports_background()` function runs in separate thread
- Captures all logs using custom log handler
- Extracts Excel file path from log messages using regex
- Properly cleans up environment and logging handlers

### Frontend (src/CostMinimizer/web/static/js/app.js)

#### 1. Modified `handleRunReports()` Function
- Clears **reports-status** panel and adds log container (changed from credentials-status)
- Initiates report generation via POST to `/api/run-reports`
- Receives session ID and calls `streamReportLogs()`

#### 2. New `streamReportLogs()` Function
- Establishes SSE connection to `/api/stream-logs/<session_id>`
- Handles different message types:
  - `log`: Regular log messages (displayed in log container)
  - `excel`: Excel file path notification
  - `success`: Success messages (highlighted in green)
  - `error`: Error messages (highlighted in red)
  - `done`: Completion message (closes connection, shows download link)
  - `keepalive`: Connection maintenance
- Updates **reports-status** div with final success/error message
- Preserves log content when showing final status

#### 3. Log Display Features
- Real-time log streaming in monospace font in **reports-status** div
- Auto-scroll to bottom as new logs arrive
- Color highlighting for important messages (errors in red, success in green)
- Excel file path extraction and download link generation
- Final status message with download link displayed in reports-status

### Styling (src/CostMinimizer/web/static/css/style.css)

#### Added Log Container Styles
- Dark theme terminal-like appearance (#1e1e1e background)
- Monospace font for log readability
- Custom scrollbar styling
- Max height with overflow-y auto
- Proper spacing and padding
- Min height for reports-status log container

#### Enhanced Status Message Styles
- Added h3 heading support with proper colors for success/error/info states
- Styled download links (blue, underlined, bold)
- Hover effects for links
- Specific styling for reports-status div states

## How It Works

### Flow Diagram
```
User clicks "Generate Reports"
    ↓
Frontend: POST /api/run-reports
    ↓
Backend: Creates session ID, starts background thread
    ↓
Backend: Returns session ID immediately
    ↓
Frontend: Connects to SSE /api/stream-logs/<session_id>
    ↓
Backend Thread: Runs CostMinimizer App
    ↓
Backend Thread: Captures logs via SSELogHandler
    ↓
Backend Thread: Sends logs to queue
    ↓
SSE Endpoint: Reads from queue, streams to frontend
    ↓
Frontend: Displays logs in real-time
    ↓
Backend Thread: Extracts Excel file path from logs
    ↓
Backend Thread: Sends DONE message
    ↓
Frontend: Shows download link
    ↓
User clicks download link
    ↓
Backend: Serves Excel file via /api/download-report
```

## Key Features

1. **Real-time Log Streaming**: Users see logs as they happen, not after completion
2. **Non-blocking**: Report generation runs in background, UI remains responsive
3. **Excel File Detection**: Automatically extracts file path from logs
4. **Download Link**: Provides direct download link for generated Excel report
5. **Error Handling**: Proper error messages and connection cleanup
6. **Visual Feedback**: Color-coded log messages for easy scanning

## Example Log Message Parsing

The system looks for this pattern in logs:
```
CostMinimizer.report_output_handler.report_output_handler - INFO - !!! Excel Report Output saved into: /root/cow/636706114485/-2026-02-15-13-11/CostMinimizer.xlsx
```

Regex pattern used:
```python
r'Excel Report Output saved into:\s*(.+\.xlsx)'
```

This extracts: `/root/cow/636706114485/-2026-02-15-13-11/CostMinimizer.xlsx`

## Security Considerations

1. **File Download Validation**: Only .xlsx files can be downloaded
2. **File Existence Check**: Verifies file exists before serving
3. **Session Management**: Each report run has unique session ID
4. **Credential Storage**: AWS credentials stored in Flask session (server-side)
5. **Environment Cleanup**: Properly restores environment variables after execution

## Testing

To test the modifications:

1. Start the web server:
   ```bash
   python src/CostMinimizer/web/app.py
   ```

2. Navigate to `http://localhost:8000`

3. Enter AWS credentials and validate

4. Select reports and click "Generate Reports"

5. Observe:
   - Logs streaming in real-time in credentials-status panel
   - Excel file path appearing in logs
   - Download link appearing when complete
   - Ability to download the Excel file

## Future Enhancements

1. Add progress percentage indicator
2. Support multiple concurrent report generations
3. Add log filtering/search functionality
4. Store report history with download links
5. Add WebSocket support for bidirectional communication
6. Implement log level filtering (INFO, WARNING, ERROR)
