Feature: Automatic Compilation on File Changes

  As a user
  I want the presentation to automatically compile when files are changed
  So that I can see the results immediately without manual compilation steps

  Scenario: Writing a file triggers auto-compilation
    Given I have an auto-compilation test presentation named "Auto Compile Test"
    When I use the tool "write_file" to create "test.md" with content "# Test Slide"
    Then the tool output should contain "Presentation automatically compiled"
    And the presentation should be compiled to HTML

  Scenario: Replacing text triggers auto-compilation
    Given I have an auto-compilation test presentation named "Auto Compile Test"
    And I use the tool "write_file" to create "test.md" with content "# Old Title"
    When I use the tool "replace_text" on "test.md" to replace "Old" with "New"
    Then the tool output should contain "Presentation automatically compiled"
    And the presentation should be compiled to HTML

  Scenario: Updating deck.marp.md triggers auto-compilation
    Given I have an auto-compilation test presentation named "Auto Compile Test"
    When I use the tool "write_file" to create "deck.marp.md" with valid Marp content
    Then the tool output should contain "Presentation automatically compiled"
    And the presentation should be compiled to HTML

  Scenario: Copying a file triggers auto-compilation
    Given I have an auto-compilation test presentation named "Auto Compile Test"
    And I use the tool "write_file" to create "source.txt" with content "data"
    When I use the tool "copy_file" to copy "source.txt" to "dest.txt"
    Then the tool output should contain "Presentation automatically compiled"
    And the presentation should be compiled to HTML

  Scenario: Moving a file triggers auto-compilation
    Given I have an auto-compilation test presentation named "Auto Compile Test"
    And I use the tool "write_file" to create "move_me.txt" with content "data"
    When I use the tool "move_file" to move "move_me.txt" to "moved.txt"
    Then the tool output should contain "Presentation automatically compiled"
    And the presentation should be compiled to HTML

  Scenario: Deleting a file triggers auto-compilation
    Given I have an auto-compilation test presentation named "Auto Compile Test"
    And I use the tool "write_file" to create "delete_me.txt" with content "data"
    When I use the tool "delete_file" to delete "delete_me.txt"
    Then the tool output should contain "Presentation automatically compiled"
    And the presentation should be compiled to HTML

  Scenario: Generating an image triggers auto-compilation
    Given I have an auto-compilation test presentation named "Auto Compile Test"
    When I use the tool "generate_image" with prompt "a cat"
    Then the tool output should contain "Presentation automatically compiled"
    And the presentation should be compiled to HTML
