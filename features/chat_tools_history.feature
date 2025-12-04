Feature: Chat History with Tools

  Scenario: Agent loads tool usage history from file
    Given a presentation "HistoryTest" exists
    And the presentation "HistoryTest" has a history log containing a tool call:
      | key    | value                                         |
      | tool   | write_file                                    |
      | args   | {"filename": "test.txt", "content": "Hello"}  |
      | result | Successfully wrote to test.txt                |
    When the agent is initialized for "HistoryTest"
    And I send the message "What just happened?"
    Then the API request should contain the tool call "write_file" in history
    And the API request should contain the tool output "Successfully wrote to test.txt" in history

  Scenario: Replace text tool call stores structured arguments in history
    Given a presentation "ReplaceTextTest" exists
    And the presentation "ReplaceTextTest" has a file "test.md" with content "Old content here"
    When I use the replace_text tool on "ReplaceTextTest" to replace "Old content here" with "New content here" in "test.md"
    Then the chat history should contain a replace_text tool call with:
      | key       | value                |
      | filename  | test.md              |
      | old_text  | Old content here     |
      | new_text  | New content here    |