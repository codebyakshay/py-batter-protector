# Roadmap: py-battery-protector

**Goal**: Extend battery lifespan by automating the 30-82% charge rule via macOS command-line tools.

## Phases

### 01: Core Monitoring [MON]
**Goal**: Scriptable access to real-time battery percentage and charging state.
**Requirements**:
- [MON-01]: Parse `pmset -g batt` to integer percentage.
- [MON-02]: Detect and report battery power vs. AC power.
- [MON-03]: Define modular monitor class for loop execution with 30-82% threshold logic.
- [MON-04]: Implement "Sailing Mode" (50% restart floor).

### 02: Intelligent Notifications [NOT]
**Goal**: User-facing alerts for critical thresholds (30% and 82%).
**Requirements**:
- [NOT-01]: Trigger native macOS notifications using `osascript`.
- [NOT-02]: Implement threshold throttling to avoid spam.
- [NOT-03]: Support custom notification messages and icons.

### 03: Automated Persistence [SYS]
**Goal**: Headless background execution (Daemonize).
**Requirements**:
- [SYS-01]: Configure `launchd` plist for auto-startup.
- [SYS-02]: Handle system sleep/wake event gracefully.
- [SYS-03]: Add logging for state transitions and battery health trends.
