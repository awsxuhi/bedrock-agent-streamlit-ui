# Streamlit Demo UI

A Streamlit-based user interface that can be used with any text-based Bedrock agent by updating the `config.py` file. Supports agents across multiple AWS regions.

## Using with Any Bedrock Agent

To add your own agent:

1. Add a new configuration to the `bot_configs` list in `config.py`:

```python
{
    "bot_name": "Your Bot Name",    # Display name in the UI
    "agent_name": "your_agent_id",  # Your Bedrock agent ID
    "region": "us-east-1",          # AWS region where your agent is deployed (optional, defaults to us-east-1)
    "start_prompt": "Initial message to show users",
    "session_attributes": {         # Optional: Include if your agent needs specific session attributes
        "sessionAttributes": {      # Custom key-value pairs for your agent's session
            "key1": "value1",
            "key2": "value2"
        },
        "promptSessionAttributes": {} # Additional prompt-specific attributes if needed
    }
}
```

### Multi-Region Support

The application now supports agents deployed in different AWS regions. To use an agent from a specific region:

1. Add the `region` field to your agent's configuration in `config.py`
2. The application will automatically use the specified region when:
   - Looking up agent IDs and aliases
   - Invoking the agent
   - Processing agent responses

## Tested Demo Examples

The following demos have been tested with this UI and can be found in their respective folders of project (https://github.com/awslabs/amazon-bedrock-agent-samples):

- **Sports Team Poet** (`/examples/multi_agent_collaboration/team_poems_agent/`): Creates poems about sports teams
- **Portfolio Assistant** (`/examples/multi_agent_collaboration/portfolio_assistant_agent/`): Analyzes stock tickers
- **Trip Planner** (`/examples/multi_agent_collaboration/trip_planner_agent/`): Generates travel itineraries
- **Voyage Virtuoso** (`/examples/multi_agent_collaboration/voyage_virtuoso_agent/`): Provides exotic travel recommendations
- **Mortgages Assistant** (`/examples/multi_agent_collaboration/mortgage_assistant/`): Handles mortgage-related queries
- **Custom Orchestration** (`/examples/agents/custom_orchestration_agent/`): Demonstrates ReWoo (Reasoning without Observation) orchestration for a restaurant assistant agent

## Prerequisites

1. Follow the setup instructions in each agent's respective folder before using them in the demo UI:

   - `/examples/multi_agent_collaboration/mortgage_assistant/README.md`
   - `/examples/multi_agent_collaboration/voyage_virtuoso_agent/README.md`
   - `/examples/multi_agent_collaboration/trip_planner_agent/README.md`
   - `/examples/multi_agent_collaboration/team_poems_agent/README.md`
   - `/examples/agents/custom_orchestration_agent/README.md`
   - `/examples/multi_agent_collaboration/portfolio_assistant_agent/README.md`

2. Ensure you have:

   - Python 3.x
   - AWS credentials configured with appropriate permissions

3. Create and activate a Python virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install required dependencies:
   ```bash
   pip install -r src/requirements.txt
   ```

## Running the Demo

3. Configure your AWS credentials with appropriate permissions

4. Run the Streamlit application:

   ```bash
   cd examples/agents_ux/streamlit_demo/; streamlit run demo_ui.py
   ```

5. Optionally, specify a specific bot using the BOT_NAME environment variable:

   ```bash
   BOT_NAME="<bot-name>" streamlit run demo_ui.py
   ```

   Supported BOT_NAME values:

   - "PortfolioCreator Agent" (default)
   - "Portfolio Assistant"
   - "Sports Team Poet"
   - "Trip Planner"
   - "Voyage Virtuoso"
   - "Mortgages Assistant"
   - "Custom Orchestration"

## Using UV

```shell
# 1. Create a UV virtual environment (defaults to .venv)
uv venv

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Install dependencies
uv pip install -r src/requirements.txt

# 4. Start Streamlit
BOT_NAME="<bot-name>" streamlit run demo_ui.py
```

## Bot Configuration Details

After executing this code: `bot_config = next((config for config in bot_configs if config['bot_name'] == bot_name), None)`, the `bot_config` will contain the first configuration item that matches the `bot_name` variable value.

According to the code where `bot_name = os.environ.get('BOT_NAME', 'Agent Assistant')`, if the BOT_NAME environment variable is not set, it will default to 'Agent Assistant'.

Example:

If the BOT_NAME environment variable is not set, then `bot_name` will be 'Agent Assistant'. According to the definition in `config.py`, `bot_config` will be:

```json
{
    "bot_name": "Agent Assistant",
    "agent_name": "booking-agent",
    "region": "us-east-1",          # Default region
    "start_prompt": "Hi, I am Henry. How can I help you?",
    "agent_id": "VEM8PN7UL6",       # This is obtained via get_agent_id_by_name or read from configuration
    "agent_alias_id": "6TRSXGBJKM"  # This is obtained via get_agent_latest_alias_id or read from configuration
}
```

If the BOT_NAME environment variable is set to "Mortgages Assistant", then `bot_config` will be:

```json
{
    "bot_name": "Mortgages Assistant",
    "agent_name": "mortgages_assistant",
    "region": "us-east-1",          # Default region
    "start_prompt": "I'm your mortgages assistant. How can I help today?",
    "session_attributes": {
        "sessionAttributes": {
            "customer_id": "123456",
            "todays_date": "2025-04-09"
        },
        "promptSessionAttributes": {
            "customer_id": "123456",
            "customer_preferred_name": "Mark",
            "todays_date": "2025-04-09"
        }
    },
    "agent_id": "T4OHRV29ZV",
    "agent_alias_id": "GPF1XLJB8F"
}
```

If the BOT_NAME environment variable is set to a name that doesn't exist in `bot_configs`, such as "Nonexistent Bot", then `bot_config` will be None.

## Error Handling Improvements

This application includes the following error handling improvements to make it more robust:

1. **Multi-region support**: The application can now handle agents located in different AWS regions by specifying the `region` field in the configuration.

2. **Safe token handling**: Improved handling of `inputTokens` and `outputTokens`, ensuring the application works correctly even if these values don't exist or are zero.

3. **Function name handling**: Added handling for missing `function` keys in action group calls, using the default value "Unknown function" and continuing execution.

4. **Exception catching**: Added more try-except blocks to catch and log possible exceptions rather than letting the application crash.

5. **Path optimization**: Simplified import paths, removing unnecessary `sys.path` modifications.

These improvements allow the application to better handle agents in different regions and differences in agent response structures, improving overall stability.

## Quick Start Guide

Follow these steps to quickly set up and run the Bedrock Agent Streamlit UI:

1. **Create a virtual environment using UV**:

   ```bash
   uv venv
   source .venv/bin/activate
   ```

2. **Install dependencies**:

   ```bash
   uv pip install -r src/requirements.txt
   ```

3. **Configure your agent**:

   - Open `config.py` and add your agent configuration to the `bot_configs` list
   - Example configuration:

   ```python
   {
       "bot_name": "Your Agent Name",
       "agent_name": "your_agent_id",
       "region": "us-east-1",
       "start_prompt": "How can I help you today?"
   }
   ```

4. **Set default agent (Optional)**:

   - Open `demo_ui.py` and locate line 97:

   ```python
   bot_name = os.environ.get('BOT_NAME', "Agent Assistant")
   ```

   - Change `"Agent Assistant"` to your preferred default agent name

5. **Run the Streamlit application**:
   ```bash
   streamlit run demo_ui.py
   ```

## Usage

1. The UI will display the selected bot's interface (defaults to the agent specified in line 97 of demo_ui.py)
2. Enter your query in the chat input field
3. The agent will:
   - Process your request
   - Show the collaboration between different agents
   - Display thought processes and tool usage
   - Provide a detailed response

## Architecture

The demo UI integrates with Amazon Bedrock Agent Runtime for agent execution and showcases multi_agent_collaboration features including:

- Dynamic routing between specialized agents
- Knowledge base lookups
- Tool invocations
- Code interpretation capabilities

Below is an example of the demo UI in action, showing the Mortgages Assistant interface:

![Demo UI Screenshot](demo_ui.png)
