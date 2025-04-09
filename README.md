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

The following demos have been tested with this UI and can be found in their respective folders:

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
# 1. 创建 uv 虚拟环境（默认自动使用 .venv）
uv venv

# 2. 激活虚拟环境（这一步与原来一致）
source .venv/bin/activate

# 3. 安装依赖（可直接使用 requirements.txt）
uv pip install -r src/requirements.txt

# 4. 启动 Streamlit
BOT_NAME="<bot-name>" streamlit run demo_ui.py
```

## Bot Configuration Details

这行代码 bot_config = next((config for config in bot_configs if config['bot_name'] == bot_name), None) 执行后，bot_config 将包含与 bot_name 变量值匹配的第一个配置项。

根据代码中的 bot_name = os.environ.get('BOT_NAME', 'PortfolioCreator Agent')，如果环境变量 BOT_NAME 未设置，则默认使用 'PortfolioCreator Agent'。

举例说明：

假设环境变量 BOT_NAME 未设置，则 bot_name 为 'PortfolioCreator Agent'。根据 config.py 中的定义，bot_config 将是：

```json
{
    "bot_name": "PortfolioCreator Agent",
    "agent_name": "portfolio_creator",
    "region": "us-west-2",          # 注意这个 agent 位于 us-west-2 区域
    "start_prompt": "I can help create portfolios. What would you like to know?",
    "agent_id": "VEM8PN7UL6",       # 这是通过 get_agent_id_by_name 获取或从配置中读取的
    "agent_alias_id": "6TRSXGBJKM"  # 这是通过 get_agent_latest_alias_id 获取或从配置中读取的
}
```

如果环境变量 BOT_NAME 设置为 "Mortgages Assistant"，则 bot_config 将是：

```json
{
    "bot_name": "Mortgages Assistant",
    "agent_name": "mortgages_assistant",
    "region": "us-east-1",          # 默认区域
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

如果环境变量 BOT_NAME 设置为一个不存在于 bot_configs 中的名称，例如 "Nonexistent Bot"，则 bot_config 将是 None。

## Error Handling Improvements

本应用程序包含以下错误处理改进，使其更加健壮：

1. **多区域支持**：应用程序现在可以处理位于不同 AWS 区域的 agent，通过在配置中指定 `region` 字段。

2. **安全的令牌处理**：改进了对 `inputTokens` 和 `outputTokens` 的处理，即使这些值不存在或为零，应用程序也能正常工作。

3. **函数名称处理**：添加了对 action group 调用中缺失 `function` 键的处理，使用默认值 "未知函数" 并继续执行。

4. **异常捕获**：添加了更多的 try-except 块，以捕获并记录可能的异常，而不是让应用程序崩溃。

5. **路径优化**：简化了导入路径，移除了不必要的 `sys.path` 修改。

这些改进使应用程序能够更好地处理不同区域的 agent，以及不同 agent 响应结构的差异，提高了整体稳定性。

## Usage

1. The UI will display the selected bot's interface (defaults to PortfolioCreator Agent if not specified)
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
