# Excel MCP Server Installation Guide

This guide will help you install and configure the Excel MCP Server for interacting with Excel files through Claude Desktop and other AI assistants.

## Requirements

- Docker installed on your system.

## Installation

The server runs as a Docker container. You can launch it with a single command.

**Step 1**: Create a local directory for your Excel files. This folder will be mounted into the container.

```bash
mkdir -p excel_files
```

**Step 2**: Run the Docker container.

This command will start the Excel MCP server, map the necessary port, and mount your local `excel_files` directory into the container.

```bash
docker run -d --rm --name excel-mcp \
  -p 8660:8660 \
  -e PORT=8660 \
  -e HOST=0.0.0.0 \
  -e EXCEL_FILES_PATH=/app/excel_files \
  -v "$(pwd)/excel_files":/app/excel_files \
  -v "${HOME}/.excel-mcp:/home/app/.excel-mcp" \
  --platform linux/amd64 \
  ghcr.io/olegische/excel-mcp-server:latest
```
**Note for Windows Users**: Replace `$(pwd)` with the absolute path to your `excel_files` directory.

## IDE/Client Configuration

To connect your AI assistant to the running server, you need to configure it as an MCP server.

**For Claude Desktop, Cursor, or other compatible clients**, add the following to your MCP server configuration:

```json
{
  "mcpServers": {
    "excel": {
      "type": "sse",
      "url": "http://host.docker.internal:8660/sse",
      "headers": {}
    }
  }
}
```

**Configuration File Locations:**
- **Claude Desktop (macOS)**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Claude Desktop (Windows)**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Claude Desktop (Linux)**: `~/.config/Claude/claude_desktop_config.json`
- **Cursor**: Open Settings → MCP → + Add new global MCP server.

## Troubleshooting

- **Connection Issues**:
    - Ensure the Docker container is running: `docker ps | grep excel-mcp`.
    - Verify that port `8660` is not blocked by a firewall.
    - If connecting from a client not running in Docker, you might need to replace `host.docker.internal` with `localhost`.
- **File Not Found Errors**:
    - Make sure the volume path in your `docker run` command is correct.
    - When using tools, provide filepaths relative to the root of the mounted directory (e.g., `my_workbook.xlsx`). The server handles the internal path mapping.
- **Check Container Logs**:
    ```bash
    docker logs excel-mcp
    ```

## Available Tools

### Workbook Operations
- **create_workbook**: Creates a new Excel workbook.
  - `filepath`: Path where to create workbook.
- **create_worksheet**: Creates a new worksheet in an existing workbook.
  - `filepath`: Path to Excel file.
  - `sheet_name`: Name for the new worksheet.
- **get_workbook_metadata**: Get metadata about workbook including sheets and ranges.
  - `filepath`: Path to Excel file.
  - `include_ranges`: Whether to include range information.

### Data Operations
- **write_data_to_excel**: Write data to Excel worksheet.
  - `filepath`: Path to Excel file.
  - `sheet_name`: Target worksheet name.
  - `data`: List of dictionaries containing data to write.
  - `start_cell`: Starting cell (default: "A1").
- **read_data_from_excel**: Read data from Excel worksheet.
  - `filepath`: Path to Excel file.
  - `sheet_name`: Source worksheet name.
  - `start_cell`: Starting cell (default: "A1").
  - `end_cell`: Optional ending cell.
  - `preview_only`: Whether to return only a preview.

### Formatting Operations
- **format_range**: Apply formatting to a range of cells.
  - `filepath`, `sheet_name`, `start_cell`, `end_cell`, and various formatting options.
- **merge_cells**: Merge a range of cells.
  - `filepath`, `sheet_name`, `start_cell`, `end_cell`.
- **unmerge_cells**: Unmerge a previously merged range of cells.
  - `filepath`, `sheet_name`, `start_cell`, `end_cell`.

### Formula Operations
- **apply_formula**: Apply Excel formula to cell.
  - `filepath`, `sheet_name`, `cell`, `formula`.
- **validate_formula_syntax**: Validate Excel formula syntax without applying it.
  - `filepath`, `sheet_name`, `cell`, `formula`.

### Chart Operations
- **create_chart**: Create chart in worksheet.
  - `filepath`, `sheet_name`, `data_range`, `chart_type`, `target_cell`, and optional chart labels.

### Pivot Table Operations
- **create_pivot_table**: Create pivot table in worksheet.
  - `filepath`, `sheet_name`, `data_range`, `target_cell`, `rows`, `values`, and optional columns/aggregation function.

### Table Operations
- **create_table**: Creates a native Excel table from a specified range of data.
  - `filepath`, `sheet_name`, `data_range`, and optional table name/style.

### Worksheet Operations
- **copy_worksheet**: Copy worksheet within workbook.
  - `filepath`, `source_sheet`, `target_sheet`.
- **delete_worksheet**: Delete worksheet from workbook.
  - `filepath`, `sheet_name`.
- **rename_worksheet**: Rename worksheet in workbook.
  - `filepath`, `old_name`, `new_name`.

### Range Operations
- **copy_range**: Copy a range of cells to another location.
  - `filepath`, `sheet_name`, `source_start`, `source_end`, `target_start`, and optional target sheet.
- **delete_range**: Delete a range of cells and shift remaining cells.
  - `filepath`, `sheet_name`, `start_cell`, `end_cell`, and optional shift direction.
- **validate_excel_range**: Validate if a range exists and is properly formatted.
  - `filepath`, `sheet_name`, `start_cell`, and optional end cell.
- **get_data_validation_info**: Get data validation rules and metadata for a worksheet.
  - `filepath`, `sheet_name`.

## Usage Examples

After installation and configuration, you can ask your AI assistant to perform tasks like:

- **Create a new workbook**: "Create a new Excel file named 'report.xlsx'."
- **Write data**: "In 'report.xlsx', create a sheet named 'Sales' and write this data into it: [ ... your data ... ]"
- **Apply formatting**: "In 'report.xlsx' on the 'Sales' sheet, make the header row (A1:D1) bold."
- **Create a chart**: "Create a bar chart from the data in range A2:B10 on the 'Sales' sheet and place it at cell E1."
- **Read data**: "Read the data from the 'Inventory' sheet in 'inventory.xlsx'."

## Security Notes

- The server provides direct access to manipulate files in the mounted directory. Ensure that only trusted users have access to the AI assistant connected to this server.
- Do not expose the server port (`8660`) to the public internet without proper authentication and authorization mechanisms in front of it.
