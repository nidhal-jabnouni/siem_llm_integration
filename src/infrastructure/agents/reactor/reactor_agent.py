# src/infrastructure/agents/reactor/langgraph_reactor_agent.py
from typing import Dict, Any, List, Annotated

from langchain_core.runnables.graph import MermaidDrawMethod
from typing_extensions import TypedDict
import operator
import datetime
import json
import logging
import traceback
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import AzureChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from chromadb import PersistentClient

from src.infrastructure.agents.reactor.tools import get_all_tools  # Absolute import
from src.infrastructure.config.settings import load_config
from src.infrastructure.embeddings.embedder import get_azure_embedding, AzureEmbeddingFunction
import os

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State of the agent workflow"""
    messages: Annotated[List[BaseMessage], operator.add]
    issue: str
    context: str
    tools_used: List[str]
    current_step: str
    processing_start: datetime.datetime
    error_count: int
    max_iterations: int
    iteration_count: int
    tool_decisions: List[Dict[str, Any]]  # Store tool decisions for manual execution


class LangGraphReactorAgent:
    """Security Response Agent using LangGraph for workflow management"""

    def __init__(self):
        self.config = load_config()
        self._initialize_components()
        self._create_workflow()

    def _initialize_components(self):
        """Initialize all necessary components"""
        self._initialize_llm()
        self._initialize_database()
        self._initialize_tools()

    def _initialize_llm(self):
        """Initialize Azure OpenAI connection"""
        try:
            self.llm = AzureChatOpenAI(
                api_key=self.config.azure_openai_api_key,
                api_version=self.config.azure_openai_api_version,
                azure_endpoint=self.config.azure_openai_endpoint,
                deployment_name=self.config.azure_deployment_name,
                temperature=0.1
            )
            logger.info("Success: Azure OpenAI connection initialized")
        except Exception as e:
            logger.error(f"Error: Failed to initialize Azure OpenAI: {e}")
            logger.debug(traceback.format_exc())
            raise

    def _initialize_database(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, '..', '..', '..', '..', 'chroma_known_problems_db')
            logger.debug(f"Database path: {db_path}")

            if not os.path.exists(db_path):
                logger.error(f"Database directory not found: {db_path}")
                self.collection = None
                return

            self.client = PersistentClient(path=db_path)
            logger.debug(f"Database client initialized: {self.client}")

            self.collection = self.client.get_collection(
                name="known_problems",
                embedding_function=AzureEmbeddingFunction()
            )
            logger.info(f"Success: Connected to knowledge base with {self.collection.count()} documents")
        except Exception as e:
            logger.exception("CRITICAL: Database initialization failed")
            self.collection = None

    def _initialize_tools(self):
        """Initialize available security tools"""
        try:
            self.tools = get_all_tools()
            logger.debug(f"Loaded tools: {[t.name for t in self.tools]}")

            # Create a dictionary for easy tool lookup
            self.tools_dict = {tool.name: tool for tool in self.tools}

            logger.info(f"Success: Initialized {len(self.tools)} security tools")
        except Exception as e:
            logger.exception("Tool initialization failed")
            self.tools = []
            self.tools_dict = {}

    def _create_workflow(self):
        """Create the LangGraph workflow"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("analyze_issue", self._analyze_issue_node)
        workflow.add_node("execute_tools", self._execute_tools_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("error_handler", self._error_handler_node)

        # Set entry point
        workflow.set_entry_point("retrieve_context")

        # Add edges
        workflow.add_edge("retrieve_context", "analyze_issue")
        workflow.add_conditional_edges(
            "analyze_issue",
            self._should_use_tools,
            {
                "use_tools": "execute_tools",
                "generate_response": "generate_response",
                "error": "error_handler"
            }
        )
        workflow.add_conditional_edges(
            "execute_tools",
            self._should_continue,
            {
                "continue": "analyze_issue",
                "finish": "generate_response",
                "error": "error_handler"
            }
        )
        workflow.add_edge("generate_response", END)
        workflow.add_edge("error_handler", END)

        self.graph = workflow.compile()
        #
        # try:
        #     graph = self.graph.get_graph()
        #     png_data = graph.draw_mermaid_png(draw_method=MermaidDrawMethod.PYPPETEER)
        #     with open("workflow.png", "wb") as f:
        #         f.write(png_data)
        #     logger.info("Workflow graph saved as workflow.png")
        # except Exception as e:
        #     logger.error(f"Failed to visualize workflow: {e}")

    def _retrieve_context_node(self, state: AgentState) -> Dict[str, Any]:
        """Node to retrieve context from knowledge base"""
        try:
            logger.debug(f"Retrieving context for: {state['issue'][:50]}...")
            context = self._retrieve_context(state["issue"])
            return {
                "context": context,
                "current_step": "context_retrieved"
            }
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            logger.debug(traceback.format_exc())
            return {
                "context": f"Context retrieval failed: {str(e)}",
                "current_step": "context_error",
                "error_count": state.get("error_count", 0) + 1
            }

    def _analyze_issue_node(self, state: AgentState) -> Dict[str, Any]:
        """Node to analyze the security issue and determine actions"""
        try:
            logger.debug(f"Analyzing issue. Context: {state.get('context', '')[:100]}...")
            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(state["issue"], state["context"])

            # Get LLM response WITHOUT tool binding - just regular invoke
            response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
            logger.debug(f"Analysis response: {response.content[:200]}...")

            # Parse the response to extract tool decisions
            tool_decisions = self._parse_tool_decisions(response.content)

            # Add to messages
            messages = [HumanMessage(content=analysis_prompt), response]

            return {
                "messages": messages,
                "tool_decisions": tool_decisions,
                "current_step": "issue_analyzed",
                "iteration_count": state.get("iteration_count", 0) + 1
            }

        except Exception as e:
            logger.error(f"Issue analysis failed: {e}")
            logger.debug(traceback.format_exc())
            return {
                "current_step": "analysis_error",
                "error_count": state.get("error_count", 0) + 1
            }

    def _parse_tool_decisions(self, response_content: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract tool usage decisions"""
        tool_decisions = []

        # Look for structured tool calls in the response
        # This is a simple parser - you might want to make it more sophisticated
        lines = response_content.lower().split('\n')

        for line in lines:
            # Look for tool mentions
            if 'block_ip' in line and any(keyword in line for keyword in ['use', 'call', 'execute', 'run']):
                # Extract IP if mentioned
                import re
                ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                ip_match = re.search(ip_pattern, response_content)
                if ip_match:
                    tool_decisions.append({
                        'tool_name': 'block_ip',
                        'arguments': {'ip_address': ip_match.group()}
                    })

            elif 'isolate_host' in line and any(keyword in line for keyword in ['use', 'call', 'execute', 'run']):
                # Look for hostname in the original issue or response
                import re
                host_pattern = r'\b[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\b'
                host_matches = re.findall(host_pattern, response_content)
                # Filter for likely hostnames (not IPs)
                hostnames = [h for h in host_matches if not re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', h)]
                if hostnames:
                    tool_decisions.append({
                        'tool_name': 'isolate_host',
                        'arguments': {'hostname': hostnames[0]}
                    })

            elif 'generate_alert' in line and any(keyword in line for keyword in ['use', 'call', 'execute', 'run']):
                tool_decisions.append({
                    'tool_name': 'generate_alert',
                    'arguments': {'message': 'Security incident detected', 'severity': 'high'}
                })

        if tool_decisions:
            logger.info(f"Parsed tool decisions: {[td['tool_name'] for td in tool_decisions]}")
        else:
            logger.info("No tool decisions found in response")

        return tool_decisions

    def _execute_tools_node(self, state: AgentState) -> Dict[str, Any]:
        """Node to execute tools based on LLM decisions"""
        try:
            tool_decisions = state.get("tool_decisions", [])

            if not tool_decisions:
                logger.info("No tool decisions to execute")
                return {"current_step": "no_tools_needed"}

            logger.info(f"Executing {len(tool_decisions)} tool decisions")

            tools_used = state.get("tools_used", [])
            tool_results = []

            for decision in tool_decisions:
                tool_name = decision['tool_name']
                arguments = decision['arguments']

                if tool_name not in self.tools_dict:
                    logger.error(f"Tool '{tool_name}' not found in available tools")
                    continue

                try:
                    tool = self.tools_dict[tool_name]
                    logger.info(f"Executing tool: {tool_name} with args: {arguments}")

                    # Use invoke instead of calling directly
                    result = tool.invoke(arguments)

                    tools_used.append(tool_name)
                    tool_results.append({
                        'tool_name': tool_name,
                        'arguments': arguments,
                        'result': result
                    })

                    logger.info(f"Tool {tool_name} executed successfully")

                except Exception as e:
                    logger.error(f"Failed to execute tool {tool_name}: {e}")
                    tool_results.append({
                        'tool_name': tool_name,
                        'arguments': arguments,
                        'result': f"Error: {str(e)}"
                    })

            # Create tool messages for the conversation
            tool_messages = []
            for result in tool_results:
                tool_msg = ToolMessage(
                    content=f"Tool {result['tool_name']} result: {result['result']}",
                    tool_call_id=f"{result['tool_name']}_call"
                )
                tool_messages.append(tool_msg)

            return {
                "messages": tool_messages,
                "tools_used": tools_used,
                "current_step": "tools_executed",
                "tool_results": tool_results
            }

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            logger.debug(traceback.format_exc())
            return {
                "current_step": "tool_error",
                "error_count": state.get("error_count", 0) + 1
            }

    def _generate_response_node(self, state: AgentState) -> Dict[str, Any]:
        """Node to generate final response"""
        try:
            logger.debug("Generating final response")
            # Create summary prompt
            summary_prompt = self._create_summary_prompt(state)

            # Get final response from LLM
            final_response = self.llm.invoke([HumanMessage(content=summary_prompt)])

            return {
                "messages": [HumanMessage(content=summary_prompt), final_response],
                "current_step": "response_generated"
            }

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            logger.debug(traceback.format_exc())
            return {
                "current_step": "response_error",
                "error_count": state.get("error_count", 0) + 1
            }

    def _error_handler_node(self, state: AgentState) -> Dict[str, Any]:
        """Node to handle errors and provide fallback responses"""
        logger.error(
            f"ERROR HANDLER TRIGGERED | "
            f"Step: {state.get('current_step')} | "
            f"Errors: {state.get('error_count')} | "
            f"Messages: {len(state.get('messages', []))} | "
            f"Iteration: {state.get('iteration_count', 0)}/{state.get('max_iterations', 5)}"
        )

        fallback_response = self._fallback_response(state["issue"], state.get("context", ""))

        return {
            "messages": [AIMessage(content=fallback_response)],
            "current_step": "error_handled"
        }

    def _should_use_tools(self, state: AgentState) -> str:
        """Conditional logic to determine if tools should be used"""
        try:
            logger.debug(
                f"Tool decision: errors={state.get('error_count')}, "
                f"step={state.get('current_step')}, "
                f"iter={state.get('iteration_count', 0)}"
            )

            if state.get("error_count", 0) > 2:
                logger.warning("Exceeded max errors, routing to error handler")
                return "error"

            # Check if we have tool decisions to execute
            tool_decisions = state.get("tool_decisions", [])
            if tool_decisions:
                logger.info(f"Tool decisions found: {[td['tool_name'] for td in tool_decisions]}")
                return "use_tools"

            logger.info("No tool decisions found, generating direct response")
            return "generate_response"

        except Exception as e:
            logger.error(f"Error in tool decision routing: {e}")
            logger.debug(traceback.format_exc())
            return "error"

    def _should_continue(self, state: AgentState) -> str:
        """Conditional logic to determine if processing should continue"""
        try:
            logger.debug(
                f"Continue decision: errors={state.get('error_count')}, "
                f"step={state.get('current_step')}, "
                f"iter={state.get('iteration_count', 0)}/{state.get('max_iterations', 5)}"
            )

            if state.get("error_count", 0) > 2:
                logger.warning("Max errors exceeded, stopping workflow")
                return "error"

            if state.get("iteration_count", 0) >= state.get("max_iterations", 5):
                logger.info("Max iterations reached, finishing workflow")
                return "finish"

            # Check if we need to continue analyzing
            if state.get("current_step") == "tools_executed":
                logger.info("Tool results need analysis, continuing workflow")
                return "continue"

            return "finish"

        except Exception as e:
            logger.error(f"Error in continue decision: {e}")
            logger.debug(traceback.format_exc())
            return "error"

    def _create_analysis_prompt(self, issue: str, context: str) -> str:
        """Create prompt for issue analysis"""
        return f"""You are a Security Response Agent specialized in automated incident response.

SECURITY ISSUE: {issue}

RELEVANT CONTEXT FROM KNOWLEDGE BASE:
{context}

AVAILABLE TOOLS:
{self._format_tools_description()}

Your task is to analyze this security issue and determine the appropriate response actions.

Consider:
1. The severity and type of security issue
2. Relevant context from similar past incidents
3. Which tools (if any) should be used to address this issue
4. The order in which actions should be taken

If you determine that tools should be used, please specify clearly in your response which tools to use and why. Use phrases like:
- "I recommend using the block_ip tool to..."
- "Execute the isolate_host tool for..."
- "Generate an alert using the generate_alert tool..."

Provide your analysis and tool recommendations clearly.
"""

    def _create_summary_prompt(self, state: AgentState) -> str:
        """Create prompt for final response summary"""
        tools_used = ", ".join(state.get("tools_used", [])) or "None"
        tool_results = state.get("tool_results", [])

        tool_results_text = ""
        if tool_results:
            tool_results_text = "\n".join([
                f"- {result['tool_name']}: {result['result']}"
                for result in tool_results
            ])

        return f"""Based on the security issue analysis and actions taken, provide a comprehensive summary.

ORIGINAL ISSUE: {state['issue']}
TOOLS USED: {tools_used}
TOOL RESULTS:
{tool_results_text}
CONTEXT USED: {state.get('context', 'None')[:200]}...

Please provide a final summary that includes:
1. Issue assessment and severity
2. Actions taken (if any)
3. Current status
4. Any follow-up recommendations
5. Monitoring suggestions

Format your response clearly and professionally for the security operations team.
"""

    def _format_tools_description(self) -> str:
        """Format available tools for prompt"""
        return "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])

    def _retrieve_context(self, issue: str, n_results: int = 3) -> str:
        """Retrieve relevant context from known problems database"""
        if not self.collection:
            logger.warning("Knowledge base not available for context retrieval")
            return "No context available - knowledge base not connected"

        try:
            logger.debug(f"Querying knowledge base: {issue[:50]}...")
            results = self.collection.query(
                query_texts=[issue],
                n_results=n_results
            )

            if not results['documents'][0]:
                logger.info("No similar issues found in knowledge base")
                return "No similar issues found in knowledge base"

            context_parts = []
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
                context_parts.append(f"{i}. Problem: {doc}")
                context_parts.append(f"   Solution: {metadata.get('fix', 'No solution provided')}")
                context_parts.append("")

            context_str = "\n".join(context_parts)
            logger.info(f"Retrieved {len(results['documents'][0])} similar cases from knowledge base")
            return context_str

        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            logger.debug(traceback.format_exc())
            return f"Context retrieval failed: {str(e)}"

    def _fallback_response(self, issue: str, context: str) -> str:
        """Fallback response when processing fails"""
        issue_lower = issue.lower()
        logger.warning(f"Generating fallback response for: {issue}")

        if "ip" in issue_lower and any(word in issue_lower for word in ["block", "attack", "dos", "ddos"]):
            return "🔧 FALLBACK RESPONSE: Recommend using block_ip tool to block malicious IP addresses"
        elif any(word in issue_lower for word in ["malware", "virus", "infection"]):
            return "🔧 FALLBACK RESPONSE: Recommend using isolate_host tool and execute_script for malware removal"
        elif any(word in issue_lower for word in ["alert", "notify", "escalate"]):
            return "🔧 FALLBACK RESPONSE: Recommend using generate_alert tool to notify SOC team"
        else:
            return f"🔧 FALLBACK RESPONSE: Security issue detected. Context from knowledge base:\n{context[:200]}..."

    def react_to_issue(self, issue: str, max_iterations: int = 5) -> dict:
        """Main method to process security issues using LangGraph"""
        start_time = datetime.datetime.now()

        logger.info(f"Processing security issue: {issue[:100]}...")
        logger.debug(f"Max iterations: {max_iterations}")

        # Initialize state
        initial_state = {
            "issue": issue,
            "context": "",
            "messages": [],
            "tools_used": [],
            "tool_decisions": [],
            "current_step": "initialized",
            "processing_start": start_time,
            "error_count": 0,
            "max_iterations": max_iterations,
            "iteration_count": 0
        }

        try:
            # Execute the workflow
            logger.debug("Starting workflow execution")
            final_state = self.graph.invoke(initial_state)
            logger.debug("Workflow execution completed")

            # Extract final response
            if final_state.get("messages"):
                final_message = final_state["messages"][-1]
                response = final_message.content if hasattr(final_message, 'content') else str(final_message)
                logger.debug(f"Final response: {response[:200]}...")
            else:
                response = "No response generated"
                logger.warning("No messages in final state")

            success = final_state.get("current_step") not in ["error_handled", "response_error", "analysis_error"]

        except Exception as e:
            logger.critical(f"Workflow execution failed: {e}")
            logger.debug(traceback.format_exc())
            response = self._fallback_response(issue, "")
            success = False
            final_state = initial_state

        # Calculate processing time
        end_time = datetime.datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Return structured response
        return {
            "issue": issue,
            "response": response,
            "context_used": final_state.get("context", ""),
            "processing_time": processing_time,
            "timestamp": end_time.isoformat(),
            "success": success,
            "tools_available": [tool.name for tool in self.tools],
            "tools_used": final_state.get("tools_used", []),
            "iterations": final_state.get("iteration_count", 0),
            "final_step": final_state.get("current_step", "unknown"),
            "error_count": final_state.get("error_count", 0)
        }


# Convenience function for direct usage
def react_to_issue(issue: str, max_iterations: int = 5) -> dict:
    """Direct function to process security issue using LangGraph"""
    agent = LangGraphReactorAgent()
    return agent.react_to_issue(issue, max_iterations)


# Test and demonstration
if __name__ == "__main__":

    print("Testing LangGraph Reactor Agent...")
    print("=" * 50)

    # Test cases
    test_cases = [
        "DOS attack detected from IP 192.168.1.100",
        "Malware infection found on host WEB-SERVER-01",
        "Unauthorized access attempt from user account",
        "Suspicious network traffic detected"
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case}")
        print("-" * 40)

        try:
            result = react_to_issue(test_case)
            print(f"Success: {result['success']}")
            print(f"Processing Time: {result['processing_time']:.2f}s")
            print(f"Tools Used: {', '.join(result['tools_used']) if result['tools_used'] else 'None'}")
            print(f"Iterations: {result['iterations']}")
            print(f"Final Step: {result['final_step']}")
            print(f"Error Count: {result['error_count']}")
            print(f"Response: {result['response'][:200]}...")

        except Exception as e:
            print(f"Error: Test failed: {e}")
            print(traceback.format_exc())

        print()

    print("Testing completed!")