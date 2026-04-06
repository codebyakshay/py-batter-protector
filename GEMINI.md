# py-battery-protector

A Python-based utility to monitor and manage macOS battery health by keeping charge levels within a healthy 30-82% range with advanced "Sailing Mode" logic.

## Core Purpose
Automate the monitoring of internal battery state and provides proactive notifications to extend battery lifecycle by avoiding micro-cycles.

## Logic (30-82-50 Rule)
- **High Threshold**: Alert at **82%** (to unplug).
- **Sailing Mode**: Once at 82%, do not alert to plug back in until reaching **50%**.
- **Low Threshold**: Alert at **30%** (critical recharge).

## Tech Stack
- **Runtime**: Python 3.12+
- **Commands**: `pmset`, `osascript` (for notifications)
- **Framework**: GSD (Get Shit Done) for planning and execution.

## Standards
- **Functional**: Success is measured by observable battery state changes and notification deliveries.
- **Security**: No sudo permissions unless strictly required for `pmset` modifications (D-01: prefer non-sudo discovery first).
- **Architecture**: Modular monitoring loops.
