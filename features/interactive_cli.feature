Feature: Interactive CLI Entry
  As a user
  I want to start the tool without arguments
  So that I can select a presentation interactively

  Scenario: Start without arguments and select existing presentation
    Given I have a presentation named "deck-A"
    And I have a presentation named "deck-B"
    When I run the CLI without arguments and select "deck-A"
    Then the REPL should start with context "deck-A"

  Scenario: Start without arguments and create new
    Given the presentation directory is empty
    When I run the CLI without arguments and choose to create "new-deck"
    Then a new directory "new-deck" should be created
    And the REPL should start with context "new-deck"
    And the REPL output should NOT contain "Analyzing presentation..."

