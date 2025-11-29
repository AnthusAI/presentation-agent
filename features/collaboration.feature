Feature: Agent Collaboration
  As a user
  I want the agent to act as a developer
  So that my changes are reflected in the code and preview

  Scenario: Agent refactors a slide based on feedback
    Given I have a slide "intro.md" with content "# Old Title"
    When I tell the agent "Change the title to 'New Title'"
    And the agent decides to update "intro.md" with content "# New Title"
    Then the presentation file "intro.md" should contain "# New Title"
    And the preview should trigger a reload

