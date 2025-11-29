Feature: Dynamic Context and Welcome
  As a user
  I want the agent to know the current state of the presentation
  And I want a simple, helpful welcome
  So that I can start working immediately

  Scenario: Welcome message is simple and brand-aligned
    Given I have a presentation named "demo-deck"
    When I execute the load command for "demo-deck"
    Then the output should contain a box in "magenta2" color
    And the REPL output should contain "DeckBot"
    And the REPL output should contain "I can help you make a presentation"
    And the REPL output should NOT contain "Vibe Zone"

  Scenario: Agent receives dynamic context
    Given I have a presentation named "context-deck"
    And the presentation contains a file "slide1.md" with content "# Slide 1"
    When I start the REPL for "context-deck"
    Then the agent system prompt should contain "# Slide 1"
    
    When I create a file "slide2.md" with content "# Slide 2" via the agent
    And I send a message "What is on slide 2?" to the agent
    Then the agent system prompt should contain "# Slide 2"

  Scenario: Initial interaction summarizes existing presentation
    Given I have a presentation named "existing-deck"
    And the presentation contains a file "intro.md" with content "# Introduction"
    When I start the REPL for "existing-deck"
    Then the agent should generate an initial response
    And the initial response should be based on "Analyze the current presentation"
    
  Scenario: Initial interaction for new presentation asks for direction
    Given I have a presentation named "new-empty-deck"
    When I start the REPL for "new-empty-deck"
    Then the agent should generate an initial response

