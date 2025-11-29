Feature: Agent Tools
  As an AI agent
  I want to have tools to interact with the presentation
  So that I can implement the user's requests

  Scenario: List files in the presentation directory
    Given I have a presentation named "test-deck"
    And the presentation contains an empty file "slide1.md"
    When the agent uses the "list_files" tool
    Then the result should contain "slide1.md"

  Scenario: Read a file
    Given I have a presentation named "test-deck"
    And the presentation contains a file "intro.md" with content "# Intro"
    When the agent uses the "read_file" tool for "intro.md"
    Then the result should match "# Intro"

  Scenario: Write a file
    Given I have a presentation named "test-deck"
    When the agent uses the "write_file" tool for "new_slide.md" with content "# New Slide"
    Then the file "new_slide.md" should exist in the presentation
    And the content of "new_slide.md" should match "# New Slide"

  Scenario: Compile presentation
    Given I have a presentation named "test-deck"
    And the presentation contains a file "deck.marp.md" with content "# Slide 1"
    And Marp CLI is available
    When the agent uses the "compile_presentation" tool
    Then the result should indicate success

  Scenario: Generate image tool
    Given I have a presentation named "test-deck"
    When the agent uses the "generate_image" tool with prompt "A cool robot"
    Then the Nano Banana client should generate candidates
    And the result should be a relative file path

