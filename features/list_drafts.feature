Feature: List Drafts

  Scenario: Listing drafts returns items in reverse chronological order
    Given a presentation "DraftsTest" exists
    And I create a directory "drafts" in "DraftsTest"
    And I wait 1 second
    And I create a file "drafts/old_file.txt" in "DraftsTest"
    And I wait 1 second
    And I create a directory "drafts/newer_folder" in "DraftsTest"
    And I wait 1 second
    And I create a file "drafts/newest_file.txt" in "DraftsTest"
    When the agent lists files in "drafts"
    Then the list should start with "newest_file.txt"
    And the list should contain "newer_folder" after "newest_file.txt"
    And the list should contain "old_file.txt" after "newer_folder"




