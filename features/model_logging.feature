Feature: Model Configuration Logging

  Scenario: Log model configuration on startup
    Given I am working on a presentation "LoggingTest"
    And a config file with:
      """
      primary_model: "custom-primary"
      secondary_model: "custom-secondary"
      """
    When the agent is initialized with logging capture
    Then the log output should contain "Primary Model: custom-primary"
    And the log output should contain "Secondary Model: custom-secondary"

