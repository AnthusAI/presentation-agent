Feature: System Images for Templates
  As a user
  I want standard placeholder images available in all presentations
  So that layouts have proper placeholders and templates can include custom images

  Background:
    Given the system images directory exists with placeholder images

  Scenario: New presentation without template copies system images
    When I create a presentation "test-pres" without a template
    Then the presentation "test-pres" should have an "images" folder
    And the "images" folder should contain "placeholder-square.png"
    And the "images" folder should contain "placeholder-landscape.png"
    And the "images" folder should contain "placeholder-portrait.png"

  Scenario: New presentation from template without images uses system images
    Given a template "MinimalTemplate" exists without an images folder
    When I create a presentation "minimal-test" from template "MinimalTemplate"
    Then the presentation "minimal-test" should have an "images" folder
    And the "images" folder should contain "placeholder-square.png"
    And the "images" folder should contain "placeholder-landscape.png"
    And the "images" folder should contain "placeholder-portrait.png"

  @wip @ci_flaky
  Scenario: Template with custom images overrides system images
    Given a template "BrandedTemplate" exists with custom images
    And the template has "custom-logo.png" in its images folder
    When I create a presentation "branded-test" from template "BrandedTemplate"
    Then the presentation "branded-test" should have an "images" folder
    And the "images" folder should contain "custom-logo.png"
    And the "images" folder should NOT contain "placeholder-square.png"

  @wip @ci_flaky
  Scenario: Template with custom images AND wants system images gets both
    Given a template "HybridTemplate" exists with custom images
    And the template has "brand-logo.png" in its images folder
    And the template metadata indicates "include_system_images: true"
    When I create a presentation "hybrid-test" from template "HybridTemplate"
    Then the presentation "hybrid-test" should have an "images" folder
    And the "images" folder should contain "brand-logo.png"
    And the "images" folder should contain "placeholder-square.png"
    And the "images" folder should contain "placeholder-landscape.png"
    And the "images" folder should contain "placeholder-portrait.png"

  Scenario: Layouts reference correct placeholder images
    Given I create a presentation "layout-test" without a template
    When I read the "layouts.md" file
    Then the "full-image" layout should reference "images/placeholder-square.png"
    And the "image-caption" layout should reference "images/placeholder-landscape.png"
    And the "image-left" layout should reference "images/placeholder-portrait.png"
    And the "image-right" layout should reference "images/placeholder-portrait.png"

  Scenario: System images are the correct aspect ratios
    Given the system images exist
    Then "placeholder-square.png" should have aspect ratio close to 1:1
    And "placeholder-landscape.png" should have aspect ratio close to 16:9
    And "placeholder-portrait.png" should have aspect ratio close to 9:16

  Scenario: Agent is aware of available placeholder images
    Given I create a presentation "agent-test" without a template
    And I load the presentation "agent-test"
    When the agent is queried about available images
    Then the agent should mention "placeholder-square.png"
    And the agent should mention "placeholder-landscape.png"
    And the agent should mention "placeholder-portrait.png"

