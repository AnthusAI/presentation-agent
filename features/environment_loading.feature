Feature: Environment Variable Loading
  As a developer
  I want environment variables to load from .env file
  So that configuration works consistently in both CLI and web modes

  Scenario: GOOGLE_API_KEY loads from .env in CLI mode
    Given the environment variable "GOOGLE_API_KEY" is set in .env
    When I import the vibe_presentation package
    Then the environment variable "GOOGLE_API_KEY" should be accessible

  Scenario: GOOGLE_API_KEY loads from .env in web mode
    Given the environment variable "GOOGLE_API_KEY" is set in .env
    When I import the webapp module
    Then the environment variable "GOOGLE_API_KEY" should be accessible

  Scenario: Agent uses GOOGLE_API_KEY (not legacy key)
    Given the environment variable "GOOGLE_API_KEY" is set
    When I create an Agent instance
    Then the agent should have the API key configured
    And the agent should not reference any legacy API key variables






