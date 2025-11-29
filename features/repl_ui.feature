Feature: REPL UI and Commands
  As a user
  I want to control the REPL session and see clear status
  So that I can work efficiently and exit cleanly

  Scenario: Clean exit with slash commands
    Given I have a presentation named "test-deck"
    When I execute the load command for "test-deck" and type "/exit"
    Then the REPL should exit cleanly
    
    When I execute the load command for "test-deck" and type "/quit"
    Then the REPL should exit cleanly
    
    When I execute the load command for "test-deck" and type "/q"
    Then the REPL should exit cleanly

  Scenario: Intro message
    Given I have a presentation named "test-deck"
    When I execute the load command for "test-deck"
    Then the output should contain a box in "magenta2" color
    And the REPL output should contain "DeckBot"
    And the REPL output should contain "Working on:"
    And the REPL output should contain "test-deck"
    And the REPL output should contain "I can help you make a presentation"

