from features.steps.cli_steps import temporary_environment
from behave import use_fixture

def before_scenario(context, scenario):
    use_fixture(temporary_environment, context)

