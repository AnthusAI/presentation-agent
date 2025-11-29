Feature: End-to-End Workflows
  As a user
  I want to complete common tasks smoothly
  So that I can rely on DeckBot for my work

  Scenario: Create Presentation, Chat, Generate Image
    When I create a presentation named "workflow-deck" via the UI
    Then the presentation "workflow-deck" should exist
    When I send a chat message "Let's add a slide" via API
    Then the response status code should be 200
    When I request image generation for "A chart" via API
    Then the response status code should be 200
    And the response should contain "started"

  Scenario: Resume Workflow
    Given the presentation "resume-flow" has history
    When I load the presentation "resume-flow" via API
    Then the response should contain "Mock user message"
    When I send a chat message "Continue" via API
    Then the response should contain "processing"

