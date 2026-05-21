"""Tests for metrics-branch-protection-stress change.

Verifies Terraform resources, CI/CD triggers, and MCP stress tool
conform to the spec requirements.
"""
import inspect
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


def read_infra(relative_path: str) -> str:
    return (ROOT / "infra" / relative_path).read_text(encoding="utf-8")


def read_root(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def read_mcp(relative_path: str) -> str:
    return (ROOT / "mcp-server" / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Task 1.1 — DynamoDB On-Demand metric names
# ---------------------------------------------------------------------------

class TestDynamoDBMetrics(unittest.TestCase):
    """Dashboard MUST use Consumed*CapacityUnits for PAY_PER_REQUEST tables.
    
    On-demand (PAY_PER_REQUEST) tables do NOT emit ReadRequestUnits or
    WriteRequestUnits — those metrics exist only for provisioned mode.
    The correct metrics are ConsumedReadCapacityUnits and
    ConsumedWriteCapacityUnits.
    """

    def _content(self) -> str:
        return read_infra("modules/crud/main.tf")

    def test_dashboard_uses_consumed_read_capacity(self):
        content = self._content()
        self.assertIn("ConsumedReadCapacityUnits", content)

    def test_dashboard_uses_consumed_write_capacity(self):
        content = self._content()
        self.assertIn("ConsumedWriteCapacityUnits", content)

    def test_dashboard_no_read_request_units(self):
        content = self._content()
        self.assertNotIn("ReadRequestUnits", content)

    def test_dashboard_no_write_request_units(self):
        content = self._content()
        self.assertNotIn("WriteRequestUnits", content)


# ---------------------------------------------------------------------------
# Tasks 1.2–1.5 — SNS topic, email subscription, CloudWatch alarms
# ---------------------------------------------------------------------------

class TestSNSAndAlarms(unittest.TestCase):
    """SNS topic + email sub + 5 CloudWatch alarms."""

    def _content(self) -> str:
        return read_infra("modules/crud/main.tf")

    def test_sns_topic_declared(self):
        content = self._content()
        self.assertRegex(content, r'resource\s+"aws_sns_topic"\s+"alarm_notifications"')

    def test_sns_email_subscription_declared(self):
        content = self._content()
        self.assertRegex(content, r'resource\s+"aws_sns_topic_subscription"\s+"email"')

    def test_alarm_email_variable_referenced(self):
        content = self._content()
        self.assertIn("var.alarm_email", content)

    def test_mcp_tool_errors_alarm(self):
        content = self._content()
        self.assertRegex(content, r'resource\s+"aws_cloudwatch_metric_alarm"\s+"mcp_tool_errors"')

    def test_apigw_5xx_alarm(self):
        content = self._content()
        self.assertRegex(content, r'resource\s+"aws_cloudwatch_metric_alarm"\s+"apigw_5xx"')

    def test_ecs_cpu_alarm(self):
        content = self._content()
        self.assertRegex(content, r'resource\s+"aws_cloudwatch_metric_alarm"\s+"ecs_cpu"')

    def test_alb_healthy_hosts_alarm(self):
        content = self._content()
        self.assertRegex(content, r'resource\s+"aws_cloudwatch_metric_alarm"\s+"alb_healthy_hosts"')

    def test_alarms_reference_sns_topic(self):
        content = self._content()
        # All alarms must reference the SNS topic ARN
        # Count alarm resources and alarm_actions references — they should match
        alarm_count = len(re.findall(r'resource\s+"aws_cloudwatch_metric_alarm"', content))
        actions_count = len(re.findall(r'alarm_actions\s*=\s*\[aws_sns_topic\.alarm_notifications', content))
        self.assertGreater(alarm_count, 0, "Should have at least one alarm")
        self.assertEqual(alarm_count, actions_count, "All alarms should reference SNS topic")


# ---------------------------------------------------------------------------
# Tasks 1.6–1.7 — ECS scaling variables + parameterized autoscaling
# ---------------------------------------------------------------------------

class TestECSScalingVariables(unittest.TestCase):
    """ECS min/desired/max capacity as Terraform variables with defaults 1/1/2."""

    def _variables(self) -> str:
        return read_infra("modules/crud/variables.tf")

    def _main(self) -> str:
        return read_infra("modules/crud/main.tf")

    def test_ecs_min_capacity_variable(self):
        content = self._variables()
        self.assertIn("ecs_min_capacity", content)

    def test_ecs_desired_count_variable(self):
        content = self._variables()
        self.assertIn("ecs_desired_count", content)

    def test_ecs_max_capacity_variable(self):
        content = self._variables()
        self.assertIn("ecs_max_capacity", content)

    def test_alarm_email_variable(self):
        content = self._variables()
        self.assertIn("alarm_email", content)

    def test_autoscaling_uses_min_capacity_variable(self):
        content = self._main()
        self.assertIn("var.ecs_min_capacity", content)

    def test_autoscaling_uses_max_capacity_variable(self):
        content = self._main()
        self.assertIn("var.ecs_max_capacity", content)

    def test_ecs_service_uses_desired_count_variable(self):
        content = self._main()
        self.assertIn("var.ecs_desired_count", content)


# ---------------------------------------------------------------------------
# Task 1.8 — Outputs for SNS topic ARN
# ---------------------------------------------------------------------------

class TestOutputs(unittest.TestCase):
    """Export SNS topic ARN and alarm ARNs."""

    def _content(self) -> str:
        return read_infra("modules/crud/outputs.tf")

    def test_sns_topic_arn_output(self):
        content = self._content()
        self.assertRegex(content, r'output\s+"sns_topic_arn"')


# ---------------------------------------------------------------------------
# Tasks 2.1–2.2 — MCP stress tool
# ---------------------------------------------------------------------------

class TestMCPStressTool(unittest.TestCase):
    """stress_test tool with iterations, concurrency, delay_ms parameters."""

    def _content(self) -> str:
        return read_mcp("mcp_server.py")

    def test_stress_tool_function_exists(self):
        content = self._content()
        self.assertIn("def stress_test(", content)

    def test_stress_tool_has_iterations_param(self):
        content = self._content()
        self.assertRegex(content, r'iterations.*int.*=\s*10')

    def test_stress_tool_has_concurrency_param(self):
        content = self._content()
        self.assertRegex(content, r'concurrency.*int.*=\s*1')

    def test_stress_tool_has_delay_ms_param(self):
        content = self._content()
        self.assertRegex(content, r'delay_ms.*int.*=\s*100')

    def test_stress_tool_decorated_with_mcp_tool(self):
        content = self._content()
        self.assertIn("@mcp.tool()", content)

    def test_stress_tool_calls_api_endpoints(self):
        """Tool must call existing API endpoints (product_list, dictionary_list, shopping_cart_list)."""
        content = self._content()
        # Should reference at least one of the list endpoints
        has_product = "product_list" in content
        has_dictionary = "dictionary_list" in content
        has_cart = "shopping_cart_list" in content
        self.assertTrue(
            has_product or has_dictionary or has_cart,
            "stress_test should call at least one list endpoint",
        )


# ---------------------------------------------------------------------------
# Tasks 3.1–3.2 — CI/CD branch triggers
# ---------------------------------------------------------------------------

class TestCIWorkflowTriggers(unittest.TestCase):
    """CI triggers on PRs to any branch AND pushes to staging + main."""

    def _content(self) -> str:
        return read_root(".github/workflows/ci.yml")

    def test_ci_has_pull_request_trigger(self):
        content = self._content()
        self.assertIn("pull_request", content)

    def test_ci_push_includes_staging(self):
        content = self._content()
        self.assertIn("staging", content)

    def test_ci_push_includes_main(self):
        content = self._content()
        self.assertIn("main", content)


class TestCDWorkflowTriggers(unittest.TestCase):
    """CD triggers on pushes to staging and main only."""

    def _content(self) -> str:
        return read_root(".github/workflows/cd.yml")

    def test_cd_push_includes_staging(self):
        content = self._content()
        self.assertIn("staging", content)

    def test_cd_push_includes_main(self):
        content = self._content()
        self.assertIn("main", content)


# ---------------------------------------------------------------------------
# Task 4.1 — README architecture image
# ---------------------------------------------------------------------------

class TestREADMEArchitectureImage(unittest.TestCase):
    """README.md references architecture image."""

    def _content(self) -> str:
        return read_root("README.md")

    def test_readme_has_architecture_image(self):
        content = self._content()
        # Should have an image reference (markdown or HTML)
        has_image = (
            "architecture.png" in content
            or "architecture.jpg" in content
            or "architecture.svg" in content
            or "docs/architecture" in content
        )
        self.assertTrue(has_image, "README should reference an architecture image")


if __name__ == "__main__":
    unittest.main()
