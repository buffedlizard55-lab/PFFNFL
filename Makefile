.PHONY: verify test export clean

verify:
	python scripts/verify_pff.py

test:
	python tests/test_pff_parsers.py

export:
	python scripts/export_to_parquet.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

all: verify test export
