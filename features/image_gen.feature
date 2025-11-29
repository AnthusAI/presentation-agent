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

