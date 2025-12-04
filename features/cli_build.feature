Feature: Compile Presentation via CLI

  As a user
  I want to compile my presentation into a static file (PDF, HTML, PPTX)
  So that I can share it with others without needing the DeckBot tool

  Scenario: Build PDF output
    Given I have a presentation named "Test Build Deck"
    And the presentation has a valid "deck.marp.md" file
    When I run the deckbot command "build 'Test Build Deck' --format pdf"
    Then the command should exit successfully
    And a file named "deck.pdf" should exist in the "Test Build Deck" presentation folder

  Scenario: Build HTML output
    Given I have a presentation named "Test Build Deck"
    And the presentation has a valid "deck.marp.md" file
    When I run the deckbot command "build 'Test Build Deck' --format html"
    Then the command should exit successfully
    And a file named "deck.marp.html" should exist in the "Test Build Deck" presentation folder

