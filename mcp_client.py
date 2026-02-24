import subprocess
import json
import os
import sys
import argparse

try:
    import ollama
except ImportError:
    print("Error: The 'ollama' package is required.")
    print("Please install it running: pip install ollama")
    sys.exit(1)

class MCPSubprocessClient:
    """
    A minimal MCP Client class.
    Spawns the Benchmark MCP Server subprocess and communicates via stdio (JSON-RPC 2.0 messages).
    Provides safe, isolated, read-only system interaction logic.
    """
    def __init__(self, script_path):
        # Start the Python MCP server process
        self.process = subprocess.Popen(
            [sys.executable, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        self.msg_id = 0

    def send_request(self, method, params=None):
        """Sends a JSON-RPC request and expects a response back."""
        self.msg_id += 1
        req = {
            "jsonrpc": "2.0",
            "id": self.msg_id,
            "method": method
        }
        if params:
            req["params"] = params
            
        # Write to the server and read its synchronous result
        self.process.stdin.write(json.dumps(req) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        return json.loads(line)

    def send_notification(self, method, params=None):
        """Sends a JSON-RPC notification (fire-and-forget, no ID)."""
        req = {
            "jsonrpc": "2.0",
            "method": method
        }
        if params:
            req["params"] = params
        self.process.stdin.write(json.dumps(req) + "\n")
        self.process.stdin.flush()

def main():
    print("=== GenAI Benchmarking Assistant over MCP (Ollama LLaMA 3.2) ===\n")
    
    server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")
    client = MCPSubprocessClient(server_path)
    
    # ---------------------------
    # 1. MCP Handshake
    # ---------------------------
    print("[1] Initializing Benchmarking MCP Server...")
    client.send_request("initialize", {
        "protocolVersion": "2024-11-05", 
        "capabilities": {}, 
        "clientInfo": {"name": "benchmark-client", "version": "1.0"}
    })
    client.send_notification("notifications/initialized")
    
    # ---------------------------
    # 2. Fetch Tools from Server
    # ---------------------------
    print("[2] Discovering Benchmarking Tools...")
    tools_res = client.send_request("tools/list")
    mcp_tools = tools_res.get("result", {}).get("tools", [])
    print(f"    -> Tools exposed: {[t['name'] for t in mcp_tools]}")
    
    # ---------------------------
    # 3. Connect to Ollama Model
    # ---------------------------
    print("[3] Bootstrapping GenAI Controller with exposed tools...")
    ollama_tools = [{
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["inputSchema"]
        }
    } for t in mcp_tools]
    
    system_instruction = (
        "You are an expert Performance Engineer and Systems Analyst. "
        "The user will ask you to benchmark their system. "
        "You must independently decide which benchmark tools to call, collect their metrics, and synthesize the data. "
        "Always call the benchmarking tools provided. "
        "Once you gather the data, provide human-readable insights, identify potential bottlenecks, "
        "comparative analyses (e.g., strong vs weak points), and optimization suggestions."
    )
    
    parser = argparse.ArgumentParser(description="GenAI Benchmarking Assistant over MCP")
    parser.add_argument("--prompt", type=str, default="Check my system performance and suggest improvements. Make sure to run all CPU, memory, and IO benchmarks for a complete view.", help="Custom prompt for the assistant")
    args = parser.parse_args()
    
    user_prompt = args.prompt
    print(f"\n[User]: {user_prompt}\n")
    
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt}
    ]
    
    print("[4] Prompting AI model for tool usage evaluation...")
    
    # ---------------------------
    # 4. Handle Function / Tool Calls Loop
    # ---------------------------
    max_turns = 10
    turn = 0
    
    while turn < max_turns:
        turn += 1
        
        try:
            response = ollama.chat(
                model='llama3.2',
                messages=messages,
                tools=ollama_tools
            )
        except Exception as e:
            print(f"\n[Error connecting to Ollama]: {e}")
            print("Please ensure Ollama is running and 'llama3.2' model is available (run `ollama pull llama3.2`).")
            break
        
        message = response.get('message', {})
        messages.append(message)
        
        if not message.get('tool_calls'):
            print(f"\n[AI Analyst Final Report]:\n{'-'*40}\n{message.get('content', '').strip()}\n{'-'*40}")
            break
        
        for tool_call in message['tool_calls']:
            tool_name = tool_call['function']['name']
            tool_args = tool_call['function']['arguments']
            
            print(f"\n  [AI Requests Exec] -> {tool_name}({tool_args})")
            
            # Forward to MCP Server
            mcp_res = client.send_request("tools/call", {"name": tool_name, "arguments": tool_args})
            
            content = mcp_res.get("result", {}).get("content", [])
            text_result = content[0]["text"] if content else "{}"
            
            print(f"  [MCP Server Data ] -> {text_result}")
            
            messages.append({
                'role': 'tool',
                'name': tool_name,
                'content': str(text_result)
            })
            
        print("\n  [Uploading results back to AI Controller for analysis...]")

    # Cleanup
    client.process.terminate()
    print("\n=== Exited GenAI Benchmarking Flow ===")

if __name__ == '__main__':
    main()
