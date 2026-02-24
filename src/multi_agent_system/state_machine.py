"""State machine for workflow management."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class State(str, Enum):
    """Possible states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StateMachine:
    """Simple state machine."""
    
    def __init__(self, initial_state: State = State.PENDING) -> None:
        self._state = initial_state
        self._history: List[State] = [initial_state]
        self._transitions: Dict[State, Dict[State, Callable]] = {}
    
    @property
    def state(self) -> State:
        return self._state
    
    def add_transition(self, from_state: State, to_state: State, handler: Optional[Callable] = None) -> None:
        if from_state not in self._transitions:
            self._transitions[from_state] = {}
        self._transitions[from_state][to_state] = handler
    
    def can_transition(self, to_state: State) -> bool:
        if self._state not in self._transitions:
            return False
        return to_state in self._transitions[self._state]
    
    def transition(self, to_state: State) -> bool:
        if not self.can_transition(to_state):
            return False
        
        handler = self._transitions[self._state].get(to_state)
        if handler:
            handler()
        
        self._state = to_state
        self._history.append(to_state)
        return True
    
    def reset(self, state: State = State.PENDING) -> None:
        self._state = state
        self._history = [state]
