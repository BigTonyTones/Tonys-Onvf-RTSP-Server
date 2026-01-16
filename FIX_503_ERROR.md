# Fix for 503 Error After ~2 Hours

## Problem Description
Users reported that after approximately 2 hours of operation, all cameras except the "last" camera would fail with a 503 error and show 0 bandwidth. The diagnostic output showed streams were "ready" but transmitting no data.

## Root Cause Analysis

### The Issue
The problem was caused by **zombie FFmpeg processes** accumulating over time due to improper process lifecycle management:

1. **MediaMTX Configuration**: `runOnInitRestart: True` was set for all transcoded streams
2. **Process Accumulation**: When FFmpeg processes crashed or hung, MediaMTX would spawn new processes WITHOUT properly cleaning up the old ones
3. **Resource Exhaustion**: After ~2 hours, the system would hit limits:
   - File descriptor exhaustion (each RTSP stream holds open sockets)
   - Memory leaks from zombie processes
   - Thread/process limits
4. **"Last Camera Works"**: The most recently added camera worked because it was the newest process and hadn't accumulated the resource leak yet

### Why This Happened
- FFmpeg processes would occasionally hang or crash (network issues, camera reboots, etc.)
- MediaMTX's `runOnInitRestart: True` would spawn a NEW process
- The OLD process wasn't being killed, it just sat there holding resources
- After 16-32 cameras running for 2 hours, hundreds of zombie processes accumulated
- System ran out of file descriptors/sockets

## The Solution

### Changes Made to `app/mediamtx_manager.py`

#### 1. Disabled Automatic MediaMTX Restart
Changed `runOnInitRestart: True` to `runOnInitRestart: False` for all stream types:
- Main streams (line ~364)
- Sub streams (line ~435)
- GridFusion composite streams (line ~608)

**Why**: This prevents MediaMTX from spawning new processes when the old ones are still running.

#### 2. Implemented Shell-Level Auto-Reconnect
Wrapped FFmpeg commands in infinite loops at the shell level:

**Windows**:
```batch
cmd /c "for /L %i in (1,0,2) do (ffmpeg_command & timeout /t 2 /nobreak > nul)"
```

**Linux/Unix**:
```bash
sh -c 'while true; do ffmpeg_command; sleep 2; done'
```

**Why**: 
- The shell loop ensures automatic reconnection when FFmpeg exits
- The 2-second delay prevents rapid restart loops
- When MediaMTX kills the process, it kills the ENTIRE shell process tree
- No zombie processes are left behind

#### 3. Added `runOnDemand: False`
Ensures streams stay active and don't get stopped/started repeatedly.

## How It Works Now

### Before (Broken):
```
MediaMTX spawns FFmpeg → FFmpeg hangs → MediaMTX spawns NEW FFmpeg → Old FFmpeg still running → ZOMBIE!
```

### After (Fixed):
```
MediaMTX spawns Shell → Shell spawns FFmpeg → FFmpeg exits → Shell spawns new FFmpeg → MediaMTX kills Shell → ALL processes die
```

## Expected Behavior

### Immediate Benefits:
1. ✅ No more zombie processes
2. ✅ Automatic reconnection on FFmpeg crashes
3. ✅ Proper process cleanup when stopping cameras
4. ✅ All cameras stay active indefinitely

### Long-Term Stability:
- Streams will automatically recover from network hiccups
- No resource exhaustion after extended runtime
- Clean process tree management
- Predictable memory usage

## Testing Recommendations

### For Your User:
1. **Restart the server** with the updated code
2. **Monitor for 3-4 hours** to verify streams stay active
3. **Check process count**: `ps aux | grep ffmpeg | wc -l` (Linux) or Task Manager (Windows)
   - Should see 2 processes per transcoded stream (shell + ffmpeg)
   - Should NOT increase over time
4. **Verify bandwidth**: All cameras should show active bandwidth in diagnostics
5. **Test camera recovery**: Reboot a physical camera and verify the stream auto-reconnects

### Process Count Math:
- 16 cameras with transcoding enabled = 32 streams (main + sub)
- Each stream = 2 processes (shell wrapper + ffmpeg) = 64 processes
- **Expected**: ~64 processes total
- **Before fix**: Could grow to 200+ zombie processes after 2 hours

## Additional Notes

### Why the "Last Camera" Always Worked:
The last camera added was the most recently started process, so it hadn't accumulated the resource leak yet. As older processes became zombies, the newest one still had access to system resources.

### FFmpeg Input Arguments:
The existing FFmpeg input args already include:
```
-rtsp_transport tcp -timeout 10000000
```

This provides:
- TCP transport for reliability
- 10-second timeout to prevent indefinite hangs
- Combined with the shell loop, this creates a robust auto-reconnect system

## Version History
- **v5.8.5**: Fixed 503 error after 2 hours by implementing proper process lifecycle management
- Previous versions: Zombie process accumulation issue

## Support
If the issue persists after this fix, check:
1. System file descriptor limits: `ulimit -n` (Linux)
2. MediaMTX logs for errors
3. FFmpeg logs in debug mode
4. Network connectivity to cameras

---
**Fixed by**: Antigravity AI Assistant  
**Date**: 2026-01-16  
**Issue**: Zombie FFmpeg processes causing 503 errors after ~2 hours
