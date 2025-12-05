Feature: Conversation Context
  As a user
  I want the agent to remember previous messages in the conversation
  So that I can have natural, contextual conversations without repeating myself

  Scenario: Agent remembers previous request
    Given I have a presentation named "context-test"
    And the agent is active for "context-test"
    When I type "Generate a diagram showing a feedback loop"
    And I type "Make it blue instead"
    Then the agent's response should reference the previous image request
    And the agent should not ask what image to modify

  Scenario: Agent maintains context across multiple turns
    Given I have a presentation named "multi-turn-test"
    And the agent is active for "multi-turn-test"
    When I type "Let's create a presentation about AI"
    And I type "Add a slide about neural networks"
    And I type "Now add one about transformers"
    Then the agent should understand "one" refers to a slide
    And the agent should not ask for clarification about the topic

  Scenario: Agent uses loaded history on resume
    Given I have a presentation named "resume-context-test"
    And the presentation has chat history:
      | role  | content                                    |
      | user  | I want to create slides about cats         |
      | model | Great! I'll help you create slides about cats. |
    When I load the presentation "resume-context-test"
    And I type "Add a slide about their hunting behavior"
    Then the agent should understand "their" refers to cats
    And the agent should not ask what topic to cover





