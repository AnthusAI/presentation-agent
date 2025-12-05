Feature: Style Specification Management
  As a user
  I want to manage the style specification for my presentation
  So that the AI generates content and images that match my style

  Background:
    Given a presentation "StyleTest" exists
    And the presentation has a "metadata.json" file

  Scenario: Get style specification
    Given the presentation has the following styling in metadata:
      | key                 | value                                  |
      | instructions        | Use professional tone                  |
      | image_style.prompt  | Minimalist blue                        |
    And the presentation has a style reference image "images/style.png"
    When I request the style specification
    Then the response should contain:
      | key                 | value                                  |
      | instructions        | Use professional tone                  |
      | image_style.prompt  | Minimalist blue                        |
      | image_style.style_reference | images/style.png                 |

  Scenario: Update style specification text
    When I update the style specification with:
      | key                 | value                                  |
      | instructions        | Use casual tone                        |
      | image_style.prompt  | Vibrant neon                           |
    Then the "metadata.json" should contain:
      | key                 | value                                  |
      | instructions        | Use casual tone                        |
      | image_style.prompt  | Vibrant neon                           |

  Scenario: Upload style reference image
    When I upload a style reference image "new_ref.png"
    Then the file "images/style.png" should exist in the presentation directory

  Scenario: Remove style reference image
    Given the presentation has a style reference image "images/style.png"
    When I remove the style reference image
    Then the file "images/style.png" should not exist in the presentation directory

