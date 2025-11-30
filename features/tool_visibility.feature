Feature: Real-Time Tool Visibility
  As a user
  I want to see what tools the agent is using
  So that I understand what is happening in the background

  Scenario: User sees tool usage in web UI
    Given I'm chatting with the real agent in web UI
    When the agent calls the "write_file" tool with argument "intro.md"
    Then the tool event listener should receive a "tool_start" event
    And the tool event listener should receive a "tool_end" event
    And the event data should contain "write_file"

