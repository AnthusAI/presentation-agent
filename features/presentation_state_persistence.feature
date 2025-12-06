Feature: Presentation State Persistence
  As a user
  I want DeckBot to remember which presentation I was working on
  So that I can reload the page without losing my context

  @wip
  Scenario: Presentation context is saved when loaded
    # React UI manages state persistence via localStorage
    # Backend state API endpoints need to be implemented
    Given I have a presentation named "my-saved-deck"
    When I load the presentation "my-saved-deck" via the API
    Then the persisted state should indicate "my-saved-deck" is the current presentation

  @wip
  Scenario: Presentation is automatically restored on page reload
    # React UI manages state persistence via localStorage
    # Backend state API endpoints need to be implemented
    Given the persisted state indicates "restored-deck" is the current presentation
    And I have a presentation named "restored-deck"
    When I request the current presentation state
    Then the state response should contain name "restored-deck"

  @wip
  Scenario: State is cleared when no presentation is active
    # React UI manages state persistence via localStorage
    # Backend state API endpoints need to be implemented
    Given I have a persisted presentation state
    When I clear the current presentation state
    Then the persisted state should be empty

  @wip
  Scenario: User closes the presentation via the UI
    # React UI manages state persistence via localStorage
    # Backend state API endpoints need to be implemented
    Given I have a persisted presentation state
    When I request to close the presentation via API
    Then the persisted state should be empty
    And the current service should be unloaded
