Feature: Visual Feedback Loop
  As a user
  I want the agent to visually inspect slides when needed
  So that layout issues, placeholders, and glitches are caught and fixed automatically

  Background:
    Given I have a new presentation "VisualTest"

  Scenario: Sub-agent detects issues on explicit inspection
    Given the presentation contains a slide with text "RAW_CSS_ARTIFACT"
    And I mock the visual sub-agent to report "Found raw CSS artifact on the slide."
    When the agent triggers the "inspect_slide" tool for slide 1
    Then the visual sub-agent should be invoked
    And the agent should receive a system message containing "CRITICAL VISUAL ISSUES FOUND"
    And the agent should receive a system message containing "STOP AND THINK"

  Scenario: Sub-agent is silent when no issues found
    Given the presentation is clean
    And I mock the visual sub-agent to report "No issues found."
    When the agent triggers the "inspect_slide" tool for slide 1
    Then the visual sub-agent should be invoked
    And the agent should receive a system message containing "[Visual QA] Checked slide 1"

  Scenario: Sub-agent explicitly detects content overflow
    Given the presentation contains a slide with text "Content overflowing bottom"
    And I mock the visual sub-agent to report "Content cropped/cut off at the bottom or sides (overflow)."
    When the agent triggers the "inspect_slide" tool for slide 1
    Then the visual sub-agent should be invoked
    And the agent should receive a system message containing "Visual QA Report"
    And the agent should receive a system message containing "Content cropped/cut off"
    And the agent should receive a system message containing "STOP AND THINK"

  Scenario: Navigation does NOT automatically trigger visual inspection
    Given the presentation is clean
    And I mock the visual sub-agent to report "No issues found."
    When the agent triggers the "go_to_slide" tool for slide 1
    Then the agent should NOT receive a system message containing "Visual QA Report"
    And the agent should NOT receive a system message containing "---VISUAL_QA_START---"
