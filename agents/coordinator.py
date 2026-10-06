"""Spatial multi-agent coordinator for orchestrating sequential agent pipelines and blackboard state."""

from typing import List, Optional
import pandas as pd

from agents.base import AgentContext, BaseAgent
from agents.emergency_dispatch_agent import EmergencyDispatchAgent
from agents.perception_agent import PerceptionAgent
from agents.policy_synthesis_agent import PolicySynthesisAgent
from agents.spatial_optimization_agent import SpatialOptimizationAgent


class SpatialMultiAgentCoordinator:
    """Orchestrates autonomous agents sequentially, updating blackboard state and collating traces."""

    def __init__(
        self,
        perception_agent: Optional[BaseAgent] = None,
        spatial_agent: Optional[BaseAgent] = None,
        emergency_agent: Optional[BaseAgent] = None,
        policy_agent: Optional[BaseAgent] = None,
    ):
        self.perception_agent = perception_agent or PerceptionAgent()
        self.spatial_agent = spatial_agent or SpatialOptimizationAgent()
        self.emergency_agent = emergency_agent or EmergencyDispatchAgent()
        self.policy_agent = policy_agent or PolicySynthesisAgent()

        self.pipeline: List[BaseAgent] = [
            self.perception_agent,
            self.spatial_agent,
            self.emergency_agent,
            self.policy_agent,
        ]

    async def run(
        self,
        raw_data: pd.DataFrame,
        num_dark_stores: int = 3,
    ) -> AgentContext:
        """Executes the complete spatial multi-agent pipeline.

        Args:
            raw_data: Input pandas DataFrame with ward features and coordinates.
            num_dark_stores: Number of dark stores / micro-fulfillment hubs requested.

        Returns:
            AgentContext: Fully populated blackboard context containing metrics,
                         dark stores, emergency hub, dynamic traces, and report.
        """
        context = AgentContext(
            raw_data=raw_data,
            num_dark_stores=num_dark_stores,
        )

        for agent in self.pipeline:
            await agent.execute(context)

        return context
