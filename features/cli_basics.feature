Feature: CLI Core and Presentation Management
  As a user
  I want to manage my presentations through a CLI
  So that I can keep them organized and vibe code them

  Scenario: Create a new presentation
    Given the presentation directory is empty
    When I run the command "create my-new-deck --description 'A demo deck'"
    Then a new directory "my-new-deck" should be created
    And the presentation list should contain "my-new-deck"
    And the description for "my-new-deck" should be "A demo deck"

  Scenario: List presentations
    Given I have a presentation named "deck-1" with description "First deck"
    And I have a presentation named "deck-2" with description "Second deck"
    When I run the command "list"
    Then the output should contain "deck-1"
    And the output should contain "First deck"
    And the output should contain "deck-2"
    And the output should contain "Second deck"

