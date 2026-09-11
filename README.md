# Computer Use Agent

An autonomous AI agent that can understand natural-language computer tasks,
interact with the computer, observe the results, and verify task completion.

## Project Goal

The goal of this project is to build a Computer Use Agent that follows this
core loop:

User Goal
    ↓
Task Understanding
    ↓
Planning
    ↓
Action Selection
    ↓
Computer Action
    ↓
Observation
    ↓
Verification
    ↓
Done / Next Action

## Current Development Phase

Phase 1 - Computer Control

The current goal is to create a reliable computer-control layer that can:

- Take screenshots
- Move the mouse
- Click
- Type text
- Press keyboard keys
- Open applications
- Open URLs

## Project Structure

```text
com_use/
│
├── computer/       # Computer control functionality
├── docs/           # Project documentation
├── tests/          # Tests for project components
├── README.md       # Project overview
├── requirements.txt
└── .gitignore