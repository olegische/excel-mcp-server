import logging
import os
from typing import Any, List, Dict

from mcp.server.fastmcp import FastMCP

# Import exceptions
from excel_mcp.exceptions import (
    ValidationError,
    WorkbookError,
    SheetError,
    DataError,
    FormattingError,
    CalculationError,
    PivotError,
    ChartError
)

# Import from excel_mcp package with consistent _impl suffixes
from excel_mcp.validation import (
    validate_formula_in_cell_operation as validate_formula_impl,
    validate_range_in_sheet_operation as validate_range_impl
)
from excel_mcp.chart import create_chart_in_sheet as create_chart_impl
from excel_mcp.workbook import get_workbook_info
from excel_mcp.data import write_data
from excel_mcp.pivot import create_pivot_table as create_pivot_table_impl
from excel_mcp.tables import create_excel_table as create_table_impl
from excel_mcp.sheet import (
    copy_sheet,
    delete_sheet,
    rename_sheet,
    merge_range,
    unmerge_range,
)

# Initialize EXCEL_FILES_PATH variable without assigning a value
EXCEL_FILES_PATH = None

# Initialize HOST and PORT variables for SSE mode
HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "8660"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("excel-mcp")
# Initialize FastMCP server
mcp = FastMCP(
    "excel-mcp",
    version="0.1.4",
    description="Excel MCP Server for manipulating Excel files",
    dependencies=["openpyxl>=3.1.2"],
    host=HOST,
    port=PORT,
    env_vars={
        "EXCEL_FILES_PATH": {
            "description": "Path to Excel files directory",
            "required": False,
            "default": EXCEL_FILES_PATH
        },
        "HOST": {
            "description": "Host for SSE server",
            "required": False,
            "default": "localhost"
        },
        "PORT": {
            "description": "Port for SSE server",
            "required": False,
            "default": "8660"
        }
    }
)

def get_excel_path(filename: str) -> str:
    """Get full path to Excel file.
    
    Args:
        filename: Name of Excel file
        
    Returns:
        Full path to Excel file
    """
    # If filename is already an absolute path, return it
    if os.path.isabs(filename):
        return filename

    # Check if in SSE mode (EXCEL_FILES_PATH is not None)
    if EXCEL_FILES_PATH is None:
        # Must use absolute path
        raise ValueError(f"Invalid filename: {filename}, must be an absolute path when not in SSE mode")

    # In SSE mode, if it's a relative path, resolve it based on EXCEL_FILES_PATH
    return os.path.join(EXCEL_FILES_PATH, filename)

@mcp.tool()
def apply_formula(
    filepath: str,
    sheet_name: str,
    cell: str,
    formula: str,
) -> dict[str, Any]:
    """
    Apply Excel formula to cell.
    Excel formula will write to cell with verification.
    """
    try:
        full_path = get_excel_path(filepath)
        # First validate the formula
        validation = validate_formula_impl(full_path, sheet_name, cell, formula)
        if isinstance(validation, dict) and "error" in validation:
            return validation
            
        # If valid, apply the formula
        from excel_mcp.calculations import apply_formula as apply_formula_impl
        return apply_formula_impl(full_path, sheet_name, cell, formula)
    except (ValidationError, CalculationError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error applying formula: {e}")
        raise

@mcp.tool()
def validate_formula_syntax(
    filepath: str,
    sheet_name: str,
    cell: str,
    formula: str,
) -> dict[str, Any]:
    """Validate Excel formula syntax without applying it."""
    try:
        full_path = get_excel_path(filepath)
        return validate_formula_impl(full_path, sheet_name, cell, formula)
    except (ValidationError, CalculationError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error validating formula: {e}")
        raise

@mcp.tool()
def format_range(
    filepath: str,
    sheet_name: str,
    start_cell: str,
    end_cell: str = None,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    font_size: int = None,
    font_color: str = None,
    bg_color: str = None,
    border_style: str = None,
    border_color: str = None,
    number_format: str = None,
    alignment: str = None,
    wrap_text: bool = False,
    merge_cells: bool = False,
    protection: Dict[str, Any] = None,
    conditional_format: Dict[str, Any] = None
) -> dict[str, Any]:
    """Apply formatting to a range of cells."""
    try:
        full_path = get_excel_path(filepath)
        from excel_mcp.formatting import format_range as format_range_func
        
        format_range_func(
            filepath=full_path,
            sheet_name=sheet_name,
            start_cell=start_cell,
            end_cell=end_cell,
            bold=bold,
            italic=italic,
            underline=underline,
            font_size=font_size,
            font_color=font_color,
            bg_color=bg_color,
            border_style=border_style,
            border_color=border_color,
            number_format=number_format,
            alignment=alignment,
            wrap_text=wrap_text,
            merge_cells=merge_cells,
            protection=protection,
            conditional_format=conditional_format
        )
        return {"message": "Range formatted successfully"}
    except (ValidationError, FormattingError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error formatting range: {e}")
        raise

@mcp.tool()
def read_data_from_excel(
    filepath: str,
    sheet_name: str,
    start_cell: str = "A1",
    end_cell: str = None,
    preview_only: bool = False
) -> dict[str, Any]:
    """
    Read data from Excel worksheet with cell metadata including validation rules.
    
    Args:
        filepath: Path to Excel file
        sheet_name: Name of worksheet
        start_cell: Starting cell (default A1)
        end_cell: Ending cell (optional, auto-expands if not provided)
        preview_only: Whether to return preview only
    
    Returns:  
    JSON string containing structured cell data with validation metadata.
    Each cell includes: address, value, row, column, and validation info (if any).
    """
    try:
        full_path = get_excel_path(filepath)
        from excel_mcp.data import read_excel_range_with_metadata
        result = read_excel_range_with_metadata(
            full_path, 
            sheet_name, 
            start_cell, 
            end_cell
        )
        if not result or not result.get("cells"):
            return {"message": "No data found in specified range"}
            
        return result
        
    except Exception as e:
        logger.error(f"Error reading data: {e}")
        raise

@mcp.tool()
def write_data_to_excel(
    filepath: str,
    sheet_name: str,
    data: List[List],
    start_cell: str = "A1",
) -> dict[str, Any]:
    """
    Write data to Excel worksheet.
    Excel formula will write to cell without any verification.

    PARAMETERS:  
    filepath: Path to Excel file
    sheet_name: Name of worksheet to write to
    data: List of lists containing data to write to the worksheet, sublists are assumed to be rows
    start_cell: Cell to start writing to, default is "A1"
  
    """
    try:
        full_path = get_excel_path(filepath)
        return write_data(full_path, sheet_name, data, start_cell)
    except (ValidationError, DataError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error writing data: {e}")
        raise

@mcp.tool()
def create_workbook(filepath: str) -> dict[str, Any]:
    """Create new Excel workbook."""
    try:
        full_path = get_excel_path(filepath)
        from excel_mcp.workbook import create_workbook as create_workbook_impl
        result = create_workbook_impl(full_path)
        if "workbook" in result:
            del result["workbook"]
        return result
    except WorkbookError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error creating workbook: {e}")
        raise

@mcp.tool()
def create_worksheet(filepath: str, sheet_name: str) -> dict[str, Any]:
    """Create new worksheet in workbook."""
    try:
        full_path = get_excel_path(filepath)
        from excel_mcp.workbook import create_sheet as create_worksheet_impl
        return create_worksheet_impl(full_path, sheet_name)
    except (ValidationError, WorkbookError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error creating worksheet: {e}")
        raise

@mcp.tool()
def create_chart(
    filepath: str,
    sheet_name: str,
    data_range: str,
    chart_type: str,
    target_cell: str,
    title: str = "",
    x_axis: str = "",
    y_axis: str = ""
) -> dict[str, Any]:
    """Create chart in worksheet."""
    try:
        full_path = get_excel_path(filepath)
        return create_chart_impl(
            filepath=full_path,
            sheet_name=sheet_name,
            data_range=data_range,
            chart_type=chart_type,
            target_cell=target_cell,
            title=title,
            x_axis=x_axis,
            y_axis=y_axis
        )
    except (ValidationError, ChartError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error creating chart: {e}")
        raise

@mcp.tool()
def create_pivot_table(
    filepath: str,
    sheet_name: str,
    data_range: str,
    rows: List[str],
    values: List[str],
    columns: List[str] = None,
    agg_func: str = "mean"
) -> dict[str, Any]:
    """Create pivot table in worksheet."""
    try:
        full_path = get_excel_path(filepath)
        return create_pivot_table_impl(
            filepath=full_path,
            sheet_name=sheet_name,
            data_range=data_range,
            rows=rows,
            values=values,
            columns=columns or [],
            agg_func=agg_func
        )
    except (ValidationError, PivotError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error creating pivot table: {e}")
        raise

@mcp.tool()
def create_table(
    filepath: str,
    sheet_name: str,
    data_range: str,
    table_name: str = None,
    table_style: str = "TableStyleMedium9"
) -> dict[str, Any]:
    """Creates a native Excel table from a specified range of data."""
    try:
        full_path = get_excel_path(filepath)
        return create_table_impl(
            filepath=full_path,
            sheet_name=sheet_name,
            data_range=data_range,
            table_name=table_name,
            table_style=table_style
        )
    except DataError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        raise

@mcp.tool()
def copy_worksheet(
    filepath: str,
    source_sheet: str,
    target_sheet: str
) -> dict[str, Any]:
    """Copy worksheet within workbook."""
    try:
        full_path = get_excel_path(filepath)
        return copy_sheet(full_path, source_sheet, target_sheet)
    except (ValidationError, SheetError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error copying worksheet: {e}")
        raise

@mcp.tool()
def delete_worksheet(
    filepath: str,
    sheet_name: str
) -> dict[str, Any]:
    """Delete worksheet from workbook."""
    try:
        full_path = get_excel_path(filepath)
        return delete_sheet(full_path, sheet_name)
    except (ValidationError, SheetError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error deleting worksheet: {e}")
        raise

@mcp.tool()
def rename_worksheet(
    filepath: str,
    old_name: str,
    new_name: str
) -> dict[str, Any]:
    """Rename worksheet in workbook."""
    try:
        full_path = get_excel_path(filepath)
        return rename_sheet(full_path, old_name, new_name)
    except (ValidationError, SheetError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error renaming worksheet: {e}")
        raise

@mcp.tool()
def get_workbook_metadata(
    filepath: str,
    include_ranges: bool = False
) -> dict[str, Any]:
    """Get metadata about workbook including sheets, ranges, etc."""
    try:
        full_path = get_excel_path(filepath)
        return get_workbook_info(full_path, include_ranges=include_ranges)
    except WorkbookError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error getting workbook metadata: {e}")
        raise

@mcp.tool()
def merge_cells(filepath: str, sheet_name: str, start_cell: str, end_cell: str) -> dict[str, Any]:
    """Merge a range of cells."""
    try:
        full_path = get_excel_path(filepath)
        return merge_range(full_path, sheet_name, start_cell, end_cell)
    except (ValidationError, SheetError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error merging cells: {e}")
        raise

@mcp.tool()
def unmerge_cells(filepath: str, sheet_name: str, start_cell: str, end_cell: str) -> dict[str, Any]:
    """Unmerge a range of cells."""
    try:
        full_path = get_excel_path(filepath)
        return unmerge_range(full_path, sheet_name, start_cell, end_cell)
    except (ValidationError, SheetError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error unmerging cells: {e}")
        raise

@mcp.tool()
def copy_range(
    filepath: str,
    sheet_name: str,
    source_start: str,
    source_end: str,
    target_start: str,
    target_sheet: str = None
) -> dict[str, Any]:
    """Copy a range of cells to another location."""
    try:
        full_path = get_excel_path(filepath)
        from excel_mcp.sheet import copy_range_operation
        return copy_range_operation(
            full_path,
            sheet_name,
            source_start,
            source_end,
            target_start,
            target_sheet
        )
    except (ValidationError, SheetError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error copying range: {e}")
        raise

@mcp.tool()
def delete_range(
    filepath: str,
    sheet_name: str,
    start_cell: str,
    end_cell: str,
    shift_direction: str = "up"
) -> dict[str, Any]:
    """Delete a range of cells and shift remaining cells."""
    try:
        full_path = get_excel_path(filepath)
        from excel_mcp.sheet import delete_range_operation
        return delete_range_operation(
            full_path,
            sheet_name,
            start_cell,
            end_cell,
            shift_direction
        )
    except (ValidationError, SheetError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error deleting range: {e}")
        raise

@mcp.tool()
def validate_excel_range(
    filepath: str,
    sheet_name: str,
    start_cell: str,
    end_cell: str = None
) -> dict[str, Any]:
    """Validate if a range exists and is properly formatted."""
    try:
        full_path = get_excel_path(filepath)
        range_str = start_cell if not end_cell else f"{start_cell}:{end_cell}"
        return validate_range_impl(full_path, sheet_name, range_str)
    except ValidationError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Error validating range: {e}")
        raise

@mcp.tool()
def get_data_validation_info(
    filepath: str,
    sheet_name: str
) -> dict[str, Any]:
    """
    Get all data validation rules in a worksheet.
    
    This tool helps identify which cell ranges have validation rules
    and what types of validation are applied.
    
    Args:
        filepath: Path to Excel file
        sheet_name: Name of worksheet
        
    Returns:
        JSON string containing all validation rules in the worksheet
    """
    try:
        full_path = get_excel_path(filepath)
        from openpyxl import load_workbook
        from excel_mcp.cell_validation import get_all_validation_ranges
        
        wb = load_workbook(full_path, read_only=False)
        if sheet_name not in wb.sheetnames:
            return {"error": f"Sheet '{sheet_name}' not found"}
            
        ws = wb[sheet_name]
        validations = get_all_validation_ranges(ws)
        wb.close()
        
        if not validations:
            return {"message": "No data validation rules found in this worksheet"}
            
        return {
            "sheet_name": sheet_name,
            "validation_rules": validations
        }
        
    except Exception as e:
        logger.error(f"Error getting validation info: {e}")
        raise

async def run_sse():
    """Run Excel MCP server in SSE mode."""
    # Assign value to EXCEL_FILES_PATH in SSE mode
    global EXCEL_FILES_PATH
    EXCEL_FILES_PATH = os.environ.get("EXCEL_FILES_PATH", "./excel_files")
    # Create directory if it doesn't exist
    os.makedirs(EXCEL_FILES_PATH, exist_ok=True)
    
    try:
        logger.info(f"Starting Excel MCP server with SSE transport")
        logger.info(f"Host: {HOST}, Port: {PORT}")
        logger.info(f"Files directory: {EXCEL_FILES_PATH}")
        await mcp.run_sse_async()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        await mcp.shutdown()
    except Exception as e:
        logger.error(f"Server failed: {e}")
        raise
    finally:
        logger.info("Server shutdown complete")

def run_stdio():
    """Run Excel MCP server in stdio mode."""
    # No need to assign EXCEL_FILES_PATH in stdio mode
    
    try:
        logger.info("Starting Excel MCP server with stdio transport")
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        raise
    finally:
        logger.info("Server shutdown complete")
