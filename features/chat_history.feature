Feature: Chat History and Resumption
  As a user
  I want my chat history to be saved
  So that I can resume a conversation after restarting the tool

  Scenario: Chat logs are saved
    Given I have a presentation named "history-test"
    And I run the load command for "history-test"
    When I type "Hello, history!"
    Then the message "Hello, history!" should be logged to "history-test/chat_history.jsonl"

  Scenario: Resuming a session
    Given I have a presentation named "history-test"
    And the presentation contains a chat history with a message "Previous context"
    When I run the load command for "history-test" with the --continue flag
    Then the conversation history should be loaded into the agent

