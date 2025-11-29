Feature: Real-time Updates via SSE
  As a user
  I want to see immediate updates in the web interface
  So that I don't have to refresh the page to see progress

  Scenario: User sees agent thinking indicator
    Given I'm chatting with the agent in web UI
    When I send a message
    Then I should receive a "thinking_start" event
    And when the response arrives, a "thinking_end" event

  Scenario: User watches images generate one by one
    Given I requested image generation
    Then I should receive "image_progress" events
    And finally an "images_ready" event with all paths

  Scenario: User sees preview update after compilation
    Given I asked the agent to add a slide
    When the agent calls compile_presentation
    Then I should receive a "presentation_updated" event

  Scenario: Multiple users can connect to SSE simultaneously
    Given two browser tabs are open
    When I send a message in tab 1
    Then both tabs should receive the events

