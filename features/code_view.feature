Feature: Code View
  As a user
  I want to view the source files of my presentation
  So that I can inspect the code and assets without leaving DeckBot

  Background:
    Given the web UI is running
    And I have a presentation "code-view-test" loaded

  Scenario: View menu contains Code option
    When I click the "View" menu
    Then I should see a "Code" menu item
    And it should have a code icon
    And it should show the current state (checked if active)

  Scenario: Selecting Code from View menu
    Given the sidebar is showing preview
    When I click the "View" menu
    And I select "Code"
    Then the sidebar should switch to show the code view
    And the Code option should be checked in the menu
    And the Preview option should be unchecked in the menu

  Scenario: Code view displays file tree
    When I switch to the code view
    Then I should see a file tree sidebar
    And the file tree should contain "deck.marp.md"
    And the file tree should contain "metadata.json"
    And the file tree should contain "layouts.md"

  Scenario: Code view displays folders
    When I switch to the code view
    Then I should see a folder "images" in the file tree

  Scenario: Clicking a file displays its content
    Given I am in the code view
    When I click on "deck.marp.md" in the file tree
    Then the content area should display the file content
    And the file name header should show "deck.marp.md"

  Scenario: Expanding a folder shows its contents
    Given I am in the code view
    When I click on the "images" folder
    Then the folder should expand
    And I should see files inside the "images" folder

  Scenario: Collapsing a folder hides its contents
    Given I am in the code view
    And the "images" folder is expanded
    When I click on the "images" folder again
    Then the folder should collapse
    And the files inside "images" should be hidden

  Scenario: Toggle button in preview view
    Given I am viewing the preview
    Then I should see a toggle button in the top-right corner
    And the toggle button should have a code icon
    And the toggle button should say "Code"

  Scenario: Toggle button switches to code view
    Given I am viewing the preview
    When I click the toggle button
    Then the sidebar should switch to the code view

  Scenario: Toggle button in code view
    Given I am in the code view
    Then I should see a toggle button in the top-right corner
    And the toggle button should have an eye icon
    And the toggle button should say "Preview"

  Scenario: Toggle button switches to preview view
    Given I am in the code view
    When I click the toggle button
    Then the sidebar should switch to the preview view

  Scenario: Keyboard shortcut for Code view
    Given I am viewing the preview
    When I press "⌘3" or "Ctrl+3"
    Then the sidebar should switch to the code view

  Scenario: Viewing a JSON file
    Given I am in the code view
    When I click on "metadata.json" in the file tree
    Then the content should be displayed with syntax highlighting
    And the content should be formatted as JSON

  Scenario: Viewing an image file
    Given I am in the code view
    And there is an image file in the images folder
    When I click on the image file in the file tree
    Then the image should be displayed as a preview
    And I should not see raw binary data

  Scenario: View state persists across sessions
    Given I am in the code view
    When I refresh the page
    Then the sidebar should still show the code view
    And the "Code" option in View menu should be checked

  Scenario: Default view is Preview not Code
    When I first load the web UI with a presentation
    Then the sidebar should show Preview by default
    And the code view should not be visible

  Scenario: Default file selected initially
    When I switch to the code view
    Then the content area should display the main presentation file
    And the file name header should show "deck.marp.md"

  Scenario: Code view is editable with Monaco editor
    Given I am in the code view
    When I view any file
    Then I should see Monaco editor
    And I should see a save button
    And the content should be editable

