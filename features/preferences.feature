Feature: User Preferences and Customization
  As a DeckBot user
  I want to customize my workspace (theme, colors)
  So that the tool feels personal and matches my workflow

  Scenario: First-time user gets sensible defaults
    Given I am using DeckBot for the first time
    When I check my preferences
    Then the stored theme preference should be "system"
    And the stored color theme preference should be "miami"
    And a ".deckbot.yaml" file should exist

  Scenario: User changes their preferred theme
    Given I have DeckBot configured
    When I set my theme preference to "dark"
    Then my ".deckbot.yaml" should contain "theme: dark"
    And subsequent sessions should use the dark theme

  Scenario: User switches color themes to match their brand
    Given I'm working on a corporate presentation
    When I change my color theme to "midwest"
    Then my preference should persist across sessions
    And the web UI should reflect the new colors

  Scenario: User resets preferences to defaults
    Given I have customized preferences
    When I delete my theme preference
    Then it should revert to "system"
    And my other preferences should remain unchanged

  Scenario: Preferences survive invalid YAML errors
    Given my ".deckbot.yaml" becomes corrupted
    When I try to read preferences
    Then I should get default values
    And the system should not crash

