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
        "error_message": directives.unchanged,
    }

    def get_nested_value(self, data, path):
        keys = path.split(".")
        for key in keys:
            if data is None:
                return None
            if isinstance(data, dict):
                data = data.get(key)
            elif isinstance(data, list):
                try:
                    index = int(key)
                    data = data[index] if 0 <= index < len(data) else None
                except ValueError:
                    return None
            else:
                return None
        return data

    def format_multiline_text(self, text):
        if not text:
            return ""
        return text.replace("\n", "<br>")

    def run(self):
        try:
            json_data = ""

            json_file = self.options.get("file", "").strip()
            if json_file:
                if not os.path.isfile(json_file):
                    error_message = self.options.get("error_message", f"Error: File not found: {json_file}")
                    return [nodes.paragraph(text=error_message)]
                with open(json_file, "r", encoding="utf-8") as f:
                    json_data = f.read().strip()
            else:
                json_data = "\n".join(self.content).strip()

            if not json_data:
                error_message = self.options.get("error_message", "No JSON data provided.")
                return [nodes.paragraph(text=error_message)]

            data = json.loads(json_data)
            json_path = self.options.get("path", "").strip()

            if json_path:
                data = self.get_nested_value(data, json_path)

            if not isinstance(data, list) or not data:
                error_message = self.options.get("error_message", "No valid data available at the given path.")
                return [nodes.paragraph(text=error_message)]

            selected_columns = self.options.get("columns", "").split(",")
            selected_columns = [col.strip() for col in selected_columns if col.strip()]
            if not selected_columns:
                selected_columns = list(data[0].keys())

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
                    if "." in field:
                        value = self.get_nested_value(item, field)
                    else:
                        value = item.get(field, "N/A")
                    value = str(value).strip() if value is not None else "N/A"
                    value = self.format_multiline_text(value)
                    entry = nodes.entry()
                    entry += nodes.raw("", value, format="html")
                    row += entry
                tbody += row

            return [table]

        except Exception as e:
            error_message = self.options.get("error_message", f"Error processing JSON: {str(e)}")
            return [nodes.paragraph(text=error_message)]

def setup(app):
    app.add_directive("json-table", JSONTable)