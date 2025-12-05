Feature: Automatic View Switching
  As a user
  I want the UI to automatically switch to the appropriate view
  So that I can see the results of my actions without manual navigation

  Background:
    Given the web UI is running

  Scenario: New presentation opens in Preview mode
    When I create a new presentation "auto-test"
    Then the sidebar should show the Preview view
    And the Layouts view should not be visible
    And the "Preview" menu item should be checked
    And the "Layouts" menu item should not be checked

  Scenario: Creating presentation switches from Layouts to Preview
    Given I am viewing the Layouts view
    When I create a new presentation "switch-test"
    Then the sidebar should automatically switch to Preview
    And the preview iframe should load the presentation

  Scenario: Selecting a layout creates slide and shows preview
    Given I have a presentation "layout-switch-test" loaded
    And I am viewing the Layouts view
    When I click "New Slide" on the "two-column" layout
    Then the system should create the slide
    And the sidebar should automatically switch to Preview
    And I should see the new slide in the preview

  Scenario: Agent makes presentation changes and preview updates
    Given I have a presentation "update-test" loaded
    And I am viewing the Layouts view
    When the agent modifies the presentation
    Then the sidebar should automatically switch to Preview
    And the preview should reload to show the changes

  Scenario: Compiling presentation switches to Preview
    Given I have a presentation "compile-test" loaded
    And I am viewing the Layouts view
    When the presentation is compiled
    Then the sidebar should automatically switch to Preview
    And the compiled presentation should be visible

  Scenario: View preference persists but respects automatic switching
    Given my saved view preference is "Layouts"
    When I load the web UI with no presentation
    Then the sidebar should show Layouts (respecting preference)
    When I create a new presentation
    Then the sidebar should switch to Preview (overriding preference for this action)

  Scenario: Manual view switching is preserved until presentation changes
    Given I have a presentation loaded in Preview
    When I manually switch to Layouts view
    Then the sidebar should show Layouts
    And manual switching should be respected
    When I create a new slide using a layout
    Then the sidebar should switch back to Preview

  Scenario: presentation_updated event triggers preview switch
    Given I am viewing Layouts
    When a "presentation_updated" SSE event is received
    Then the sidebar should switch to Preview
    And the preview should reload

  Scenario: Opening existing presentation shows Preview
    Given there are existing presentations
    When I open presentation "existing-deck"
    Then the sidebar should show Preview
    And the presentation should be loaded in the iframe

  Scenario: First-time user sees Preview by default
    Given I am a new user with no saved preferences
    When I load the web UI
    Then the sidebar should show Preview view by default
    And no layouts should be visible




