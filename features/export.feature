Feature: Export Presentation
  As a user
  I want to export my presentation to PDF
  So that I can share it with others who don't use Marp

  Scenario: Export to PDF
    Given I have a presentation named "My Cool Deck"
    And the presentation contains a file "deck.marp.md" with content "# Title Slide"
    And Marp CLI is available
    When the agent uses the "export_pdf" tool
    Then the result should indicate the PDF export was successful
    And a file "My Cool Deck.pdf" should exist in the presentation

