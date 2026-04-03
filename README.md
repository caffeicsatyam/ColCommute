<h1 align="center">ColCommute</h1>

<p align="center">
  A multi-agent system built with the Google Agent Development Kit (ADK) to coordinate collaborative commute planning.
</p>

---

## 🚀 Overview

**ColCommute** is an advanced AI system designed to handle complex commute requests. It uses an **Orchestrator** agent to delegate tasks to specialized sub-agents:

- **Routing Agent**: Calculates the best routes, distances, and durations.
- **Pricing Agent**: Estimates fares based on distance and ride type (solo vs. shared).
- **Notification Agent** (Planning): Handles alerts for ride matches.

## 📁 Project Structure

```text
ColCommute/
├── agents/             # Specialized AI agents
│   ├── orchestrator.py # Main brain coordinating sub-agents
│   ├── routing.py      # Route planning logic
│   └── pricing.py      # Fare estimation agent
├── colCommute/         # ADK entry point
│   ├── agent.py        # root_agent definition
│   └── __init__.py     # Package initialization
├── core/               # Shared logic and configuration
│   ├── llm.py          # Unified LLM settings
│   └── memory.py       # Context & memory storage
├── services/           # Backend services (APIs and Databases)
└── .env                # API Keys (Git ignored)
```

## 🛠️ Getting Started

### Prerequisites
- Python 3.10+
- Google ADK (`pip install google-adk`)
- A Gemini API Key

### Setup
1. Clone the repository and add your API key to `.env`:
   ```bash
   GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
   ```

2. Run the agent using the ADK CLI:
   ```bash
   adk run colCommute
   ```

3. Launch the Web UI for a better chat experience:
   ```bash
   adk web
   ```

## 💬 Example Usage

You can ask **ColCommute** complex questions that require multiple steps:

- *"Find a route from San Francisco to San Jose and give me a price estimate for a shared ride."*
- *"I need to go from the airport to downtown. Which route is best and what's the solo fare?"*

---

<p align="center">
  Built with ❤️ using Google ADK
</p>
