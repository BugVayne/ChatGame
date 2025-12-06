import asyncio
import websockets
import json
from typing import Set, Dict, Any


class ExternalInterface:
    def __init__(self, game_core, state_monitor):
        self.game_core = game_core
        self.state_monitor = state_monitor
        self.connections: Set[websockets.WebSocketServerProtocol] = set()
        self.event_loop = None
        self.websocket_server = None

    async def handle_websocket(self, websocket):
        """Handle incoming WebSocket connections"""
        self.connections.add(websocket)
        try:
            async for message in websocket:
                await self.process_external_command(message, websocket)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connections.remove(websocket)

    async def process_external_command(self, message, websocket):
        """Process commands from external clients"""
        try:
            command = json.loads(message)
            response = self.handle_command(command)

            if response:
                await websocket.send(json.dumps(response))

            # Send current state after command
            current_state = self.state_monitor.get_current_state()
            await websocket.send(json.dumps({
                "type": "game_state",
                "state": current_state
            }))
        except Exception as e:
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))

    async def broadcast_game_event(self, event):
        """Broadcast game events to all connected clients"""
        if self.connections:
            message = json.dumps(event)
            disconnected = set()
            for ws in self.connections:
                try:
                    await ws.send(message)
                except:
                    disconnected.add(ws)
            self.connections -= disconnected

    def broadcast_event(self, event):
        """Thread-safe event broadcasting"""
        if self.event_loop and self.event_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.broadcast_game_event(event),
                self.event_loop
            )

    def start_websocket_server(self):
        """Start WebSocket server in its own event loop"""

        async def server_main():
            async with websockets.serve(
                    self.handle_websocket, "localhost", 8765
            ) as server:
                self.websocket_server = server
                await asyncio.Future()  # Run forever

        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_until_complete(server_main())

    def handle_command(self, command_data):
        """Handle commands from external systems (called from main thread)"""
        command_type = command_data.get("type")

        if command_type == "game_command":
            result = self.game_core.execute_command(
                command_data.get("command", {})
            )
            return {"type": "command_response", "result": result}

        elif command_type == "query_state":
            state = self.state_monitor.get_current_state()
            return {"type": "game_state", "state": state}

        elif command_type == "trigger_event":
            event_type = command_data.get("event_type")
            return {
                "type": "event_triggered",
                "event": event_type
            }

        elif command_type == "reset_game":
            self.game_core.initialize_world()
            return {
                "type": "game_reset",
                "message": "Game has been reset"
            }

        else:
            return {
                "type": "error",
                "message": "Unknown command type"
            }