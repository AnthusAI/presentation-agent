Feature: Automatic Model Fallback and Configuration

  Background:
    Given I am working on a presentation "FallbackTest"

  Scenario: Configure primary and secondary models via config file
    Given a config file with:
      """
      primary_model: "custom-primary"
      secondary_model: "custom-secondary"
      """
    When the agent is initialized
    Then it should use "custom-primary" as the primary model

  Scenario: Fallback to secondary model on Resource Exhausted error
    Given the agent is configured with:
      | setting         | value                  |
      | primary_model   | gemini-3-pro           |
      | secondary_model | gemini-2.0-flash-exp   |
    And the primary model is active
    And the AI will return a "429 RESOURCE_EXHAUSTED" error
    When I send a message "Hello"
    Then the agent should switch to "gemini-2.0-flash-exp"
    And the request should be retried successfully

  Scenario: Default configuration
    Given no specific model configuration exists
    When the agent is initialized
    Then it should use "gemini-3-pro-preview" as the primary model
    And "gemini-2.0-flash-exp" as the secondary model

