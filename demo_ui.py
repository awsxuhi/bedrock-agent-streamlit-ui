import streamlit as st
import os
import uuid
import yaml
import sys
import boto3
import datetime
from pathlib import Path
import json
import importlib

# 不需要添加父目录到 sys.path，因为 demo_ui.py 和 src 目录在同一个目录下
# sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.bedrock_agent import agents_helper
import config
from ui_utils import invoke_agent, get_error_text

def get_agent_id_by_name(agent_name, region=None):
    """根据agent名称获取agent ID"""
    try:
        if region:
            bedrock_agent = boto3.client("bedrock-agent", region_name=region)
        else:
            bedrock_agent = boto3.client("bedrock-agent")
            
        response = bedrock_agent.list_agents(maxResults=100)
        agents_json = response["agentSummaries"]
        target_agent = next(
            (agent for agent in agents_json if agent["agentName"] == agent_name), None
        )
        if target_agent:
            return target_agent["agentId"]
        else:
            return None
    except Exception as e:
        print(f"Error finding agent: {e}")
        return None

def get_agent_name_by_id(agent_id, region=None):
    """根据agent ID获取agent名称"""
    try:
        if region:
            bedrock_agent = boto3.client("bedrock-agent", region_name=region)
        else:
            bedrock_agent = boto3.client("bedrock-agent")
            
        response = bedrock_agent.get_agent(agentId=agent_id)
        return response["agent"]["agentName"]
    except Exception as e:
        print(f"Error finding agent name: {e}")
        return None

def get_agent_alias_id(agent_id, region=None):
    """根据agent ID获取最新的alias ID"""
    try:
        if region:
            bedrock_agent = boto3.client("bedrock-agent", region_name=region)
        else:
            bedrock_agent = boto3.client("bedrock-agent")
            
        agent_aliases = bedrock_agent.list_agent_aliases(
            agentId=agent_id, maxResults=100
        )
        
        latest_alias_id = ""
        latest_update = datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        
        for summary in agent_aliases["agentAliasSummaries"]:
            curr_update = summary["updatedAt"]
            if curr_update > latest_update:
                latest_alias_id = summary["agentAliasId"]
                latest_update = curr_update
        
        return latest_alias_id if latest_alias_id else None
    except Exception as e:
        print(f"Error finding agent alias: {e}")
        return None

def save_bot_configs(bot_configs):
    """将bot_configs保存到config.py文件"""
    try:
        with open('config.py', 'r') as file:
            content = file.read()
        
        # 找到bot_configs的定义开始位置
        start_idx = content.find('bot_configs = [')
        if start_idx == -1:
            return False, "无法在config.py中找到bot_configs定义"
        
        # 找到bot_configs定义的结束位置
        end_idx = content.find(']', start_idx)
        if end_idx == -1:
            return False, "无法在config.py中找到bot_configs定义的结束位置"
        end_idx += 1  # 包含结束的']'
        
        # 生成新的bot_configs定义
        new_configs = "bot_configs = [\n"
        for config in bot_configs:
            new_configs += "    {\n"
            for key, value in config.items():
                if key == "session_attributes":
                    new_configs += f"        \"{key}\": {value},\n"
                elif isinstance(value, str):
                    new_configs += f"        \"{key}\": \"{value}\",\n"
                else:
                    new_configs += f"        \"{key}\": {value},\n"
            new_configs = new_configs.rstrip(",\n") + "\n    },\n"
        new_configs = new_configs.rstrip(",\n") + "\n]"
        
        # 替换原有的bot_configs定义
        new_content = content[:start_idx] + new_configs + content[end_idx:]
        
        with open('config.py', 'w') as file:
            file.write(new_content)
        
        return True, "成功保存配置"
    except Exception as e:
        print(f"Error saving bot_configs: {e}")
        return False, f"保存配置时出错: {str(e)}"

def add_bot_config(new_config):
    """添加新的bot配置到config.py"""
    try:
        # 重新加载config模块以获取最新的bot_configs
        importlib.reload(config)
        bot_configs = config.bot_configs
        
        # 检查bot_name是否已存在
        if any(cfg['bot_name'] == new_config['bot_name'] for cfg in bot_configs):
            return False, f"Bot名称 '{new_config['bot_name']}' 已存在"
        
        # 添加新配置到列表的最前面
        bot_configs.insert(0, new_config)
        
        # 保存到config.py
        success, message = save_bot_configs(bot_configs)
        if success:
            return True, f"成功添加Bot: {new_config['bot_name']}"
        else:
            return False, message
    except Exception as e:
        print(f"Error adding bot config: {e}")
        return False, f"添加Bot配置时出错: {str(e)}"

def delete_bot_config(bot_name):
    """从config.py中删除bot配置"""
    try:
        # 重新加载config模块以获取最新的bot_configs
        importlib.reload(config)
        bot_configs = config.bot_configs
        
        # 查找要删除的配置
        idx_to_delete = None
        for idx, cfg in enumerate(bot_configs):
            if cfg['bot_name'] == bot_name:
                idx_to_delete = idx
                break
        
        if idx_to_delete is None:
            return False, f"找不到Bot: {bot_name}"
        
        # 删除配置
        del bot_configs[idx_to_delete]
        
        # 保存到config.py
        success, message = save_bot_configs(bot_configs)
        if success:
            return True, f"成功删除Bot: {bot_name}"
        else:
            return False, message
    except Exception as e:
        print(f"Error deleting bot config: {e}")
        return False, f"删除Bot配置时出错: {str(e)}"

def initialize_session():
    """Initialize session state and bot configuration."""
    # 初始化语言设置
    if 'language' not in st.session_state:
        st.session_state['language'] = "English"  # 默认使用英文界面
    
    # 初始化新bot表单状态
    if 'new_bot_name' not in st.session_state:
        st.session_state['new_bot_name'] = ""
    
    if 'new_agent_name' not in st.session_state:
        st.session_state['new_agent_name'] = ""
    
    if 'new_agent_alias_id' not in st.session_state:
        st.session_state['new_agent_alias_id'] = ""
    
    if 'new_start_prompt' not in st.session_state:
        st.session_state['new_start_prompt'] = "Hi, I am Henry. How can I help you?"
    
    if 'new_region' not in st.session_state:
        st.session_state['new_region'] = "us-east-1"
    
    # 初始化配置是否已应用
    if 'config_applied' not in st.session_state:
        st.session_state['config_applied'] = False
    
    if 'count' not in st.session_state:
        st.session_state['count'] = 1

        # 重新加载config模块以获取最新的bot_configs
        importlib.reload(config)
        bot_configs = config.bot_configs
        
        # Refresh agent IDs and aliases
        for idx, bot_config in enumerate(bot_configs):
            try:
                # 检查是否需要使用特定区域
                if 'region' in bot_config:
                    # 创建特定区域的 boto3 客户端
                    region_bedrock_agent = boto3.client("bedrock-agent", region_name=bot_config['region'])
                    
                    # 检查agent_id是否已存在
                    if 'agent_id' not in bot_config:
                        # 使用特定区域查找 agent_id
                        try:
                            response = region_bedrock_agent.list_agents(maxResults=100)
                            agents_json = response["agentSummaries"]
                            target_agent = next(
                                (agent for agent in agents_json if agent["agentName"] == bot_config['agent_name']), None
                            )
                            if target_agent:
                                agent_id = target_agent["agentId"]
                            else:
                                raise Exception(f"Agent {bot_config['agent_name']} not found in region {bot_config['region']}")
                        except Exception as e:
                            print(f"Error finding agent in region {bot_config['region']}: {e}")
                            continue
                    else:
                        agent_id = bot_config['agent_id']
                    
                    # 检查agent_alias_id是否已存在
                    if 'agent_alias_id' not in bot_config:
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
                                raise Exception(f"No alias found for agent {bot_config['agent_name']} in region {bot_config['region']}")
                        except Exception as e:
                            print(f"Error finding agent alias in region {bot_config['region']}: {e}")
                            continue
                    else:
                        agent_alias_id = bot_config['agent_alias_id']
                else:
                    # 使用默认区域
                    # 检查agent_id是否已存在
                    if 'agent_id' not in bot_config:
                        agent_id = agents_helper.get_agent_id_by_name(bot_config['agent_name'])
                    else:
                        agent_id = bot_config['agent_id']
                    
                    # 检查agent_alias_id是否已存在
                    if 'agent_alias_id' not in bot_config:
                        agent_alias_id = agents_helper.get_agent_latest_alias_id(agent_id)
                    else:
                        agent_alias_id = bot_config['agent_alias_id']
                
                bot_configs[idx]['agent_id'] = agent_id
                bot_configs[idx]['agent_alias_id'] = agent_alias_id
                print(f"Agent ID: {agent_id}, Agent Alias ID: {agent_alias_id}")
                
            except Exception as e:
                print(f"Could not find agent named:{bot_config.get('agent_name', 'unknown')}, skipping...")
                continue

        # Get bot configuration
        bot_name = os.environ.get('BOT_NAME', "Multi-agent PortfolioCreator")  # Change this default name to your testing agent name
        # 使用生成器表达式，从列表中查找第一个 bot_name 匹配的配置项。next(..., None) 表示：如果找到了就返回该配置；如果没有找到就返回 None。
        bot_config = next((cfg for cfg in bot_configs if cfg['bot_name'] == bot_name), None)
        
        # 如果找不到默认的bot配置，尝试使用第一个有效的bot配置
        if not bot_config and bot_configs:
            # 查找第一个同时具有agent_id和agent_alias_id的配置
            for cfg in bot_configs:
                if 'agent_id' in cfg and 'agent_alias_id' in cfg:
                    bot_config = cfg
                    print(f"Using alternative bot configuration: {cfg['bot_name']}")
                    break
            
            # 如果没有找到同时具有agent_id和agent_alias_id的配置，使用第一个配置
            if not bot_config and bot_configs:
                bot_config = bot_configs[0]
                print(f"Using first available bot configuration: {bot_config['bot_name']}")
        
        if bot_config:
            st.session_state['bot_config'] = bot_config
            st.session_state['config_applied'] = True
            
            # Load tasks if any
            task_yaml_content = {}
            if 'tasks' in bot_config:
                with open(bot_config['tasks'], 'r') as file:
                    task_yaml_content = yaml.safe_load(file)
            st.session_state['task_yaml_content'] = task_yaml_content

            # Initialize session ID and message history
            st.session_state['session_id'] = str(uuid.uuid4())
            st.session_state.messages = []

def get_agent_info_by_alias_id(alias_id, region=None):
    """根据agent alias ID获取agent ID和agent name"""
    try:
        if region:
            bedrock_agent = boto3.client("bedrock-agent", region_name=region)
        else:
            bedrock_agent = boto3.client("bedrock-agent")
        
        # 首先获取agent ID
        response = bedrock_agent.list_agent_aliases(maxResults=100)
        agent_id = None
        
        for alias in response.get("agentAliasSummaries", []):
            if alias["agentAliasId"] == alias_id:
                agent_id = alias["agentId"]
                break
        
        if not agent_id:
            return None, None
        
        # 然后获取agent name
        agent_response = bedrock_agent.get_agent(agentId=agent_id)
        agent_name = agent_response["agent"]["agentName"]
        
        return agent_id, agent_name
    except Exception as e:
        print(f"Error finding agent by alias ID: {e}")
        return None, None

def update_custom_config():
    """根据用户输入更新自定义配置"""
    if st.session_state['use_custom_config']:
        custom_config = {
            'bot_name': 'Bedrock Agent',  # 默认名称
            'region': st.session_state['custom_region']
        }
        
        # 配置优先级：alias_id > agent_id > agent_name
        # 如果提供了agent_alias_id，优先使用它来查找agent_id和agent_name
        if st.session_state['custom_agent_alias_id']:
            custom_config['agent_alias_id'] = st.session_state['custom_agent_alias_id']
            agent_id, agent_name = get_agent_info_by_alias_id(
                st.session_state['custom_agent_alias_id'], 
                st.session_state['custom_region']
            )
            
            if agent_id:
                custom_config['agent_id'] = agent_id
                st.session_state['custom_agent_id'] = agent_id
                
            if agent_name:
                custom_config['agent_name'] = agent_name
                st.session_state['custom_agent_name'] = agent_name
        else:
            # 如果提供了agent_id，使用它并尝试查找agent_name
            if st.session_state['custom_agent_id']:
                custom_config['agent_id'] = st.session_state['custom_agent_id']
                agent_name = get_agent_name_by_id(st.session_state['custom_agent_id'], st.session_state['custom_region'])
                if agent_name:
                    custom_config['agent_name'] = agent_name
                    st.session_state['custom_agent_name'] = agent_name
            # 如果只提供了agent_name，尝试查找agent_id
            elif st.session_state['custom_agent_name']:
                custom_config['agent_name'] = st.session_state['custom_agent_name']
                agent_id = get_agent_id_by_name(st.session_state['custom_agent_name'], st.session_state['custom_region'])
                if agent_id:
                    custom_config['agent_id'] = agent_id
                    st.session_state['custom_agent_id'] = agent_id
            
            # 如果没有提供alias_id但有agent_id，尝试查找最新的alias_id
            if 'agent_id' in custom_config:
                alias_id = get_agent_alias_id(custom_config['agent_id'], st.session_state['custom_region'])
                if alias_id:
                    custom_config['agent_alias_id'] = alias_id
                    st.session_state['custom_agent_alias_id'] = alias_id
        
        # 更新会话状态中的bot_config
        st.session_state['bot_config'] = custom_config
        st.session_state['config_applied'] = True
        
        # 重置会话ID和消息历史
        st.session_state['session_id'] = str(uuid.uuid4())
        st.session_state.messages = []
        
        # 设置空的task_yaml_content
        st.session_state['task_yaml_content'] = {}

def get_ui_text(key):
    """根据当前语言获取UI文本"""
    texts = {
        "中文": {
            "title": "Agent 配置",
            "language_select": "界面语言",
            "manage_bots": "管理 Bots",
            "select_bot": "选择 Bot",
            "add_bot": "添加新 Bot",
            "delete_bot": "删除 Bot",
            "bot_name": "Bot 名称",
            "agent_name": "Agent 名称",
            "agent_id": "Agent ID",
            "agent_alias_id": "Agent Alias ID (可选)",
            "start_prompt": "初始提示语 (可选)",
            "region": "区域",
            "apply": "应用",
            "add": "添加",
            "delete": "删除",
            "config_updated": "配置已更新！",
            "bot_added": "Bot 已添加！",
            "bot_deleted": "Bot 已删除！",
            "bot_exists": "Bot 名称已存在！",
            "missing_fields": "Bot 名称和 Agent 名称为必填项！",
            "chinese": "中文",
            "english": "English",
            "new_session": "🔄 新建会话",
            "new_session_help": "清空聊天历史，重新开始对话"
        },
        "English": {
            "title": "Agent Configuration",
            "language_select": "Interface Language",
            "manage_bots": "Manage Bots",
            "select_bot": "Select Bot",
            "add_bot": "Add New Bot",
            "delete_bot": "Delete Bot",
            "bot_name": "Bot Name",
            "agent_name": "Agent Name",
            "agent_id": "Agent ID",
            "agent_alias_id": "Agent Alias ID (optional)",
            "start_prompt": "Start Prompt (optional)",
            "region": "Region",
            "apply": "Apply",
            "add": "Add",
            "delete": "Delete",
            "config_updated": "Configuration Updated!",
            "bot_added": "Bot Added!",
            "bot_deleted": "Bot Deleted!",
            "bot_exists": "Bot name already exists!",
            "missing_fields": "Bot name and Agent name are required!",
            "chinese": "中文",
            "english": "English",
            "new_session": "🔄 New Session",
            "new_session_help": "Clear chat history and start a new conversation"
        }
    }
    
    return texts[st.session_state['language']][key]

def on_language_change():
    """语言切换回调函数"""
    if st.session_state['language_toggle'] == get_ui_text("chinese"):
        st.session_state['language'] = "中文"
    else:
        st.session_state['language'] = "English"

def on_custom_config_change():
    """自定义配置切换回调函数"""
    st.session_state['use_custom_config'] = st.session_state['use_custom_config_checkbox']

def on_agent_id_change():
    """Agent ID输入变化回调函数"""
    agent_id = st.session_state['custom_agent_id_input']
    st.session_state['custom_agent_id'] = agent_id

def on_new_bot_name_change():
    """新Bot名称输入变化回调函数"""
    st.session_state['new_bot_name'] = st.session_state['new_bot_name_input']

def on_new_agent_name_change():
    """新Agent名称输入变化回调函数"""
    st.session_state['new_agent_name'] = st.session_state['new_agent_name_input']

def on_new_start_prompt_change():
    """新初始提示语输入变化回调函数"""
    st.session_state['new_start_prompt'] = st.session_state['new_start_prompt_input']

def on_new_region_change():
    """新区域选择变化回调函数"""
    st.session_state['new_region'] = st.session_state['new_region_select']

def main():
    """Main application flow."""
    initialize_session()
    
    # 重新加载config模块以获取最新的bot_configs
    importlib.reload(config)
    bot_configs = config.bot_configs
    
    # 侧边栏配置区域
    with st.sidebar:
        st.title(get_ui_text("title"))
        
        # 选择Bot
        st.subheader(get_ui_text("select_bot"))
        bot_names = [cfg['bot_name'] for cfg in bot_configs]
        selected_bot = st.selectbox(
            label=get_ui_text("select_bot"),
            options=bot_names,
            key="selected_bot",
            label_visibility="collapsed"
        )
        
        # 显示所选Bot的详细信息
        selected_config = next((cfg for cfg in bot_configs if cfg['bot_name'] == selected_bot), None)
        if selected_config:
            st.write(f"**{get_ui_text('agent_name')}:** {selected_config.get('agent_name', 'N/A')}")
            st.write(f"**{get_ui_text('region')}:** {selected_config.get('region', 'us-east-1')}")
            
            # 应用按钮
            if st.button(get_ui_text("apply")):
                # 确保配置中包含agent_id和agent_alias_id
                if 'agent_id' not in selected_config or 'agent_alias_id' not in selected_config:
                    # 尝试获取agent_id和agent_alias_id
                    try:
                        region = selected_config.get('region', 'us-east-1')
                        bedrock_agent = boto3.client("bedrock-agent", region_name=region)
                        
                        # 如果有agent_alias_id但没有agent_id，尝试获取agent_id
                        if 'agent_alias_id' in selected_config and 'agent_id' not in selected_config:
                            agent_id, _ = get_agent_info_by_alias_id(selected_config['agent_alias_id'], region)
                            if agent_id:
                                selected_config['agent_id'] = agent_id
                                print(f"Found agent_id: {agent_id} for alias_id: {selected_config['agent_alias_id']}")
                        
                        # 如果有agent_id但没有agent_alias_id，尝试获取agent_alias_id
                        elif 'agent_id' in selected_config and 'agent_alias_id' not in selected_config:
                            agent_alias_id = get_agent_alias_id(selected_config['agent_id'], region)
                            if agent_alias_id:
                                selected_config['agent_alias_id'] = agent_alias_id
                                print(f"Found agent_alias_id: {agent_alias_id} for agent_id: {selected_config['agent_id']}")
                        
                        # 如果只有agent_name，尝试获取agent_id和agent_alias_id
                        elif 'agent_name' in selected_config:
                            agent_id = get_agent_id_by_name(selected_config['agent_name'], region)
                            if agent_id:
                                selected_config['agent_id'] = agent_id
                                print(f"Found agent_id: {agent_id} for agent_name: {selected_config['agent_name']}")
                                
                                agent_alias_id = get_agent_alias_id(agent_id, region)
                                if agent_alias_id:
                                    selected_config['agent_alias_id'] = agent_alias_id
                                    print(f"Found agent_alias_id: {agent_alias_id} for agent_id: {agent_id}")
                    except Exception as e:
                        print(f"Error getting agent information: {e}")
                
                # 检查是否成功获取了agent_id和agent_alias_id
                if 'agent_id' in selected_config and 'agent_alias_id' in selected_config:
                    st.session_state['bot_config'] = selected_config
                    st.session_state['config_applied'] = True
                    
                    # 重置会话ID和消息历史
                    st.session_state['session_id'] = str(uuid.uuid4())
                    st.session_state.messages = []
                    
                    # 加载任务（如果有）
                    task_yaml_content = {}
                    if 'tasks' in selected_config:
                        with open(selected_config['tasks'], 'r') as file:
                            task_yaml_content = yaml.safe_load(file)
                    st.session_state['task_yaml_content'] = task_yaml_content
                    
                    st.success(get_ui_text("config_updated"))
                else:
                    st.error(get_error_text("agent_mismatch"))
        
        # 添加分隔线
        st.write("---")
        
        # 添加新Bot
        with st.expander(get_ui_text("add_bot")):
            # Bot名称
            st.text_input(
                get_ui_text("bot_name"),
                value=st.session_state['new_bot_name'],
                key="new_bot_name_input",
                on_change=on_new_bot_name_change
            )
            
            # Agent名称
            st.text_input(
                get_ui_text("agent_name"),
                value=st.session_state['new_agent_name'],
                key="new_agent_name_input",
                on_change=on_new_agent_name_change
            )
            
            # 初始提示语（可选）
            st.text_area(
                get_ui_text("start_prompt"),
                value=st.session_state['new_start_prompt'],
                key="new_start_prompt_input",
                on_change=on_new_start_prompt_change
            )
            
            # 区域选择
            st.selectbox(
                get_ui_text("region"),
                ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "eu-west-1", "ap-northeast-1"],
                index=0,
                key="new_region_select",
                on_change=on_new_region_change
            )
            
            # 检查是否输入了必填字段
            has_required = bool(st.session_state['new_bot_name'] and st.session_state['new_agent_name'])
            
            # 添加按钮
            if st.button(get_ui_text("add"), disabled=not has_required):
                if not has_required:
                    st.error(get_ui_text("missing_fields"))
                else:
                    # 创建新的bot配置
                    new_config = {
                        'bot_name': st.session_state['new_bot_name'],
                        'agent_name': st.session_state['new_agent_name'],
                        'region': st.session_state['new_region']
                    }
                    
                    if st.session_state['new_start_prompt']:
                        new_config['start_prompt'] = st.session_state['new_start_prompt']
                    
                    # 添加到config.py
                    success, message = add_bot_config(new_config)
                    if success:
                        # 显示成功消息，并提醒用户点击Apply按钮
                        success_message = f"{get_ui_text('bot_added')} {get_ui_text('select_bot')} '{new_config['bot_name']}' {get_ui_text('apply')}"
                        st.success(success_message)
                        # 清空表单
                        st.session_state['new_bot_name'] = ""
                        st.session_state['new_agent_name'] = ""
                        st.session_state['new_start_prompt'] = "Hi, I am Henry. How can I help you?"
                        st.session_state['new_region'] = "us-east-1"
                        # 重新加载页面以更新bot列表
                        st.rerun()
                    else:
                        st.error(message)
        
        # 删除Bot
        with st.expander(get_ui_text("delete_bot")):
            bot_to_delete = st.selectbox(
                label=get_ui_text("delete_bot"),
                options=bot_names,
                key="bot_to_delete"
            )
            
            # 删除按钮
            if st.button(get_ui_text("delete"), key="delete_button"):
                success, message = delete_bot_config(bot_to_delete)
                if success:
                    st.success(get_ui_text("bot_deleted"))
                    # 重新加载页面以更新bot列表
                    st.rerun()
                else:
                    st.error(message)
        
        # 在侧边栏底部添加语言切换开关
        st.write("")
        st.write("")
        st.write("")
        st.write("---")  # 添加分隔线
        col1, col2 = st.columns([1, 3])
        with col1:
            st.toggle(
                label="Language Toggle",
                value=st.session_state['language'] == "中文",
                key="language_toggle",
                on_change=on_language_change,
                label_visibility="collapsed"
            )
        with col2:
            st.caption(f"{get_ui_text('chinese')} / {get_ui_text('english')}")

    # 主界面显示聊天界面
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(st.session_state['bot_config'].get('bot_name', 'Bedrock Agent Chat'))
    with col2:
        # 添加新建会话按钮
        if st.button(get_ui_text("new_session"), help=get_ui_text("new_session_help")):
            # 重置会话ID和消息历史
            st.session_state['session_id'] = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()

    # Show message history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if 'user_input' not in st.session_state:
        next_prompt = st.session_state['bot_config'].get('start_prompt', '')
        user_query = st.chat_input(placeholder=next_prompt, key="user_input", disabled=not st.session_state['config_applied'])
        if 'start_prompt' in st.session_state['bot_config']:
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
        user_query = st.chat_input(placeholder=" ", key="user_input", disabled=not st.session_state['config_applied'])

    # Update session count
    st.session_state['count'] = st.session_state.get('count', 1) + 1
    
    # 语言切换开关已移到sidebar底部

if __name__ == "__main__":
    main()
