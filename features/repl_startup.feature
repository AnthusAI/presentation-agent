Feature: REPL Startup Logic
  As a user
  I want the REPL startup to be context-aware
  So that I don't get repetitive initial prompts when resuming

  Scenario: Skip initial analysis on resume
    Given I have a presentation named "resume-deck"
    When I start the REPL for "resume-deck" with resume=True
    Then the agent should NOT generate an initial response
    And the output should contain "Resuming previous session..."

  Scenario: Trigger initial analysis on fresh start
    Given I have a presentation named "fresh-deck"
    When I start the REPL for "fresh-deck" with resume=False
    Then the agent should generate an initial response

  Scenario: Show last agent message on resume
    Given I have a presentation named "resume-msg-deck"
    And the presentation contains a chat history with the last agent message "Ready for next steps?"
    When I start the REPL for "resume-msg-deck" with resume=True
    Then the output should contain "Ready for next steps?"
    And the output should NOT contain "I can help you make a presentation"
