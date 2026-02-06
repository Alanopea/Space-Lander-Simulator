# This class manages available emergency scenarios for simulation testing.

class EmergencyScenarioManager:
    def __init__(self):
        # Map scenario names to their configuration
        self.scenarios = {
            "None": {
                "type": "none",
                "params": {}
            },
            "One Engine Failure": {
                "type": "engine_failure",
                "params": {"count": 1}
            },
            "Two Engine Failure": {
                "type": "engine_failure",
                "params": {"count": 2}
            },
            "One Engine Stuck at 100%": {
                "type": "engine_stuck",
                "params": {"throttle": 1.0}
            },
            "Response Lag: Mild (0.2s)": {
                "type": "response_lag",
                "params": {"delay": 0.2}
            },
            "Response Lag: Medium (0.5s)": {
                "type": "response_lag",
                "params": {"delay": 0.5}
            },
            "Response Lag: Severe (1.0s)": {
                "type": "response_lag",
                "params": {"delay": 1.0}
            }
        }

    def list_scenarios(self):
        """Get list of all available scenario names."""
        return list(self.scenarios.keys())

    def get_scenario_config(self, name):
        """Get scenario configuration for a given name."""
        return self.scenarios.get(name)

    def get_scenario_type(self, name):
        """Get scenario type for a given name."""
        config = self.scenarios.get(name)
        if config:
            return config["type"]
        return None

