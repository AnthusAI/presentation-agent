Feature: Save As Presentation

  Scenario: Save As with custom description
    Given I have a presentation named "Source Presentation"
    And the presentation "Source Presentation" has description "Original description"
    When I save the presentation as "New Presentation" with description "New description"
    Then I should have a presentation named "New Presentation"
    And the presentation "New Presentation" should have description "New description"
    And the presentation metadata name should be "New Presentation"

  Scenario: Save As preserves description when not specified
    Given I have a presentation named "Source Presentation"
    And the presentation "Source Presentation" has description "Original description"
    When I save the presentation as "New Presentation" without description
    Then I should have a presentation folder for "New Presentation"
    And the presentation "New Presentation" should have description "Original description"

  Scenario: Save As auto-increments folder name when duplicate exists
    Given I have a presentation named "Standup"
    When I save the presentation as "Standup"
    Then I should have a folder named "Standup 2"
    And the presentation metadata name should be "Standup"
    And the presentation "Standup 2" should have name "Standup" in metadata

  Scenario: Save As auto-increments multiple times
    Given I have a presentation named "Standup"
    And I have a folder named "Standup 2"
    When I save the presentation as "Standup"
    Then I should have a folder named "Standup 3"
    And the presentation metadata name should be "Standup"
    And the presentation "Standup 3" should have name "Standup" in metadata

  Scenario: Save As copies images by default
    Given I have a presentation named "Source Presentation"
    And the presentation "Source Presentation" has an image file "test.png"
    When I save the presentation as "New Presentation" with images
    Then I should have a presentation folder for "New Presentation"
    And the presentation "New Presentation" should have an image file "test.png"

  Scenario: Save As can skip copying images
    Given I have a presentation named "Source Presentation"
    And the presentation "Source Presentation" has an image file "test.png"
    When I save the presentation as "New Presentation" without images
    Then I should have a presentation folder for "New Presentation"
    And the presentation "New Presentation" should not have an image file "test.png"

  Scenario: Save As preserves aspect ratio
    Given I have a presentation named "Source Presentation"
    And I set the aspect ratio of "Source Presentation" to "16:9"
    When I save the presentation as "New Presentation"
    Then the presentation "New Presentation" should have aspect ratio "16:9"

  Scenario: Save As copies all presentation files
    Given I have a presentation named "Source Presentation"
    And the presentation "Source Presentation" has a file "deck.marp.md"
    And the presentation "Source Presentation" has a file "metadata.json"
    When I save the presentation as "New Presentation"
    Then the presentation "New Presentation" should have a file "deck.marp.md"
    And the presentation "New Presentation" should have a file "metadata.json"

