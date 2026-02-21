import sys
import json
import time
import math
import os
import platform

# ==========================================
# 1. Provide safe benchmarking and info tools
# ==========================================

def get_system_info():
    """Returns basic system hardware and OS information."""
    try:
        # psutil would be better, but we stick to standard Python for the PoC
        info = {
            "os": platform.system(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "cpu_cores": os.cpu_count(),
        }
        
        # A rough attempt to get RAM without psutil (works on POSIX)
        try:
            if platform.system() == "Darwin":
                 # macOS
                 mem_bytes = int(os.popen('sysctl -n hw.memsize').read().strip())
                 info["total_ram_gb"] = round(mem_bytes / (1024**3), 2)
            elif platform.system() == "Linux":
                 mem_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
                 info["total_ram_gb"] = round(mem_bytes / (1024**3), 2)
            else:
                 info["total_ram_gb"] = "Unknown (Requires psutil)"
        except Exception:
            info["total_ram_gb"] = "Unknown"

        return json.dumps(info)
    except Exception as e:
        return json.dumps({"error": str(e)})

def run_cpu_benchmark():
    """Runs a lightweight CPU-bound task and returns execution metrics."""
    # A simple prime-finding loop to stress the CPU briefly
    start_time = time.time()
    
    primes = []
    limit = 50000 # Adjust for longer/shorter benchmark
    
    for num in range(2, limit):
        is_prime = True
        for i in range(2, int(math.isqrt(num)) + 1):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(num)
            
    end_time = time.time()
    execution_time = round(end_time - start_time, 4)
    
    metrics = {
        "benchmark_type": "CPU Prime Calculation",
        "limit": limit,
        "primes_found": len(primes),
        "execution_time_seconds": execution_time,
        "score": round(10000 / execution_time) if execution_time > 0 else "N/A"
    }
    return json.dumps(metrics)

def run_memory_benchmark():
    """Runs a memory allocation and access speed benchmark."""
    start_time = time.time()
    
    # Allocate a large list (approx 50MB of integers depending on platform)
    size = 5 * 10**6
    # Allocation
    large_array = [0] * size
    allocation_time = time.time() - start_time
    
    # Access/Modification
    start_mod = time.time()
    for i in range(size):
        large_array[i] = i * 2
    modification_time = time.time() - start_mod
    
    end_time = time.time()
    total_time = round(end_time - start_time, 4)
    
    metrics = {
        "benchmark_type": "Memory Allocation & Modification",
        "elements": size,
        "allocation_time_seconds": round(allocation_time, 4),
        "modification_time_seconds": round(modification_time, 4),
        "total_time_seconds": total_time,
        "operations_per_second": round(size / modification_time) if modification_time > 0 else "N/A"
    }
    
    del large_array # free memory
    return json.dumps(metrics)

def run_io_benchmark():
    """Runs a file write/read speed benchmark."""
    test_file = "io_test_benchmark.tmp"
    
    # We will write ~50 MB of data
    data_chunk = b"A" * 1024 * 1024  # 1 MB chunk
    num_chunks = 50
    
    try:
        # Write test
        start_write = time.time()
        with open(test_file, "wb") as f:
            for _ in range(num_chunks):
                f.write(data_chunk)
        write_time = time.time() - start_write
        
        # Read test
        start_read = time.time()
        with open(test_file, "rb") as f:
            while f.read(1024 * 1024):
                pass
        read_time = time.time() - start_read
        
        # Cleanup
        os.remove(test_file)
        
        write_speed_mb_s = round(num_chunks / write_time, 2) if write_time > 0 else 0
        read_speed_mb_s = round(num_chunks / read_time, 2) if read_time > 0 else 0
        
        metrics = {
            "benchmark_type": "Disk I/O 50MB Sequential",
            "write_time_seconds": round(write_time, 4),
            "read_time_seconds": round(read_time, 4),
            "write_speed_MB_s": write_speed_mb_s,
            "read_speed_MB_s": read_speed_mb_s
        }
        return json.dumps(metrics)
    except Exception as e:
         return json.dumps({"error": f"I/O Benchmark failed: {str(e)}"})

# ==========================================
# 2. Schema definitions for MCP
# ==========================================
TOOLS = [
    {
        "name": "get_system_info",
        "description": "Returns basic system hardware and OS information (OS, CPU cores, RAM).",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "run_cpu_benchmark",
        "description": "Runs a lightweight CPU-bound task (prime calculation) and returns execution metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "run_memory_benchmark",
        "description": "Measures memory allocation and modification speeds.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "run_io_benchmark",
        "description": "Measures sequential file read/write speeds over a 50MB payload.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

# ==========================================
# 3. Main Server Loop (STDIO based)
# ==========================================
def main():
    """
    The MCP server runs in an infinite loop. 
    It reads JSON-RPC 2.0 requests from stdin and writes responses to stdout.
    This architecture cleanly separates tool availability from the AI client's logic.
    """
    for line in sys.stdin:
        if not line.strip():
            continue
            
        try:
            req = json.loads(line)
            method = req.get("method")
            msg_id = req.get("id")

            # ---------------------------
            # INIT PHASE: handshake
            # ---------------------------
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05", # Standard MCP protocol version spec
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "benchmark-mcp-server", "version": "1.0.0"}
                    }
                }
            
            # ---------------------------
            # DISCOVERY: client asks for tools
            # ---------------------------
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": TOOLS
                    }
                }
            
            # ---------------------------
            # EXECUTION: client calls a tool
            # ---------------------------
            elif method == "tools/call":
                params = req.get("params", {})
                tool_name = params.get("name")
                
                content = []
                is_error = False
                
                try:
                    # Route request to correct Python function
                    if tool_name == "get_system_info":
                        result = get_system_info()
                        content.append({"type": "text", "text": result})
                        
                    elif tool_name == "run_cpu_benchmark":
                        result = run_cpu_benchmark()
                        content.append({"type": "text", "text": result})
                        
                    elif tool_name == "run_memory_benchmark":
                        result = run_memory_benchmark()
                        content.append({"type": "text", "text": result})
                        
                    elif tool_name == "run_io_benchmark":
                        result = run_io_benchmark()
                        content.append({"type": "text", "text": result})
                        
                    else:
                        is_error = True
                        content.append({"type": "text", "text": f"Unknown tool: {tool_name}"})
                        
                except Exception as e:
                    is_error = True
                    content.append({"type": "text", "text": str(e)})

                # Format MCP execution response
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": content,
                        "isError": is_error
                    }
                }

            else:
                # Handle unknown methods or notifications (which don't have an ID)
                if msg_id is not None:
                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32601, "message": "Method not found"}
                    }
                else:
                    response = None 

            # Send the JSON-RPC response back to the client via stdout
            if response:
                print(json.dumps(response), flush=True)

        except json.JSONDecodeError:
            # Handle invalid JSON formatting
            msg = {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}
            print(json.dumps(msg), flush=True)

if __name__ == "__main__":
    main()
