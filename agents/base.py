"""Base agent interface and shared blackboard context for multi-agent spatial coordination."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional
import pandas as pd


@dataclass
class AgentContext:
    """Shared blackboard context passed between autonomous spatial agents."""

    raw_data: Optional[pd.DataFrame] = None
    normalized_df: Optional[pd.DataFrame] = None
    num_dark_stores: int = 3
    healthcare_deserts: Optional[pd.DataFrame] = None
    dark_stores: List[Dict[str, Any]] = field(default_factory=list)
    emergency_hub: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    agent_trace: List[Dict[str, Any]] = field(default_factory=list)
    policy_report: str = ""
    spatial_bounds: Dict[str, float] = field(default_factory=dict)

    def add_trace(
        self,
        agent: str,
        action: str,
        observation: str,
        status: str = "completed",
    ) -> Dict[str, Any]:
        """Appends an execution step to the dynamic agent trace array."""
        step = {
            "agent": agent,
            "action": action,
            "observation": observation,
            "status": status,
            "timestamp": time.time(),
        }
        self.agent_trace.append(step)
        return step


class BaseAgent(ABC):
    """Abstract base class for all autonomous spatial agents."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(self, context: AgentContext) -> Dict[str, Any]:
        """Executes the agent's task against the blackboard context.

        Args:
            context: Shared AgentContext containing current multi-agent state.

        Returns:
            Dict containing the agent's output artifacts and summary findings.
        """
        pass
