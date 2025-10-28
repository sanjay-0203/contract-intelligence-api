# Example Contracts

This directory contains sample contract PDFs for testing the Contract Intelligence API.

## Files

1. **service_agreement.pdf** - Sample service agreement between two companies
2. **nda.pdf** - Sample non-disclosure agreement
3. **employment_contract.pdf** - Sample employment contract
4. **license_agreement.pdf** - Sample software license agreement

## Usage

These contracts can be used to:
- Test the API endpoints
- Run the evaluation framework
- Demonstrate the system capabilities
- Develop and test new features

## Creating Test PDFs

Since actual PDFs are not included in this repository, you can create test PDFs from the provided text templates:

```bash
# Use a tool like wkhtmltopdf or pandoc to convert markdown to PDF
pandoc service_agreement_template.md -o service_agreement.pdf
```

Or use online PDF creation tools to create PDFs from the contract templates.

## Sample Contract Templates

See the `*_template.md` files in this directory for contract text that can be converted to PDF format for testing.
