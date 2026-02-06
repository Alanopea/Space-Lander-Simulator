# Emergency scenario handler that applies various failure modes during simulation.

import numpy as np
from collections import deque


class EmergencyScenarioHandler:
    """Handles emergency scenarios like engine failures, stuck engines, and response lag."""
    
    def __init__(self, lander, scenario_config=None):
        """
        Initialize emergency scenario handler.
        
        Args:
            lander: Lander instance
            scenario_config: Dict with 'type' and 'params' keys, or None for no scenario
        """
        self.lander = lander
        self.scenario_config = scenario_config or {"type": "none", "params": {}}
        self.scenario_type = self.scenario_config.get("type", "none")
        self.params = self.scenario_config.get("params", {})
        
        # State for response lag scenario
        self.response_lag_delay = self.params.get("delay", 0.0) if self.scenario_type == "response_lag" else 0.0
        self.throttle_history = {}  # Store throttle commands with timestamps
        self.time = 0.0
        
        # Apply initial scenario setup
        self._apply_initial_scenario()
    
    def _apply_initial_scenario(self):
        """Apply scenario-specific initial setup."""
        if self.scenario_type == "engine_failure":
            # Disable engines (count specified in params)
            count = self.params.get("count", 1)
            # Disable first N engines
            for i in range(min(count, len(self.lander.engines))):
                self.lander.set_engine_enabled(i, False)
        
        elif self.scenario_type == "engine_stuck":
            # One engine will be stuck at specified throttle
            # We'll handle this in apply_scenario_effects
            pass
        
        elif self.scenario_type == "response_lag":
            # Initialize throttle history for all engines
            for i in range(len(self.lander.engines)):
                self.throttle_history[i] = deque()
    
    def update_time(self, dt):
        """Update internal time tracking for lag scenarios."""
        self.time += dt
    
    def apply_scenario_effects(self, dt):
        """
        Apply scenario effects each simulation step.
        
        Args:
            dt: Time step (s)
        """
        self.update_time(dt)
        
        if self.scenario_type == "engine_stuck":
            # Keep one engine at 100% throttle
            throttle = self.params.get("throttle", 1.0)
            if len(self.lander.engines) > 0:
                # Stuck engine is the first one
                self.lander.engines[0].throttle = throttle
                self.lander.engines[0].enabled = True
        
        elif self.scenario_type == "response_lag":
            # Apply delayed throttle commands
            self._apply_delayed_throttles(dt)
    
    def _apply_delayed_throttles(self, dt):
        """Apply throttles with delay for response lag scenario."""
        # This will be called after thrust allocation to delay throttle updates
        # The actual delay is handled by modifying throttle updates
        pass
    
    def modify_throttle_command(self, engine_index, desired_throttle):
        """
        Modify throttle command based on scenario (for response lag).
        
        Args:
            engine_index: Index of engine
            desired_throttle: Desired throttle value (0-1)
            
        Returns:
            Actual throttle to apply (may be delayed)
        """
        if self.scenario_type == "response_lag" and self.response_lag_delay > 0:
            # Store command with timestamp
            if engine_index not in self.throttle_history:
                self.throttle_history[engine_index] = deque()
            
            # Add new command with future timestamp
            self.throttle_history[engine_index].append((self.time + self.response_lag_delay, desired_throttle))
            
            # Keep only recent commands (cleanup old ones)
            while len(self.throttle_history[engine_index]) > 100:
                self.throttle_history[engine_index].popleft()
            
            # Find the throttle that should be applied now
            # Look for the most recent command that has expired
            current_throttle = self.lander.engines[engine_index].throttle  # Default to current
            actual_throttle = current_throttle
            
            # Process commands in order, applying the most recent expired one
            expired_commands = []
            for cmd_time, cmd_throttle in list(self.throttle_history[engine_index]):
                if cmd_time <= self.time:
                    expired_commands.append((cmd_time, cmd_throttle))
            
            if expired_commands:
                # Use the most recent expired command
                _, actual_throttle = max(expired_commands, key=lambda x: x[0])
            
            # If this is the very first command and delay hasn't passed, start at 0
            if self.time < self.response_lag_delay and len(self.throttle_history[engine_index]) == 1:
                actual_throttle = 0.0
            
            return actual_throttle
        
        # No modification for other scenarios
        return desired_throttle
    
    def reset(self):
        """Reset scenario handler state."""
        self.time = 0.0
        self.throttle_history = {}
        
        # Re-enable all engines (they may have been disabled)
        for i in range(len(self.lander.engines)):
            self.lander.set_engine_enabled(i, True)
        
        # Re-apply initial scenario
        self._apply_initial_scenario()

