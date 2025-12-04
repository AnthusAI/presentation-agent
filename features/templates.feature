Feature: Presentation Templates
  As a user
  I want to create presentations from templates
  So that I can ensure consistent branding and structure

  Background:
    Given the template directory exists

  Scenario: List available templates
    Given there is a template "Corporate" with description "Professional blue theme"
    When I list templates via CLI
    Then the output should contain "Corporate"
    And the output should contain "Professional blue theme"

  Scenario: Create presentation from template via CLI
    Given there is a template "Startup" with content "# Startup Pitch"
    When I run the command "create my-startup-deck --template Startup"
    Then a presentation "my-startup-deck" should exist
    And the file "my-startup-deck/deck.marp.md" should contain "# Startup Pitch"

  Scenario: Create presentation from template via Agent
    Given a basic template "Light" exists
    And the agent is active for a new presentation
    When the agent creates a presentation "new-deck" from template "Light"
    Then a presentation "new-deck" should exist

  Scenario: Agent receives branding instructions from template
    Given a template "BrandX" exists with instruction "Use the color hex #FF00FF for emphasis"
    And I create a presentation "brand-deck" from template "BrandX"
    When I load the presentation "brand-deck"
    Then the agent system prompt should contain "Use the color hex #FF00FF for emphasis"

  Scenario: Preview a template
    Given a basic template "DarkTheme" exists
    When the agent previews the template "DarkTheme"
    Then the template "DarkTheme" should be compiled to HTML

  Scenario: Create presentation from template with images
    Given a template "Branded" exists with image "logo.png"
    When I run the command "create brand-test --template Branded"
    Then a presentation "brand-test" should exist
    And the file "brand-test/images/logo.png" should exist
    And the file "brand-test/deck.marp.md" should contain "![logo](images/logo.png)"

  Scenario: Delete a template
    Given a basic template "OldTemplate" exists
    When I delete the template "OldTemplate"
    Then the template "OldTemplate" should not exist
