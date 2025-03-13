import json
import os
from docutils import nodes
from docutils.parsers.rst import Directive, directives

class JSONTable(Directive):
    has_content = True
    option_spec = {
        "file": directives.unchanged,
        "path": directives.unchanged,
        "headers": directives.unchanged,
        "columns": directives.unchanged,
    }

    def get_nested_value(self, data, path):
        keys = path.split(".")
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key, {})
            else:
                return []
        return data if isinstance(data, list) else []

    def run(self):
        try:
            json_data = ""

            json_file = self.options.get("file", "").strip()
            if json_file:
                if not os.path.isfile(json_file):
                    return [nodes.paragraph(text=f"Error: File not found: {json_file}")]
                with open(json_file, "r", encoding="utf-8") as f:
                    json_data = f.read().strip()
            else:
                json_data = "\n".join(self.content).strip()

            if not json_data:
                return [nodes.paragraph(text="No JSON data provided.")]

            data = json.loads(json_data)
            json_path = self.options.get("path", "").strip()

            if json_path:
                data = self.get_nested_value(data, json_path)

            if not isinstance(data, list) or not data:
                return [nodes.paragraph(text="No valid data available at the given path.")]

            available_fields = list(data[0].keys())

            selected_columns = self.options.get("columns", "").split(",")
            selected_columns = [col.strip() for col in selected_columns if col.strip()]
            if not selected_columns:
                selected_columns = available_fields

            custom_headers = self.options.get("headers", "").split(",")
            custom_headers = [h.strip() for h in custom_headers if h.strip()]

            if len(custom_headers) != len(selected_columns):
                custom_headers = selected_columns

            table = nodes.table()
            tgroup = nodes.tgroup(cols=len(selected_columns))
            table += tgroup

            for _ in selected_columns:
                tgroup += nodes.colspec(colwidth=1)

            thead = nodes.thead()
            tgroup += thead
            head_row = nodes.row()
            for header in custom_headers:
                entry = nodes.entry()
                entry += nodes.strong(text=header)
                head_row += entry
            thead += head_row

            tbody = nodes.tbody()
            tgroup += tbody
            for item in data:
                row = nodes.row()
                for field in selected_columns:
                    value = str(item.get(field, "N/A")).strip()
                    entry = nodes.entry()
                    entry += nodes.paragraph("", nodes.Text(value))
                    row += entry
                tbody += row

            return [table]

        except Exception as e:
            return [nodes.paragraph(text=f"Error processing JSON: {str(e)}")]

def setup(app):
    app.add_directive("json-table", JSONTable)