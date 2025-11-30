"""
Tests for JSON Schema Exporter

Tests for schema export utilities.

Version: 1.0.0
Created: 2025-11-29
"""

import pytest
import json
from src.utils.schema_exporter import (
    JSONSchemaExporter,
    create_chart_data_schema,
    create_pie_chart_schema,
    create_bar_chart_schema
)


class TestJSONSchemaExporter:
    """Test JSONSchemaExporter class"""

    def test_create_exporter(self):
        """Test creating exporter"""
        exporter = JSONSchemaExporter()

        assert exporter.schema_version == "http://json-schema.org/draft-07/schema#"

    def test_string_property(self):
        """Test creating string property"""
        exporter = JSONSchemaExporter()

        prop = exporter.string_property(
            description="Test property",
            min_length=1,
            max_length=100
        )

        assert prop["type"] == "string"
        assert prop["description"] == "Test property"
        assert prop["minLength"] == 1
        assert prop["maxLength"] == 100

    def test_number_property(self):
        """Test creating number property"""
        exporter = JSONSchemaExporter()

        prop = exporter.number_property(
            description="Test number",
            minimum=0,
            maximum=100
        )

        assert prop["type"] == "number"
        assert prop["minimum"] == 0
        assert prop["maximum"] == 100

    def test_integer_property(self):
        """Test creating integer property"""
        exporter = JSONSchemaExporter()

        prop = exporter.integer_property(
            description="Test integer",
            minimum=1,
            maximum=10
        )

        assert prop["type"] == "integer"
        assert prop["minimum"] == 1
        assert prop["maximum"] == 10

    def test_boolean_property(self):
        """Test creating boolean property"""
        exporter = JSONSchemaExporter()

        prop = exporter.boolean_property(
            description="Test flag",
            default=True
        )

        assert prop["type"] == "boolean"
        assert prop["default"] is True

    def test_array_property(self):
        """Test creating array property"""
        exporter = JSONSchemaExporter()

        prop = exporter.array_property(
            description="Test array",
            items={"type": "string"},
            min_items=1,
            max_items=10
        )

        assert prop["type"] == "array"
        assert prop["items"]["type"] == "string"
        assert prop["minItems"] == 1
        assert prop["maxItems"] == 10

    def test_object_schema(self):
        """Test creating object schema"""
        exporter = JSONSchemaExporter()

        schema = exporter.object_schema(
            properties={
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            required=["name"]
        )

        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]
        assert schema["required"] == ["name"]

    def test_create_object_schema(self):
        """Test creating complete object schema"""
        exporter = JSONSchemaExporter()

        schema = exporter.create_object_schema(
            title="TestSchema",
            description="Test schema description",
            properties={
                "field1": {"type": "string"},
                "field2": {"type": "number"}
            },
            required=["field1"]
        )

        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert schema["title"] == "TestSchema"
        assert schema["description"] == "Test schema description"
        assert schema["type"] == "object"
        assert "field1" in schema["properties"]
        assert schema["required"] == ["field1"]

    def test_create_variant_input_schema(self):
        """Test creating variant input schema"""
        exporter = JSONSchemaExporter()

        schema = exporter.create_variant_input_schema(
            variant_id="test_variant",
            variant_name="Test Variant",
            properties={
                "data": {"type": "array"},
                "title": {"type": "string"}
            },
            required=["data", "title"]
        )

        assert schema["title"] == "Test VariantInput"
        assert "test_variant" in schema["description"]
        assert schema["properties"]["data"]["type"] == "array"
        assert schema["required"] == ["data", "title"]

    def test_create_variant_output_schema_html(self):
        """Test creating variant output schema for HTML"""
        exporter = JSONSchemaExporter()

        schema = exporter.create_variant_output_schema(
            variant_id="test_variant",
            variant_name="Test Variant",
            output_format="html"
        )

        assert schema["title"] == "Test VariantOutput"
        assert "html_content" in schema["properties"]
        assert "success" in schema["properties"]
        assert "variant_id" in schema["properties"]

    def test_export_schema_to_json(self):
        """Test exporting schema to JSON string"""
        exporter = JSONSchemaExporter()

        schema = {
            "type": "object",
            "properties": {
                "test": {"type": "string"}
            }
        }

        json_str = exporter.export_schema(schema)

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["type"] == "object"
        assert "test" in parsed["properties"]


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_create_chart_data_schema(self):
        """Test creating chart data schema"""
        schema = create_chart_data_schema()

        assert schema["type"] == "array"
        assert "items" in schema
        assert schema["items"]["type"] == "object"
        assert "label" in schema["items"]["properties"]
        assert "value" in schema["items"]["properties"]

    def test_create_pie_chart_schema(self):
        """Test creating pie chart schemas"""
        schemas = create_pie_chart_schema()

        assert "input" in schemas
        assert "output" in schemas

        # Check input schema
        input_schema = schemas["input"]
        assert input_schema["title"] == "Pie ChartInput"
        assert "data" in input_schema["properties"]
        assert "title" in input_schema["properties"]
        assert input_schema["required"] == ["data", "title"]

        # Check output schema
        output_schema = schemas["output"]
        assert output_schema["title"] == "Pie ChartOutput"
        assert "html_content" in output_schema["properties"]

    def test_create_bar_chart_schema(self):
        """Test creating bar chart schemas"""
        schemas = create_bar_chart_schema()

        assert "input" in schemas
        assert "output" in schemas

        input_schema = schemas["input"]
        assert "orientation" in input_schema["properties"]
        assert input_schema["properties"]["orientation"]["enum"] == ["vertical", "horizontal"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
