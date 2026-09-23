"""
V2 Extensions package for Personal Finance & Wealth Simulator
Contains scenario comparison and goal planning modules.
"""

from .scenario_comparison import create_scenario_inputs, run_scenario_comparison
from .goal_planning import calculate_goal_requirements, validate_goal_inputs
from .shared_utils import (
    validate_and_clamp_scenario_inputs,
    validate_goal_inputs as validate_goal_inputs_shared,
    binary_search_contribution
)

__all__ = [
    'create_scenario_inputs',
    'run_scenario_comparison',
    'calculate_goal_requirements',
    'validate_goal_inputs',
    'validate_and_clamp_scenario_inputs',
    'validate_goal_inputs_shared',
    'binary_search_contribution'
]