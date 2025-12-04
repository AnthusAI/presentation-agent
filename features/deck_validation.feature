Feature: Deck Validation and Summary
  As an AI agent
  I want to be notified if I break the deck structure
  And receive a summary of the deck content when I successfully update it
  So that I can maintain a high-quality presentation

  Scenario: Update deck.marp.md with valid content
    Given a validation test presentation "validation-test" exists
    When I update "deck.marp.md" with the following content:
      """
      ---
      marp: true
      theme: default
      ---
      
      # Slide 1
      
      Content
      
      ---
      
      # Slide 2
      
      ![Image](image.png)
      """
    Then the file update validation should succeed
    And the tool output should contain "Summary:"
    And the tool output should contain "Slide 1: Title='Slide 1', Images=0"
    And the tool output should contain "Slide 2: Title='Slide 2', Images=1"

  Scenario: Update deck.marp.md with broken frontmatter
    Given a validation test presentation "validation-test" exists
    When I update "deck.marp.md" with the following content:
      """
      ---
      marp: true
      theme: default
      
      # Slide 1
      """
    Then the file update validation should fail
    And the tool error should mention "Frontmatter not closed"

  Scenario: Update deck.marp.md with CSS visible in slide
    Given a validation test presentation "validation-test" exists
    When I update "deck.marp.md" with the following content:
      """
      ---
      marp: true
      theme: default
      ---
      
      <style>
      h1 { color: red; }
      </style>
      
      # Slide 1
      """
    Then the file update validation should succeed
    And the tool output should contain "Summary:"

  # Note: The user mentioned "CSS in the frontmatter ends up visible".
  # This usually happens if the second '---' is missing or malformed,
  # which is covered by "broken frontmatter".
  # If they mean CSS inside the slide body, that is allowed in Marp, 
  # but maybe they mean a specific anti-pattern? 
  # "CSS in the frontmatter ends up visible" -> Frontmatter not closed properly.

