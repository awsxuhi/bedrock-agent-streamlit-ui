# Bedrock Agent Streamlit UI Architecture

This document outlines the architecture of the Bedrock Agent Streamlit UI application, which provides a web-based interface for interacting with Amazon Bedrock Agents.

## System Overview

The Bedrock Agent Streamlit UI is a Python-based web application that leverages Streamlit to create an interactive interface for Amazon Bedrock Agents. The application allows users to interact with various Bedrock Agents through a chat interface, with support for multiple agents across different AWS regions.

## Architecture Components

### 1. User Interface Layer

The UI layer is built using Streamlit and consists of:

- **Sidebar Configuration Panel**: Allows users to select and configure agents
  - Preset agent selection
  - Custom agent configuration (Agent Name, ID, Alias ID, Region)
  - Language toggle (English/Chinese)
- **Main Chat Interface**: Provides the chat functionality
  - Message history display
  - Input field for user queries
  - Response streaming from the agent
  - Visualization of agent processing steps

### 2. Application Logic Layer

The application logic is divided into several components:

- **Session Management**: Handles user session state, including:
  - Agent configuration
  - Message history
  - Language preferences
- **Agent Configuration**: Manages agent settings through:
  - Preset configurations from `config.py`
  - Custom configurations via the UI
  - Dynamic agent ID and alias ID resolution
- **Agent Invocation**: Handles communication with Amazon Bedrock, including:
  - Agent request formatting
  - Response processing
  - Error handling
- **Trace Visualization**: Processes and displays agent execution traces:
  - Routing classifier traces (agent selection)
  - Orchestration traces (reasoning steps)
  - Tool invocation traces
  - Knowledge base query traces

### 3. AWS Integration Layer

The AWS integration layer handles communication with AWS services:

- **Bedrock Agent Runtime**: For invoking agents and streaming responses
- **Bedrock Agent**: For retrieving agent metadata and configurations
- **Multi-region Support**: For working with agents across different AWS regions

## Data Flow

1. **Initialization**:

   - Application loads configurations from `config.py`
   - Session state is initialized
   - Agent IDs and aliases are resolved

2. **Agent Selection**:

   - User selects a preset agent or configures a custom agent
   - Configuration is applied and stored in session state

3. **User Interaction**:

   - User submits a query through the chat interface
   - Query is sent to the selected Bedrock Agent
   - Response is streamed back to the UI

4. **Response Processing**:
   - Agent response is parsed and displayed
   - Execution traces are visualized
   - Message history is updated

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit UI                             │
│                                                                 │
│  ┌───────────────────────┐           ┌─────────────────────┐    │
│  │   Sidebar Config      │           │   Chat Interface    │    │
│  │                       │           │                     │    │
│  │  - Agent Selection    │           │  - Message History  │    │
│  │  - Custom Config      │           │  - User Input       │    │
│  │  - Language Toggle    │           │  - Agent Response   │    │
│  └───────────────────────┘           └─────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Application Logic                           │
│                                                                 │
│  ┌───────────────────────┐           ┌─────────────────────┐    │
│  │  Session Management   │           │  Agent Invocation   │    │
│  └───────────────────────┘           └─────────────────────┘    │
│                                                                 │
│  ┌───────────────────────┐           ┌─────────────────────┐    │
│  │  Agent Configuration  │           │  Trace Processing   │    │
│  └───────────────────────┘           └─────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS Integration                            │
│                                                                 │
│  ┌───────────────────────┐           ┌─────────────────────┐    │
│  │  Bedrock Agent Runtime│           │   Bedrock Agent     │    │
│  └───────────────────────┘           └─────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## File Structure

- `demo_ui.py`: Main application file containing the Streamlit UI and application logic
- `ui_utils.py`: Utility functions for UI components and agent invocation
- `config.py`: Configuration file for preset agent definitions
- `src/utils/bedrock_agent.py`: Helper functions for interacting with Bedrock Agents

## Technical Dependencies

- **Streamlit**: Web application framework
- **Boto3**: AWS SDK for Python
- **PyYAML**: YAML parsing for task configurations
- **AWS Bedrock**: Foundation model service
- **AWS Bedrock Agent**: Agent service for task execution

## Deployment Model

The application is designed to be run locally or deployed as a Streamlit application. It requires:

1. Python environment with required dependencies
2. AWS credentials with appropriate permissions
3. Access to AWS Bedrock and Bedrock Agent services
4. Configured Bedrock Agents in the target AWS account(s)

## Security Considerations

- AWS credentials must be properly configured
- Agent access is controlled through AWS IAM permissions
- No sensitive data is stored in the application itself
- Session data is maintained only for the duration of the session
