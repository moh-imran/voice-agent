# Voice Agent

A robust Python/FastAPI architecture for a production-grade Voice Agent engine. 
This application provides full feature parity with its TypeScript predecessor, modularized using a plugin registry for adapters and skills.

## Features

- **Telephony Integration:** Connects with providers like Twilio.
- **Speech-to-Text (STT) & Text-to-Speech (TTS):** Uses Whisper for high-quality speech processing.
- **CRM Integration:** Syncs with Salesforce.
- **Commerce Integration:** Connects with Magento.
- **Ticketing System:** Integrates with Zendesk.
- **Modular Skills Engine:** Includes skills for Authentication, Order Tracking, Complaints, FAQ, and Handoff.
- **Multi-language Support:** Configurable language templates and prompts.
- **LLM Engine:** Powered by GPT-4o for intelligent routing and context management.

## Setup Instructions

### Prerequisites

- Python 3.9+
- Redis server running locally or accessible remotely

### Installation

1. **Clone the repository and navigate into it.**
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. **Environment Variables:**
   Copy the example environment file and fill in your credentials.
   ```bash
   cp .env.example .env
   ```

2. **Application Config:**
   Update `config.yaml` to change active providers, language support, or LLM settings.

### Running the Application

To start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

## Running Tests

To run the test suite:

```bash
pytest
```

## Project Structure

- `app/` - Main application logic, including the FastAPI setup.
  - `adapters/` - Integrations for external services (CRM, Commerce, Telephony, etc.).
  - `core/` - Core configuration, logging, prompts, and registry logic.
  - `engine/` - Context management and LLM orchestration.
  - `skills/` - Modular capabilities the agent can execute.
  - `admin/` - Admin dashboard templates and logic.
- `config.yaml` - Declarative configuration of the active components.
- `tests/` - End-to-end and unit tests for the components.
