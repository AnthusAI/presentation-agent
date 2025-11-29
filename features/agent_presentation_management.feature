Feature: Agent Presentation Management
  As an AI agent
  I want to manage presentations directly
  So that I can help the user switch contexts without leaving the chat

  Scenario: List presentations
    Given I have a presentation named "deck-1" created at "2023-01-01T10:00:00"
    And I have a presentation named "deck-2" created at "2023-01-02T10:00:00"
    When the agent uses the "list_presentations" tool
    Then the result should contain "deck-2" before "deck-1"
    And the result should include the creation date

  Scenario: Create a new presentation
    Given the presentation directory is empty
    When the agent uses the "create_presentation" tool with name "new-deck" and description "A new deck"
    Then a new directory "new-deck" should be created
    And the presentation list should contain "new-deck"

  Scenario: Load a presentation
    Given I have a presentation named "context-deck"
    When the agent uses the "load_presentation" tool for "context-deck"
    Then the agent context should be updated to "context-deck"
    And the system prompt should reflect the new presentation

