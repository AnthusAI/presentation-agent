Feature: Request Details Display
  As a user
  I want to see the full details of AI requests
  So that I can understand what prompts are being sent to the models

  Background:
    Given a presentation "details-test" exists

  Scenario: Agent Request Details Available
    Given I load the presentation "details-test" via API
    When I send a chat message "Create a slide" via API
    Then agent request details should be emitted
    And the details should include the user message
    And the details should include the system prompt
    And the details should include the model name

  Scenario: Image Request Details Available
    Given I load the presentation "details-test" via API
    When I request image generation for "A robot" via API
    Then image request details should be emitted
    And the details should include the user prompt
    And the details should include the system instructions
    And the details should include the aspect ratio
    And the details should include the resolution

  Scenario: Request Details Collapse/Expand
    Given I have sent a chat message with details
    When I view the message in the UI
    Then I should see a details toggle button
    And the details section should be collapsed by default
    When I click the details toggle
    Then the details section should expand
    And I should see the full system prompt
    And I should see the full user message

  Scenario: Multiple Requests Track Separately
    Given I send multiple chat messages
    Then each message should have its own details toggle
    And expanding one should not affect others




