Feature: Template Design Opinions
  As a user
  I want to define design opinions in my template
  So that the agent follows my specific aesthetic preferences per presentation

  Scenario: Template defines icon preference
    Given a template "LucideTheme" exists with design opinions
      | key   | value  |
      | icons | lucide |
    And a presentation uses the "LucideTheme" template
    When I initialize the agent
    Then the system prompt should contain "Prefer using Lucide icons instead of emojis"
    And the system prompt should contain "https://cdn.jsdelivr.net/npm/lucide-static"

  Scenario: Template defines no specific design opinions
    Given a template "BlankTheme" exists without design opinions
    And a presentation uses the "BlankTheme" template
    When I initialize the agent
    Then the system prompt should not contain "Prefer using Lucide icons"
