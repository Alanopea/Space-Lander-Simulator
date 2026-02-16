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
        # NOTE: Time is already updated in Simulator.step() before this is called
        # Do NOT call update_time() here as it would double-increment
        
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
            # Store command with its issue timestamp
            if engine_index not in self.throttle_history:
                self.throttle_history[engine_index] = deque()
            
            # Add new command with its issue time
            self.throttle_history[engine_index].append((self.time, desired_throttle))
            
            # Keep only recent commands (cleanup very old ones)
            cutoff_time = self.time - self.response_lag_delay - 1.0  # Some buffer
            while len(self.throttle_history[engine_index]) > 0:
                oldest_time, _ = self.throttle_history[engine_index][0]
                if oldest_time < cutoff_time:
                    self.throttle_history[engine_index].popleft()
                else:
                    break
            
            # Find the most recent command whose delay has been satisfied
            actual_throttle = 0.0  # Default: no thrust during lag
            
            # Iterate through commands from oldest to newest
            for cmd_issue_time, cmd_throttle in list(self.throttle_history[engine_index]):
                time_since_issue = self.time - cmd_issue_time
                if time_since_issue >= self.response_lag_delay:
                    # This command's delay has passed - it's a candidate
                    # Keep updating to the most recent one
                    actual_throttle = cmd_throttle
                # If we haven't reached the delay yet for a command, stop checking newer ones
                # (they definitely won't have their delays satisfied either)
            
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

