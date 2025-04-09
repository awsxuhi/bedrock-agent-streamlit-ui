import streamlit as st
import os
import uuid
import yaml
import sys
import boto3
import datetime
from pathlib import Path

# 不需要添加父目录到 sys.path，因为 demo_ui.py 和 src 目录在同一个目录下
# sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.bedrock_agent import agents_helper
from config import bot_configs
from ui_utils import invoke_agent

def initialize_session():
    """Initialize session state and bot configuration."""
    if 'count' not in st.session_state:
        st.session_state['count'] = 1

        # Refresh agent IDs and aliases
        for idx, config in enumerate(bot_configs):
            try:
                # 检查是否需要使用特定区域
                if 'region' in config:
                    # 创建特定区域的 boto3 客户端
                    region_bedrock_agent = boto3.client("bedrock-agent", region_name=config['region'])
                    
                    # 检查agent_id是否已存在
                    if 'agent_id' not in config:
                        # 使用特定区域查找 agent_id
                        try:
                            response = region_bedrock_agent.list_agents(maxResults=100)
                            agents_json = response["agentSummaries"]
                            target_agent = next(
                                (agent for agent in agents_json if agent["agentName"] == config['agent_name']), None
                            )
                            if target_agent:
                                agent_id = target_agent["agentId"]
                            else:
                                raise Exception(f"Agent {config['agent_name']} not found in region {config['region']}")
                        except Exception as e:
                            print(f"Error finding agent in region {config['region']}: {e}")
                            continue
                    else:
                        agent_id = config['agent_id']
                    
                    # 检查agent_alias_id是否已存在
                    if 'agent_alias_id' not in config:
                        try:
                            agent_aliases = region_bedrock_agent.list_agent_aliases(
                                agentId=agent_id, maxResults=100
                            )
                            
                            latest_alias_id = ""
                            latest_update = datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
                            
                            for summary in agent_aliases["agentAliasSummaries"]:
                                curr_update = summary["updatedAt"]
                                if curr_update > latest_update:
                                    latest_alias_id = summary["agentAliasId"]
                                    latest_update = curr_update
                            
                            if latest_alias_id:
                                agent_alias_id = latest_alias_id
                            else:
                                raise Exception(f"No alias found for agent {config['agent_name']} in region {config['region']}")
                        except Exception as e:
                            print(f"Error finding agent alias in region {config['region']}: {e}")
                            continue
                    else:
                        agent_alias_id = config['agent_alias_id']
                else:
                    # 使用默认区域
                    # 检查agent_id是否已存在
                    if 'agent_id' not in config:
                        agent_id = agents_helper.get_agent_id_by_name(config['agent_name'])
                    else:
                        agent_id = config['agent_id']
                    
                    # 检查agent_alias_id是否已存在
                    if 'agent_alias_id' not in config:
                        agent_alias_id = agents_helper.get_agent_latest_alias_id(agent_id)
                    else:
                        agent_alias_id = config['agent_alias_id']
                
                bot_configs[idx]['agent_id'] = agent_id
                bot_configs[idx]['agent_alias_id'] = agent_alias_id
                print(f"Agent ID: {agent_id}, Agent Alias ID: {agent_alias_id}")
                
            except Exception as e:
                print(f"Could not find agent named:{config['agent_name']}, skipping...")
                continue

        # Get bot configuration
        bot_name = os.environ.get('BOT_NAME', "Agent Assistant")  # Change this default name to your testing agent name
        # 使用生成器表达式，从列表中查找第一个 bot_name 匹配的配置项。next(..., None) 表示：如果找到了就返回该配置；如果没有找到就返回 None。
        bot_config = next((config for config in bot_configs if config['bot_name'] == bot_name), None)
        
        if bot_config:
            st.session_state['bot_config'] = bot_config
            
            # Load tasks if any
            task_yaml_content = {}
            if 'tasks' in bot_config:
                with open(bot_config['tasks'], 'r') as file:
                    task_yaml_content = yaml.safe_load(file)
            st.session_state['task_yaml_content'] = task_yaml_content

            # Initialize session ID and message history
            st.session_state['session_id'] = str(uuid.uuid4())
            st.session_state.messages = []

def main():
    """Main application flow."""
    initialize_session()

    # Display chat interface
    st.title(st.session_state['bot_config']['bot_name'])

    # Show message history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if 'user_input' not in st.session_state:
        next_prompt = st.session_state['bot_config']['start_prompt']
        user_query = st.chat_input(placeholder=next_prompt, key="user_input")
        st.session_state['bot_config']['start_prompt'] = " "
    elif st.session_state.count > 1:
        user_query = st.session_state['user_input']
        
        if user_query:
            # Display user message
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            # Get and display assistant response
            response = ""
            with st.chat_message("assistant"):
                try:
                    session_id = st.session_state['session_id']
                    response = st.write_stream(invoke_agent(
                        user_query, 
                        session_id, 
                        st.session_state['task_yaml_content']
                    ))
                except Exception as e:
                    print(f"Error: {e}")  # Keep logging for debugging
                    st.error(f"An error occurred: {str(e)}")  # Show error in UI
                    response = "I encountered an error processing your request. Please try again."

            # Update chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

        # Reset input
        user_query = st.chat_input(placeholder=" ", key="user_input")

    # Update session count
    st.session_state['count'] = st.session_state.get('count', 1) + 1

if __name__ == "__main__":
    main()
