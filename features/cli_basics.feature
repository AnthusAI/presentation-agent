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

  Scenario: Start Web UI with Default Port
    When I run the command "--web"
    Then the web server should start on port 5555
    And the output should contain "Starting Web UI on http://localhost:5555"

  Scenario: Start Web UI with Custom Port
    When I run the command "--web --port 8080"
    Then the web server should start on port 8080
    And the output should contain "Starting Web UI on http://localhost:8080"

  Scenario: Start Web UI - Flask Missing
    Given Flask is not installed
    When I run the command "--web"
    Then the output should contain "Error: Flask not installed"
