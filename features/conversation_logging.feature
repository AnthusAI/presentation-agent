Feature: Conversation Logging and Resuming
  As a user
  I want my conversation history to be saved
  So that I can resume a session later

  Scenario: Log conversation messages
    Given I have a presentation named "logging-test"
    And the agent is active for "logging-test"
    When I type "Hello AI"
    Then a "chat_history.jsonl" file should exist in the presentation
    And the history file should contain "Hello AI"
    And the history file should contain the AI response

  Scenario: Resume previous session
    Given I have a presentation named "resume-test"
    And the presentation contains a history file with a previous message "User: Remember this"
    When I run the load command for "resume-test" with the continue flag
    Then the start_repl function should be called with resume=True

