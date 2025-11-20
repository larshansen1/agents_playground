#!/usr/bin/env python3
"""
WebSocket client test script.

This script connects to the WebSocket endpoint and listens for
real-time task status updates.

Usage:
    python test_websocket.py

In another terminal, create/update tasks and see the updates here in real-time.
"""

import asyncio
import websockets
import ssl
import json
import sys


async def listen_to_updates():
    """Connect to WebSocket and listen for task updates."""
    # Setup SSL context for client certificate
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.load_cert_chain('certs/client-cert.pem', 'certs/client-key.pem')
    ssl_context.load_verify_locations('certs/ca-cert.pem')
    
    uri = "wss://localhost:8443/ws"
    
    print("=" * 60)
    print("WebSocket Client - Task Status Updates")
    print("=" * 60)
    print(f"\nConnecting to {uri}...")
    
    try:
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            print("✓ Connected to WebSocket endpoint!")
            print("\nListening for task updates... (Press Ctrl+C to stop)\n")
            
            # Send periodic pings to keep connection alive
            async def send_ping():
                while True:
                    await asyncio.sleep(30)
                    await websocket.send("ping")
            
            ping_task = asyncio.create_task(send_ping())
            
            try:
                while True:
                    # Wait for messages from server
                    message = await websocket.recv()
                    
                    # Handle pong response
                    if message == "pong":
                        continue
                    
                    # Parse and display task update
                    try:
                        data = json.loads(message)
                        print("-" * 60)
                        print(f"Task Update Received:")
                        print(f"  Task ID: {data['task_id']}")
                        print(f"  Type: {data['type']}")
                        print(f"  Status: {data['status']}")
                        if data.get('output'):
                            print(f"  Output: {json.dumps(data['output'], indent=2)}")
                        if data.get('error'):
                            print(f"  Error: {data['error']}")
                        print(f"  Updated: {data['updated_at']}")
                        print("-" * 60)
                        print()
                    except json.JSONDecodeError:
                        print(f"Received non-JSON message: {message}")
            
            except asyncio.CancelledError:
                ping_task.cancel()
                raise
    
    except websockets.exceptions.ConnectionClosed:
        print("\n✗ Connection closed by server")
    except ConnectionRefusedError:
        print("\n✗ Could not connect to the service. Is it running?")
        print("\nPlease start the service first:")
        print("  uvicorn app.main:app --host 0.0.0.0 --port 8443 \\")
        print("    --ssl-keyfile certs/server-key.pem \\")
        print("    --ssl-certfile certs/server-cert.pem \\")
        print("    --ssl-ca-certs certs/ca-cert.pem \\")
        print("    --ssl-cert-reqs 2")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✓ Disconnected")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(listen_to_updates())
