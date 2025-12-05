Feature: Gemini Model Initialization
  As a developer
  I want Gemini to initialize correctly with a valid API key
  So that the agent can function properly

  Scenario: Agent initializes with valid GOOGLE_API_KEY
    Given the GOOGLE_API_KEY environment variable is set
    And only GOOGLE_API_KEY is used (not GEMINI_API_KEY)
    When I create an agent
    Then the agent should initialize successfully
    And the model should use a valid Gemini model name

  Scenario: Agent fails gracefully without API key
    Given the GOOGLE_API_KEY environment variable is not set
    When I create an agent
    Then the agent should warn about missing API key
    And the agent should not crash





