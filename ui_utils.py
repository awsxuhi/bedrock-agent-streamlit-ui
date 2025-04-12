import boto3
import streamlit as st
import datetime
import json
import math
from src.utils.bedrock_agent import Task

def make_full_prompt(tasks, additional_instructions, processing_type="sequential"):
    """Build a full prompt from tasks and instructions."""
    prompt = ''
    if processing_type == 'sequential':
        prompt += """
Please perform the following tasks sequentially. Be sure you do not 
perform any of the tasks in parallel. If a task will require information produced from a prior task, 
be sure to include the full text details as comprehensive input to the task.\n\n"""
    elif processing_type == "allow_parallel":
        prompt += """
Please perform as many of the following tasks in parallel where possible.
When a dependency between tasks is clear, execute those tasks in sequential order. 
If a task will require information produced from a prior task,
be sure to include the comprehensive text details as input to the task.\n\n"""

    for task_num, task in enumerate(tasks, 1):
        prompt += f"Task {task_num}. {task}\n"

    prompt += "\nBefore returning the final answer, review whether you have achieved the expected output for each task."

    if additional_instructions:
        prompt += f"\n{additional_instructions}"

    return prompt

def get_trace_text(key):
    """根据当前语言获取跟踪文本"""
    texts = {
        "中文": {
            "choosing_collaborator": "正在为此请求选择协作者...",
            "no_matching": "没有匹配的协作者。对此请求恢复为'SUPERVISOR'模式。",
            "continue_conversation": "继续与之前的协作者对话",
            "use_collaborator": "使用协作者: '{}'",
            "intent_classifier": "意图分类器耗时 {:.1f}秒",
            "using_kb": "使用知识库",
            "kb_id": "知识库 ID: ",
            "query": "查询: ",
            "invoking_tool": "调用工具 - ",
            "unknown_function": "未知函数",
            "function": "函数: ",
            "type": "类型: ",
            "parameters": "参数",
            "param_name": "参数名称",
            "param_value": "参数值",
            "code_interpreter": "代码解释器工具使用",
            "kb_response": "知识库响应",
            "references": "引用",
            "tool_response": "工具响应",
            "code_output": "代码解释器输出",
            "code_error": "代码解释错误: ",
            "files_generated": "生成的文件:\n",
            "agent_response": "Agent 响应",
            "step": "步骤",
            "sub_agent": "子 Agent",
            "processing": "处理中...",
            "total_input_tokens": "总输入令牌数: ",
            "total_output_tokens": "总输出令牌数: ",
            "total_llm_calls": "总LLM调用次数: ",
            "collaborator_invoke": "调用协作者 - {}",
            "collaborator_name": "协作者名称: ",
            "collaborator_input": "输入内容: ",
            "collaborator_response": "协作者响应 - {}"
        },
        "English": {
            "choosing_collaborator": "Choosing a collaborator for this request...",
            "no_matching": "No matching collaborator. Revert to 'SUPERVISOR' mode for this request.",
            "continue_conversation": "Continue conversation with previous collaborator",
            "use_collaborator": "Use collaborator: '{}'",
            "intent_classifier": "Intent classifier took {:.1f}s",
            "using_kb": "Using knowledge base",
            "kb_id": "Knowledge base ID: ",
            "query": "Query: ",
            "invoking_tool": "Invoking Tool - ",
            "unknown_function": "Unknown function",
            "function": "Function: ",
            "type": "Type: ",
            "parameters": "Parameters",
            "param_name": "Parameter Name",
            "param_value": "Parameter Value",
            "code_interpreter": "Code interpreter tool usage",
            "kb_response": "Knowledge Base Response",
            "references": "references",
            "tool_response": "Tool Response",
            "code_output": "Code interpreter output",
            "code_error": "Code interpretation error: ",
            "files_generated": "Code interpretation files generated:\n",
            "agent_response": "Agent Response",
            "step": "Step",
            "sub_agent": "Sub-Agent",
            "processing": "Processing.....",
            "total_input_tokens": "Total Input Tokens: ",
            "total_output_tokens": "Total Output Tokens: ",
            "total_llm_calls": "Total LLM Calls: ",
            "collaborator_invoke": "Invoking Collaborator - {}",
            "collaborator_name": "Collaborator Name: ",
            "collaborator_input": "Input Content: ",
            "collaborator_response": "Collaborator Response - {}"
        }
    }
    
    language = st.session_state.get('language', "English")
    return texts[language][key]

def process_routing_trace(event, step, _sub_agent_name, _time_before_routing=None):
    """Process routing classifier trace events."""
   
    _route = event['trace']['trace']['routingClassifierTrace']
    
    if 'modelInvocationInput' in _route:
        #print("Processing modelInvocationInput")
        container = st.container(border=True)                            
        container.markdown(f"""**{get_trace_text("choosing_collaborator")}**""")
        return datetime.datetime.now(), step, _sub_agent_name, None, None
        
    if 'modelInvocationOutput' in _route and _time_before_routing:
        #print("Processing modelInvocationOutput")
        try:
            _llm_usage = _route['modelInvocationOutput'].get('metadata', {}).get('usage', {})
            inputTokens = _llm_usage.get('inputTokens', 0)
            outputTokens = _llm_usage.get('outputTokens', 0)
        except Exception as e:
            print(f"Error getting token usage from routing trace: {e}")
            inputTokens = 0
            outputTokens = 0
        
        _route_duration = datetime.datetime.now() - _time_before_routing

        _raw_resp_str = _route['modelInvocationOutput']['rawResponse']['content']
        _raw_resp = json.loads(_raw_resp_str)
        _classification = _raw_resp['content'][0]['text'].replace('<a>', '').replace('</a>', '')

        if _classification == "undecidable":
            text = get_trace_text("no_matching")
        elif _classification in (_sub_agent_name, 'keep_previous_agent'):
            step = math.floor(step + 1)
            text = get_trace_text("continue_conversation")
        else:
            _sub_agent_name = _classification
            step = math.floor(step + 1)
            text = get_trace_text("use_collaborator").format(_sub_agent_name)

        time_text = get_trace_text("intent_classifier").format(_route_duration.total_seconds())
        container = st.container(border=True)                            
        container.write(text)
        container.write(time_text)
        
        return step, _sub_agent_name, inputTokens, outputTokens

def process_orchestration_trace(event, agentClient, step):
    """Process orchestration trace events."""
    _orch = event['trace']['trace']['orchestrationTrace']
    inputTokens = 0
    outputTokens = 0
    collaborator_output = None
    
    if "invocationInput" in _orch:
        _input = _orch['invocationInput']
        
        if 'knowledgeBaseLookupInput' in _input:
            with st.expander(get_trace_text("using_kb"), False, icon=":material/plumbing:"):
                st.write(get_trace_text("kb_id") + _input["knowledgeBaseLookupInput"]["knowledgeBaseId"])
                st.write(get_trace_text("query") + _input["knowledgeBaseLookupInput"]["text"].replace('$', r'\$'))
        
        if 'agentCollaboratorInvocationInput' in _input:
            # 处理collaborator agent的调用
            collab_name = _input['agentCollaboratorInvocationInput']['agentCollaboratorName']
            collab_input = _input['agentCollaboratorInvocationInput']['input']['text']
            with st.expander(get_trace_text("collaborator_invoke").format(collab_name), False, icon=":material/account-group:"):
                st.write(f"{get_trace_text('collaborator_name')}{collab_name}")
                st.write(f"{get_trace_text('collaborator_input')}{collab_input[:200]}...")
                
        if "actionGroupInvocationInput" in _input:
            try:
                function = _input["actionGroupInvocationInput"].get("function", get_trace_text("unknown_function"))
                with st.expander(f"{get_trace_text('invoking_tool')}{function}", False, icon=":material/plumbing:"):
                    st.write(get_trace_text("function") + function)
                    if "executionType" in _input["actionGroupInvocationInput"]:
                        st.write(get_trace_text("type") + _input["actionGroupInvocationInput"]["executionType"])
                    if 'parameters' in _input["actionGroupInvocationInput"]:
                        st.write(f"*{get_trace_text('parameters')}*")
                        params = _input["actionGroupInvocationInput"]["parameters"]
                        st.table({
                            get_trace_text('param_name'): [p["name"] for p in params],
                            get_trace_text('param_value'): [p["value"] for p in params]
                        })
            except Exception as e:
                print(f"Error processing actionGroupInvocationInput: {e}")
                print(f"actionGroupInvocationInput content: {_input['actionGroupInvocationInput']}")

        if 'codeInterpreterInvocationInput' in _input:
            with st.expander(get_trace_text("code_interpreter"), False, icon=":material/psychology:"):
                gen_code = _input['codeInterpreterInvocationInput']['code']
                st.code(gen_code, language="python")
                    
    if "modelInvocationOutput" in _orch:
        try:
            metadata = _orch["modelInvocationOutput"].get("metadata", {})
            usage = metadata.get("usage", {})
            inputTokens = usage.get("inputTokens", 0)
            outputTokens = usage.get("outputTokens", 0)
        except Exception as e:
            print(f"Error getting token usage from orchestration trace: {e}")
            inputTokens = 0
            outputTokens = 0
                    
    if "rationale" in _orch:
        if "agentId" in event["trace"]:
            agentData = agentClient.get_agent(agentId=event["trace"]["agentId"])
            agentName = agentData["agent"]["agentName"]
            chain = event["trace"]["callerChain"]
            
            container = st.container(border=True)
            
            if len(chain) <= 1:
                step = math.floor(step + 1)
                container.markdown(f"""#### {get_trace_text("step")}  :blue[{round(step,2)}]""")
            else:
                step = step + 0.1
                container.markdown(f"""###### {get_trace_text("step")} {round(step,2)} {get_trace_text("sub_agent")}  :red[{agentName}]""")
            
            container.write(_orch["rationale"]["text"].replace('$', r'\$'))

    if "observation" in _orch:
        _obs = _orch['observation']
        
        if 'knowledgeBaseLookupOutput' in _obs:
            with st.expander(get_trace_text("kb_response"), False, icon=":material/psychology:"):
                _refs = _obs['knowledgeBaseLookupOutput']['retrievedReferences']
                _ref_count = len(_refs)
                st.write(f"{_ref_count} {get_trace_text('references')}")
                for i, _ref in enumerate(_refs, 1):
                    st.write(f"  ({i}) {_ref['content']['text'][0:200]}...")
        
        if 'agentCollaboratorInvocationOutput' in _obs:
            # 处理collaborator agent的响应
            collab_name = _obs['agentCollaboratorInvocationOutput']['agentCollaboratorName']
            collab_output = _obs['agentCollaboratorInvocationOutput']['output']['text']
            with st.expander(get_trace_text("collaborator_response").format(collab_name), False, icon=":material/account-group:"):
                st.write(f"{get_trace_text('collaborator_name')}{collab_name}")
                st.markdown(collab_output.replace('$', r'\$'))
            
            # 保存collaborator的输出，以便在主UI中显示
            collaborator_output = collab_output

        if 'actionGroupInvocationOutput' in _obs:
            with st.expander(get_trace_text("tool_response"), False, icon=":material/psychology:"):
                st.write(_obs['actionGroupInvocationOutput']['text'].replace('$', r'\$'))

        if 'codeInterpreterInvocationOutput' in _obs:
            with st.expander(get_trace_text("code_interpreter"), False, icon=":material/psychology:"):
                if 'executionOutput' in _obs['codeInterpreterInvocationOutput']:
                    raw_output = _obs['codeInterpreterInvocationOutput']['executionOutput']
                    st.code(raw_output)

                if 'executionError' in _obs['codeInterpreterInvocationOutput']:
                    error_text = _obs['codeInterpreterInvocationOutput']['executionError']
                    st.write(f"{get_trace_text('code_error')}{error_text}")

                if 'files' in _obs['codeInterpreterInvocationOutput']:
                    files_generated = _obs['codeInterpreterInvocationOutput']['files']
                    st.write(f"{get_trace_text('files_generated')}{files_generated}")

        if 'finalResponse' in _obs:
            with st.expander(get_trace_text("agent_response"), False, icon=":material/psychology:"):
                st.write(_obs['finalResponse']['text'].replace('$', r'\$'))
            
    return step, inputTokens, outputTokens, collaborator_output

def get_error_text(key):
    """根据当前语言获取错误文本"""
    texts = {
        "中文": {
            "missing_config": "缺少必要的Agent配置信息。请在侧边栏配置Agent ID和Agent Alias ID。",
            "config_error": "配置错误：缺少必要的Agent配置信息。",
            "agent_mismatch": "无法获取必要的Agent配置信息。请确保提供了正确的Agent名称、ID或Alias ID。"
        },
        "English": {
            "missing_config": "Missing required Agent configuration. Please configure Agent ID and Agent Alias ID in the sidebar.",
            "config_error": "Configuration Error: Missing required Agent information.",
            "agent_mismatch": "Unable to get required Agent configuration. Please ensure you provided the correct Agent name, ID or Alias ID."
        }
    }
    
    language = st.session_state.get('language', "English")
    return texts[language][key]

def invoke_agent(input_text, session_id, task_yaml_content):
    """Main agent invocation and response processing."""
    # 检查配置中是否指定了区域
    _bot_config = st.session_state['bot_config']
    region = _bot_config.get('region', None)
    
    # 使用指定的区域创建 boto3 客户端（如果有的话）
    if region:
        client = boto3.client('bedrock-agent-runtime', region_name=region)
        agentClient = boto3.client('bedrock-agent', region_name=region)
    else:
        client = boto3.client('bedrock-agent-runtime')
        agentClient = boto3.client('bedrock-agent')
        
    # 检查是否有必要的配置信息
    if 'agent_id' not in _bot_config or 'agent_alias_id' not in _bot_config:
        st.error(get_error_text("missing_config"))
        return get_error_text("config_error")
    
    # Process tasks if any
    _tasks = []
    _bot_config = st.session_state['bot_config']
    for _task_name in task_yaml_content.keys():
        _curr_task = Task(_task_name, task_yaml_content, _bot_config['inputs'])
        _tasks.append(_curr_task)
        
    if len(_tasks) > 0:
        additional_instructions = _bot_config.get('additional_instructions')
        messagesStr = make_full_prompt(_tasks, additional_instructions)
    else:
        messagesStr = input_text

    # Invoke agent
    try:
        if 'session_attributes' in _bot_config:
            session_state = {
                "sessionAttributes": _bot_config['session_attributes']['sessionAttributes']
            }
            if 'promptSessionAttributes' in _bot_config['session_attributes']:
                session_state['promptSessionAttributes'] = _bot_config['session_attributes']['promptSessionAttributes']

            response = client.invoke_agent(
                agentId=_bot_config['agent_id'],
                agentAliasId=_bot_config['agent_alias_id'],
                sessionId=session_id,
                sessionState=session_state,
                inputText=messagesStr,
                enableTrace=True
            )
        else:
            response = client.invoke_agent(
                agentId=_bot_config['agent_id'],
                agentAliasId=_bot_config['agent_alias_id'],
                sessionId=session_id,
                inputText=messagesStr,
                enableTrace=True
            )
    except Exception as e:
        print(f"Error invoking agent: {e}")
        raise e

    # Process response
    step = 0.0
    _sub_agent_name = " "
    _time_before_routing = None
    inputTokens = 0
    outputTokens = 0
    _total_llm_calls = 0
    collaborator_response = None
    has_collaborator_output = False
    
    with st.spinner(get_trace_text("processing")):
        for event in response.get("completion"):
            if "chunk" in event:
                chunk_text = event["chunk"]["bytes"].decode("utf-8").replace('$', r'\$')
                # 如果不是空字符串，并且没有collaborator输出，则输出chunk
                if chunk_text.strip() and not has_collaborator_output:
                    yield chunk_text
                
            if "trace" in event:
                if 'routingClassifierTrace' in event['trace']['trace']:
                    #print("Processing routing trace...")
                    result = process_routing_trace(event, step, _sub_agent_name, _time_before_routing)
                    if result:
                        if len(result) == 5:  # Initial invocation
                            #print("Initial routing invocation")
                            _time_before_routing, step, _sub_agent_name, in_tokens, out_tokens = result
                            if in_tokens is not None or out_tokens is not None:
                                inputTokens += (in_tokens or 0)
                                outputTokens += (out_tokens or 0)
                                _total_llm_calls += 1
                        else:  # Subsequent invocation
                            #print("Subsequent routing invocation")
                            step, _sub_agent_name, in_tokens, out_tokens = result
                            if in_tokens is not None or out_tokens is not None:
                                inputTokens += (in_tokens or 0)
                                outputTokens += (out_tokens or 0)
                                _total_llm_calls += 1

                        
                if "orchestrationTrace" in event["trace"]["trace"]:
                    result = process_orchestration_trace(event, agentClient, step)
                    if result:
                        step, in_tokens, out_tokens, collab_output = result
                        if in_tokens is not None or out_tokens is not None:
                            inputTokens += (in_tokens or 0)
                            outputTokens += (out_tokens or 0)
                            _total_llm_calls += 1
                        
                        # 如果有collaborator输出，保存它
                        if collab_output:
                            collaborator_response = collab_output
                            has_collaborator_output = True

        # 如果有collaborator输出，直接返回它而不是supervisor的输出
        if has_collaborator_output and collaborator_response:
            yield "\n\n" + collaborator_response

        # Display token usage at the end
        container = st.container(border=True)
        container.markdown(f"{get_trace_text('total_input_tokens')}**{str(inputTokens)}**")
        container.markdown(f"{get_trace_text('total_output_tokens')}**{str(outputTokens)}**")
        container.markdown(f"{get_trace_text('total_llm_calls')}**{str(_total_llm_calls)}**")
