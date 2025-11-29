Feature: AI Assistant and REPL
  As a user
  I want to have an interactive conversation with an AI assistant
  So that I can build my presentation with help

  Scenario: Load a presentation and start REPL
    Given I have a presentation named "my-deck" with description "Context deck"
    When I run the load command for "my-deck"
    Then the REPL should start with context "my-deck"
    And the system prompt should contain "Context deck"

  Scenario: Chat with the assistant
    Given the REPL is running for "my-deck"
    When I type "Help me outline the deck"
    Then the assistant should respond using the Google Gen AI model
    And the conversation history should be updated

