
workflow "security_audit_test" {
    description = "Test security audit workflow"

    step "scan" {
        action = "scan_network"
        target = "127.0.0.1"
        scan_type = "quick"
    }

    step "analyze" {
        action = "analyze_vulnerabilities"
        depends_on = ["scan"]
    }

    step "report" {
        action = "generate_report"
        depends_on = ["analyze"]
        format = "json"
    }
}
