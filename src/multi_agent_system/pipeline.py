"""Pipeline for chaining multiple agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from ..core import AgentResponse, Message


@dataclass
class PipelineStage:
    """A single stage in a pipeline."""
    name: str
    agent_handler: Callable[[Any], AgentResponse]
    input_map: Dict[str, str] = field(default_factory=dict)
    output_key: str = "result"


class Pipeline:
    """Pipeline for chaining multiple agent calls."""
    
    def __init__(self, name: str) -> None:
        self.name = name
        self.stages: List[PipelineStage] = []
    
    def add_stage(
        self,
        name: str,
        handler: Callable[[Any], AgentResponse],
        input_map: Dict[str, str] | None = None,
        output_key: str = "result",
    ) -> "Pipeline":
        stage = PipelineStage(
            name=name,
            agent_handler=handler,
            input_map=input_map or {},
            output_key=output_key,
        )
        self.stages.append(stage)
        return self
    
    def execute(self, initial_input: dict) -> Dict[str, Any]:
        """Execute the pipeline."""
        context = initial_input.copy()
        
        for stage in self.stages:
            # Map inputs from context
            agent_input = {}
            for target_key, source_key in stage.input_map.items():
                if source_key in context:
                    agent_input[target_key] = context[source_key]
                else:
                    agent_input[target_key] = source_key  # Use literal
            
            # Execute agent
            message = Message(
                task_type=stage.name,
                content=agent_input,
            )
            response = stage.agent_handler(message)
            
            # Store output in context
            if response.success:
                context[stage.output_key] = response.data
            else:
                context[f"{stage.output_key}_error"] = response.error
                return context
        
        return context


# Pipeline templates
def create_search_pipeline() -> Pipeline:
    """Create a standard search pipeline."""
    from ..agents import EntityExtractionAgent, IntentClassificationAgent, MatchingAgent
    
    pipeline = Pipeline("search")
    
    def extract(text: str) -> AgentResponse:
        agent = EntityExtractionAgent()
        return agent.handle(Message(task_type="extract_entities", content={"text": text}))
    
    def classify(text: str) -> AgentResponse:
        agent = IntentClassificationAgent()
        return agent.handle(Message(task_type="classify_intent", content={"text": text}))
    
    def match(query: dict) -> AgentResponse:
        agent = MatchingAgent()
        return agent.handle(Message(task_type="match", content=query))
    
    pipeline.add_stage("extract", extract, {"text": "query"}, "entities")
    pipeline.add_stage("classify", classify, {"text": "query"}, "intent")
    pipeline.add_stage("match", match, {"query": "query"}, "results")
    
    return pipeline
