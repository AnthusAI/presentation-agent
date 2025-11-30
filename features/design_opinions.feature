Feature: Design Opinions
  As a user who cares about aesthetics
  I want the agent to use Lucide icons instead of emojis
  So that my presentations look professional and consistent

  Scenario: Agent prefers Lucide icons over emojis
    Given a new presentation
    When I ask "Create a slide about great ideas with an icon"
    Then the agent should generate a slide
    And the slide should contain a Lucide icon image link
    And the slide should not contain emojis

  Scenario: Agent uses Lucide icons for specific concepts
    Given a new presentation
    When I ask "Add a slide about 'Warning Signs' with appropriate iconography"
    Then the slide should contain a link to "alert-triangle.svg" or "triangle-alert.svg"

