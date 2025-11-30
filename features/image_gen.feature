Feature: Nano Banana Image Generation
  As a user
  I want to generate images for my slides
  So that I can make them look professional

  Scenario: Generate image candidates
    Given I am in the REPL for "my-deck"
    When I request an image for "A futuristic city skyline"
    Then 4 image candidates should be generated using Nano Banana
    And I should be prompted to select one

  Scenario: Select an image
    Given 4 image candidates have been generated
    When I select candidate 2
    Then the image from candidate 2 should be saved to the presentation images folder
    And the other candidates should be cleaned up

  Scenario: Web Mode Async Generation
    Given I am using the web UI
    When the agent calls generate_image for "A serene lake"
    Then the agent should receive a WAIT message
    And the agent should NOT proceed with writing files
    And the web UI should show the candidates

  Scenario: Web Mode Agent Resumes
    Given the agent is waiting for image selection
    When I choose candidate number 1 in the web UI
    Then a SYSTEM message should be sent to the agent
    And the message should contain the saved filename

  Scenario: Default aspect ratio matches presentation
    Given I have a presentation with aspect ratio "16:9"
    When the agent generates an image without specifying aspect ratio
    Then the image should be generated with aspect ratio "16:9"

  Scenario: Override presentation aspect ratio
    Given I have a presentation with aspect ratio "16:9"
    When the agent generates a square image
    Then the image should be generated with aspect ratio "1:1"
