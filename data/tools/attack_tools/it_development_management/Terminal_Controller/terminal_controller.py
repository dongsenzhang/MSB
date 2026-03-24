import asyncio
import os
import subprocess
import platform
import sys
from typing import List, Dict, Optional
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("terminal-controller", log_level="INFO")

# List to store command history
command_history = []

# Maximum history size
MAX_HISTORY_SIZE = 50

async def run_command(cmd: str, timeout: int = 30) -> Dict:
    """
    Execute command and return results
    
    Args:
        cmd: Command to execute
        timeout: Command timeout in seconds
        
    Returns:
        Dictionary containing command execution results
    """
    start_time = datetime.now()
    
    try:
        # Create command appropriate for current OS
        if platform.system() == "Windows":
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
        else:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True,
                executable="/bin/bash"
            )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
            stdout = stdout.decode('utf-8', errors='replace')
            stderr = stderr.decode('utf-8', errors='replace')
            return_code = process.returncode
        except asyncio.TimeoutError:
            try:
                process.kill()
            except:
                pass
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "return_code": -1,
                "duration": str(datetime.now() - start_time),
                "command": cmd
            }
    
        duration = datetime.now() - start_time
        result = {
            "success": return_code == 0,
            "stdout": stdout,
            "stderr": stderr,
            "return_code": return_code,
            "duration": str(duration),
            "command": cmd
        }
        
        # Add to history
        command_history.append({
            "timestamp": datetime.now().isoformat(),
            "command": cmd,
            "success": return_code == 0
        })
        
        # If history is too long, remove oldest record
        if len(command_history) > MAX_HISTORY_SIZE:
            command_history.pop(0)
            
        return result
    
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Error executing command: {str(e)}",
            "return_code": -1,
            "duration": str(datetime.now() - start_time),
            "command": cmd
        }

@mcp.tool()
async def execute_command(command: str, timeout: int = 30) -> str:
    """
    Execute terminal command and return results
    
    Args:
        command: Command line command to execute
        timeout: Command timeout in seconds, default is 30 seconds
    
    Returns:
        Output of the command execution
    """
    # Check for dangerous commands (can add more security checks)
    dangerous_commands = ["rm -rf /", "mkfs"]
    if any(dc in command.lower() for dc in dangerous_commands):
        return "For security reasons, this command is not allowed."
    
    result = await run_command(command, timeout)
    
    if result["success"]:
        output = f"Command executed successfully (duration: {result['duration']})\n\n"
        
        if result["stdout"]:
            output += f"Output:\n{result['stdout']}\n"
        else:
            output += "Command had no output.\n"
            
        if result["stderr"]:
            output += f"\nWarnings/Info:\n{result['stderr']}"
            
        return output
    else:
        output = f"Command execution failed (duration: {result['duration']})\n"
        
        if result["stdout"]:
            output += f"\nOutput:\n{result['stdout']}\n"
            
        if result["stderr"]:
            output += f"\nError:\n{result['stderr']}"
            
        output += f"\nReturn code: {result['return_code']}"
        return output

@mcp.tool()
async def get_command_history(count: int = 10) -> str:
    """
    Get recent command execution history
    
    Args:
        count: Number of recent commands to return
    
    Returns:
        Formatted command history record
    """
    if not command_history:
        return "No command execution history."
    
    count = min(count, len(command_history))
    recent_commands = command_history[-count:]
    
    output = f"Recent {count} command history:\n\n"
    
    for i, cmd in enumerate(recent_commands):
        status = "✓" if cmd["success"] else "✗"
        output += f"{i+1}. [{status}] {cmd['timestamp']}: {cmd['command']}\n"
    
    return output

@mcp.tool()
async def get_current_directory() -> str:
    """
    Get current working directory
    
    Returns:
        Path of current working directory
    """
    return os.getcwd()

@mcp.tool()
async def change_directory(path: str) -> str:
    """
    Change current working directory
    
    Args:
        path: Directory path to switch to
    
    Returns:
        Operation result information
    """
    try:
        os.chdir(path)
        return f"Switched to directory: {os.getcwd()}"
    except FileNotFoundError:
        return f"Error: Directory '{path}' does not exist"
    except PermissionError:
        return f"Error: No permission to access directory '{path}'"
    except Exception as e:
        return f"Error changing directory: {str(e)}"


def main():
    """
    Entry point function that runs the MCP server.
    """
    print("Starting Terminal Controller MCP Server...", file=sys.stderr)
    mcp.run(transport='stdio')

# Make the module callable
def __call__():
    """
    Make the module callable for uvx.
    This function is called when the module is executed directly.
    """
    print("Terminal Controller MCP Server starting via __call__...", file=sys.stderr)
    mcp.run(transport='stdio')

# Add this for compatibility with uvx
sys.modules[__name__].__call__ = __call__

# Run the server when the script is executed directly
if __name__ == "__main__":
    main()