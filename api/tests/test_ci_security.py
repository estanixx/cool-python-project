import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


def read_workflow(relative_path: str) -> str:
    return (ROOT / ".github" / "workflows" / relative_path).read_text(encoding="utf-8")


def read_root_file(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class TestCodeQLWorkflow(unittest.TestCase):
    """CodeQL SAST workflow — spec scenarios: PR trigger, weekly schedule, matrix, exclusions."""

    def test_codeql_file_exists(self):
        content = read_workflow("codeql.yml")
        self.assertIn("name:", content)

    def test_codeql_name_is_codeql(self):
        content = read_workflow("codeql.yml")
        self.assertIn("CodeQL", content)

    def test_codeql_triggers_on_pull_request(self):
        content = read_workflow("codeql.yml")
        self.assertIn("pull_request:", content)

    def test_codeql_triggers_on_all_branches(self):
        content = read_workflow("codeql.yml")
        self.assertIn('branches:', content)
        self.assertIn('"*"', content)

    def test_codeql_has_weekly_schedule(self):
        content = read_workflow("codeql.yml")
        self.assertIn("schedule:", content)
        self.assertIn("cron:", content)
        self.assertIn("0 0 * * 0", content)

    def test_codeql_language_matrix_has_python_and_actions(self):
        content = read_workflow("codeql.yml")
        self.assertIn("language:", content)
        self.assertIn("python", content)
        self.assertIn("actions", content)

    def test_codeql_uses_init_action(self):
        content = read_workflow("codeql.yml")
        self.assertIn("github/codeql-action/init", content)

    def test_codeql_uses_autobuild_action(self):
        content = read_workflow("codeql.yml")
        self.assertIn("github/codeql-action/autobuild", content)

    def test_codeql_uses_analyze_action(self):
        content = read_workflow("codeql.yml")
        self.assertIn("github/codeql-action/analyze", content)

    def test_codeql_uploads_sarif(self):
        content = read_workflow("codeql.yml")
        # analyze@v3 uploads SARIF automatically to GitHub Security tab
        self.assertIn("github/codeql-action/analyze", content)
        self.assertIn("security-events: write", content)

    def test_codeql_excludes_test_directory(self):
        content = read_workflow("codeql.yml")
        self.assertIn("test/", content)

    def test_codeql_excludes_vendor_directory(self):
        content = read_workflow("codeql.yml")
        self.assertIn("vendor/", content)

    def test_codeql_excludes_node_modules_directory(self):
        content = read_workflow("codeql.yml")
        self.assertIn("node_modules/", content)


class TestDependabotConfig(unittest.TestCase):
    """Dependabot config — spec scenarios: 3 ecosystems, grouped updates, weekly schedule."""

    def test_dependabot_file_exists(self):
        content = read_root_file(".github/dependabot.yml")
        self.assertIn("version:", content)

    def test_dependabot_version_2(self):
        content = read_root_file(".github/dependabot.yml")
        self.assertIn("2", content)

    def test_dependabot_has_pip_for_api(self):
        content = read_root_file(".github/dependabot.yml")
        self.assertIn("pip", content)
        self.assertIn('"/api"', content)

    def test_dependabot_has_pip_for_mcp_server(self):
        content = read_root_file(".github/dependabot.yml")
        self.assertIn('"/mcp-server"', content)

    def test_dependabot_has_github_actions(self):
        content = read_root_file(".github/dependabot.yml")
        self.assertIn("github-actions", content)

    def test_dependabot_has_three_update_entries(self):
        content = read_root_file(".github/dependabot.yml")
        occurrences = content.count("package-ecosystem:")
        self.assertGreaterEqual(occurrences, 3)

    def test_dependabot_has_grouped_updates(self):
        content = read_root_file(".github/dependabot.yml")
        self.assertIn("api-dependencies", content)
        self.assertIn("mcp-server-dependencies", content)
        self.assertIn("github-actions", content)

    def test_dependabot_has_weekly_schedule(self):
        content = read_root_file(".github/dependabot.yml")
        self.assertIn("schedule:", content)
        self.assertIn("weekly", content)


class TestSonarProjectProperties(unittest.TestCase):
    """SonarQube project config — spec scenario: valid project properties."""

    def test_sonar_properties_file_exists(self):
        content = read_root_file("sonar-project.properties")
        self.assertIn("sonar.", content)

    def test_sonar_project_key(self):
        content = read_root_file("sonar-project.properties")
        self.assertIn("sonar.projectKey=estanixx_cool-python-project", content)

    def test_sonar_project_name(self):
        content = read_root_file("sonar-project.properties")
        self.assertIn("sonar.projectName=cool-python-project", content)

    def test_sonar_sources(self):
        content = read_root_file("sonar-project.properties")
        self.assertIn("sonar.sources=", content)
        self.assertIn("api/", content)
        self.assertIn("mcp-server/", content)

    def test_sonar_tests(self):
        content = read_root_file("sonar-project.properties")
        self.assertIn("sonar.tests=", content)
        self.assertIn("api/tests/", content)

    def test_sonar_coverage_path(self):
        content = read_root_file("sonar-project.properties")
        self.assertIn("sonar.python.coverage.reportPaths=", content)
        self.assertIn("coverage.xml", content)

    def test_sonar_exclusions(self):
        content = read_root_file("sonar-project.properties")
        self.assertIn("sonar.exclusions=", content)
        self.assertIn("tests/", content)
        self.assertIn("vendor/", content)
        self.assertIn("node_modules/", content)


class TestCISonarQubeJob(unittest.TestCase):
    """CI pipeline sonarqube job — spec scenarios: depends on test, graceful skip, steps."""

    def test_ci_has_sonarqube_job(self):
        content = read_workflow("ci.yml")
        self.assertIn("sonarqube:", content)

    def test_sonarqube_needs_test(self):
        content = read_workflow("ci.yml")
        self.assertIn("needs: test", content)

    def test_sonarqube_runs_on_ubuntu(self):
        content = read_workflow("ci.yml")
        self.assertIn("runs-on: ubuntu-latest", content)

    def test_sonarqube_conditional_on_token(self):
        content = read_workflow("ci.yml")
        self.assertIn("SONAR_TOKEN", content)
        self.assertIn("if: env.SONAR_TOKEN != ''", content)

    def test_sonarqube_checkout_fetch_depth_zero(self):
        content = read_workflow("ci.yml")
        self.assertIn("fetch-depth: 0", content)

    def test_sonarqube_uses_sonarcloud_action(self):
        content = read_workflow("ci.yml")
        self.assertIn("SonarSource/sonarcloud-github-action", content)

    def test_sonarqube_step_is_report_only(self):
        content = read_workflow("ci.yml")
        self.assertIn("continue-on-error: true", content)


class TestCITrivyStep(unittest.TestCase):
    """CI pipeline Trivy step — spec scenarios: scans infra, outputs SARIF, uploads results."""

    def test_ci_has_trivy_step(self):
        content = read_workflow("ci.yml")
        self.assertIn("Trivy", content)

    def test_trivy_uses_aquasecurity_action(self):
        content = read_workflow("ci.yml")
        self.assertIn("aquasecurity/trivy-action", content)

    def test_trivy_scan_type_config(self):
        content = read_workflow("ci.yml")
        self.assertIn("scan-type: config", content)

    def test_trivy_scan_ref_infra(self):
        content = read_workflow("ci.yml")
        self.assertIn("scan-ref: infra/", content)

    def test_trivy_outputs_sarif_format(self):
        content = read_workflow("ci.yml")
        self.assertIn("format: sarif", content)
        self.assertIn("output: trivy-results.sarif", content)

    def test_trivy_exit_code_on_high_severity(self):
        content = read_workflow("ci.yml")
        self.assertIn("exit-code: \"0\"", content)
        self.assertIn("severity: CRITICAL,HIGH", content)

    def test_trivy_uploads_sarif_results(self):
        content = read_workflow("ci.yml")
        self.assertIn("upload-sarif", content)
        self.assertIn("if: always()", content)
        self.assertIn("sarif_file: trivy-results.sarif", content)


class TestCIExistingJobsUnchanged(unittest.TestCase):
    """Regression: existing test and terraform jobs must remain unchanged."""

    def test_test_job_still_exists(self):
        content = read_workflow("ci.yml")
        self.assertIn("test:", content)
        self.assertIn("Python Tests", content)

    def test_test_job_still_runs_unittest(self):
        content = read_workflow("ci.yml")
        self.assertIn("python -m unittest discover", content)

    def test_terraform_job_still_exists(self):
        content = read_workflow("ci.yml")
        self.assertIn("Terraform Validate", content)

    def test_terraform_fmt_step_unchanged(self):
        content = read_workflow("ci.yml")
        self.assertIn("terraform fmt -check -recursive infra/", content)

    def test_terraform_validate_test_unchanged(self):
        content = read_workflow("ci.yml")
        self.assertIn("Terraform Validate (test)", content)
        self.assertIn("cd infra/test", content)

    def test_terraform_validate_prod_unchanged(self):
        content = read_workflow("ci.yml")
        self.assertIn("Terraform Validate (prod)", content)
        self.assertIn("cd infra/prod", content)


class TestTrivyIgnoreFile(unittest.TestCase):
    """Trivy ignore file — report-only mode must not rely on .trivyignore."""

    def test_trivyignore_is_removed(self):
        trivyignore_path = ROOT / ".trivyignore"
        self.assertFalse(trivyignore_path.exists())


class TestSonarOrganizationProperty(unittest.TestCase):
    """SonarQube properties — spec scenario: sonar.organization exists."""

    def test_sonar_organization_exists(self):
        content = read_root_file("sonar-project.properties")
        self.assertIn("sonar.organization=estanixx", content)
