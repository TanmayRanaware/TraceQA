"""
Base Agent class for TraceQ AI Agents
"""
import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import json

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class MessageType(Enum):
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    HEARTBEAT = "heartbeat"

class AgentMessage:
    """Message structure for agent communication"""
    def __init__(self, 
                 message_type: MessageType,
                 sender: str,
                 receiver: str,
                 content: Dict[str, Any],
                 message_id: str = None,
                 correlation_id: str = None):
        self.message_id = message_id or str(uuid.uuid4())
        self.correlation_id = correlation_id
        self.message_type = message_type
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "message_type": self.message_type.value,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "timestamp": self.timestamp
        }

class BaseAgent(ABC):
    """Base class for all AI Agents in TraceQ"""
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.status = AgentStatus.IDLE
        self.message_queue = asyncio.Queue()
        self.message_handlers = {}
        self.running = False
        self.tasks = {}
        
        # Register default message handlers
        self.register_handler(MessageType.TASK_REQUEST, self._handle_task_request)
        self.register_handler(MessageType.STATUS_UPDATE, self._handle_status_update)
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register a message handler for a specific message type"""
        self.message_handlers[message_type] = handler
    
    async def start(self):
        """Start the agent"""
        self.running = True
        self.status = AgentStatus.IDLE
        logger.info(f"Agent {self.agent_name} started")
        
        # Start message processing loop
        asyncio.create_task(self._message_loop())
        
        # Start heartbeat
        asyncio.create_task(self._heartbeat_loop())
    
    async def stop(self):
        """Stop the agent"""
        self.running = False
        self.status = AgentStatus.OFFLINE
        logger.info(f"Agent {self.agent_name} stopped")
    
    async def _message_loop(self):
        """Main message processing loop"""
        while self.running:
            try:
                # Wait for messages with timeout
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self._process_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing message in {self.agent_name}: {e}")
    
    async def _process_message(self, message: AgentMessage):
        """Process a received message"""
        try:
            handler = self.message_handlers.get(message.message_type)
            if handler:
                await handler(message)
            else:
                logger.warning(f"No handler for message type {message.message_type} in {self.agent_name}")
        except Exception as e:
            logger.error(f"Error handling message in {self.agent_name}: {e}")
            await self._send_error_response(message, str(e))
    
    async def send_message(self, message: AgentMessage):
        """Send a message to another agent"""
        # In a real implementation, this would use a message broker
        # For now, we'll simulate direct communication
        if hasattr(self, 'agent_registry'):
            target_agent = self.agent_registry.get(message.receiver)
            if target_agent:
                await target_agent.message_queue.put(message)
            else:
                logger.error(f"Target agent {message.receiver} not found")
    
    async def _handle_task_request(self, message: AgentMessage):
        """Handle task request messages"""
        try:
            self.status = AgentStatus.BUSY
            task_id = message.content.get("task_id")
            task_type = message.content.get("task_type")
            task_data = message.content.get("task_data", {})
            
            logger.info(f"Agent {self.agent_name} received task: {task_type}")
            
            # Execute the task
            result = await self.execute_task(task_type, task_data)
            
            # Send response
            response = AgentMessage(
                message_type=MessageType.TASK_RESPONSE,
                sender=self.agent_id,
                receiver=message.sender,
                content={
                    "task_id": task_id,
                    "task_type": task_type,
                    "result": result,
                    "status": "completed"
                },
                correlation_id=message.message_id
            )
            
            await self.send_message(response)
            
        except Exception as e:
            logger.error(f"Error executing task in {self.agent_name}: {e}")
            await self._send_error_response(message, str(e))
        finally:
            self.status = AgentStatus.IDLE
    
    async def _handle_status_update(self, message: AgentMessage):
        """Handle status update messages"""
        logger.info(f"Agent {self.agent_name} received status update from {message.sender}")
    
    async def _handle_heartbeat(self, message: AgentMessage):
        """Handle heartbeat messages"""
        logger.debug(f"Agent {self.agent_name} received heartbeat from {message.sender}")
    
    async def _send_error_response(self, original_message: AgentMessage, error: str):
        """Send error response"""
        error_response = AgentMessage(
            message_type=MessageType.ERROR,
            sender=self.agent_id,
            receiver=original_message.sender,
            content={
                "error": error,
                "original_message_id": original_message.message_id
            },
            correlation_id=original_message.message_id
        )
        await self.send_message(error_response)
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                if self.running:
                    heartbeat = AgentMessage(
                        message_type=MessageType.HEARTBEAT,
                        sender=self.agent_id,
                        receiver="orchestrator",
                        content={"status": self.status.value}
                    )
                    await self.send_message(heartbeat)
            except Exception as e:
                logger.error(f"Error sending heartbeat from {self.agent_name}: {e}")
    
    @abstractmethod
    async def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task - to be implemented by subclasses"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "running": self.running,
            "active_tasks": len(self.tasks)
        }
