Feature: Open Presentation Tool
  As a user
  I want to open the presentation folder
  So that I can see the files and edit them manually if needed

  Scenario: Open presentation folder
    Given I have a presentation named "open-deck"
    When the agent uses the "open_presentation_folder" tool
    Then the result should indicate the folder was opened

