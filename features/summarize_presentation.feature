Feature: Summarize Presentation Tool
  As an AI agent
  I want to get a text summary of the current presentation
  So that I can understand the content without reading every file

  Scenario: Get presentation summary
    Given I have a presentation named "summary-deck"
    And the presentation contains a file "slide1.md" with content "# Slide 1\n![image](image.png)\nSome text"
    When the agent uses the "get_presentation_summary" tool
    Then the result should contain "Slide 1"
    And the result should contain "image.png"
    And the result should contain "Some text"
