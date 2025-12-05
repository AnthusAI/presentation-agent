Feature: Semantic Release Configuration
  As a developer
  I want automated versioning and release management
  So that releases are consistent and follow semantic versioning

  Background:
    Given the project has semantic release configured

  Scenario: Version is accessible from package
    When I import the deckbot package
    Then the version should be defined
    And the version should match the pyproject.toml version

  Scenario: Pyproject.toml has semantic release configuration
    When I read the pyproject.toml file
    Then it should contain semantic_release configuration
    And it should specify version_toml for pyproject.toml
    And it should specify version_variables for __init__.py

  Scenario: GitHub Actions workflow exists
    When I check the .github/workflows directory
    Then there should be a ci.yml file
    And the workflow should have a test job
    And the workflow should have a release job

  Scenario: Commit convention documentation exists
    When I check the .github directory
    Then there should be a COMMIT_CONVENTION.md file
    And it should describe conventional commits format

  Scenario: CHANGELOG file exists
    When I check the project root
    Then there should be a CHANGELOG.md file




