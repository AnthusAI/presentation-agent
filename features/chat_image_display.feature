Feature: Chat-Based Image Display
  As a user
  I want to see generated images in the chat
  So that I have a unified conversation experience

  Background:
    Given a presentation "chat-image-test" exists

  Scenario: Images Appear as Individual Chat Messages
    Given I request image generation for "a blue circle"
    When 4 image candidates are generated
    Then I should see 4 individual image messages in chat
    And each image should be displayed inline
    And each image should be clickable

  Scenario: Request Details Shown for Image Generation
    Given I request image generation for "a red square"
    When the generation starts
    Then I should see an image request details message
    And the details should be collapsed by default
    When I expand the details
    Then I should see the user prompt "a red square"
    And I should see the system instructions
    And I should see the aspect ratio and resolution

  Scenario: Selecting an Image in Chat
    Given 4 image candidates are displayed in chat
    When I click on the second image
    Then the second image should be marked as selected
    And all other images should remain visible
    And the selected image should have a visual highlight
    And a selection request should be sent to the backend

  Scenario: Multiple Image Generations in Same Chat
    Given I request image generation for "cat"
    And 4 cat images are displayed
    And I select the first cat image
    When I request image generation for "dog"
    Then 4 new dog images should appear in chat
    And the previous cat images should remain visible
    And only the new dog images should be selectable
    And the previously selected cat image should keep its selection state

  Scenario: Chat Remains Scrollable with Images
    Given I have 10 text messages in chat
    When I generate 4 images
    Then all messages and images should be in the chat history
    And I should be able to scroll through all content
    And the latest image should be at the bottom




