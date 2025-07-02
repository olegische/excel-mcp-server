import asyncio
import os
import typer

from .server import run_sse, run_stdio

app = typer.Typer(help="Excel MCP Server")

@app.command()
def sse(
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8660, "--port", "-p", help="Port to bind to")
):
    """Start Excel MCP Server in SSE mode"""
    # Set environment variables for host and port
    os.environ["HOST"] = host
    os.environ["PORT"] = str(port)
    
    print("Excel MCP Server - SSE mode")
    print("----------------------")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print("Press Ctrl+C to exit")
    try:
        asyncio.run(run_sse())
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Service stopped.")

@app.command()
def stdio():
    """Start Excel MCP Server in stdio mode"""
    try:
        run_stdio()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Service stopped.")

if __name__ == "__main__":
    app()
