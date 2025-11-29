Feature: Marp Preview Integration
  As a user
  I want to preview my presentation
  So that I can see how it looks

  Scenario: Start preview server
    Given I have a presentation named "my-deck" with description "For preview"
    When I run the preview command for "my-deck"
    Then the Marp CLI should be invoked with server mode for the presentation directory

