"""
Data ingestion module for the Energy Transition Model.

Handles reading ODS (OpenDocument Spreadsheet) files from LibreOffice Calc.
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Any, Dict
import pandas as pd

from .temporal import extraire_mois, extraire_plage


# ODF namespaces
ODF_NAMESPACES = {
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
}


def get_cell_value(cell: ET.Element) -> Optional[Any]:
    """
    Extract the numeric or text value from an ODS cell.

    Args:
        cell: XML element representing a table cell

    Returns:
        Float value, string value, or None if empty
    """
    # Try numeric value first
    value = cell.get('{urn:oasis:names:tc:opendocument:xmlns:office:1.0}value')
    if value:
        try:
            return float(value)
        except ValueError:
            pass

    # Fall back to text content
    text_elem = cell.find('.//text:p', ODF_NAMESPACES)
    if text_elem is not None and text_elem.text:
        return text_elem.text

    return None


def expand_row(row: ET.Element, max_cols: int = 25) -> List[Any]:
    """
    Expand repeated cells in an ODS row.

    ODS format uses number-columns-repeated to compress repeated cells.
    This function expands them into a flat list.

    Args:
        row: XML element representing a table row
        max_cols: Maximum number of columns to extract

    Returns:
        List of cell values
    """
    cells = []
    for cell in row.findall('table:table-cell', ODF_NAMESPACES):
        repeat = cell.get(
            '{urn:oasis:names:tc:opendocument:xmlns:table:1.0}number-columns-repeated'
        )
        repeat = int(repeat) if repeat else 1
        repeat = min(repeat, max_cols - len(cells))

        value = get_cell_value(cell)
        for _ in range(repeat):
            cells.append(value)
            if len(cells) >= max_cols:
                break
        if len(cells) >= max_cols:
            break

    return cells


def load_ods_sheet(
    ods_path: Path,
    sheet_name: str,
    row_range: tuple = (3, 65),
    columns: Optional[Dict[str, int]] = None
) -> pd.DataFrame:
    """
    Load data from a specific sheet in an ODS file.

    Args:
        ods_path: Path to the ODS file
        sheet_name: Name (or partial name) of the sheet to load
        row_range: Tuple of (start_row, end_row) to extract (0-indexed)
        columns: Dict mapping column names to column indices

    Returns:
        DataFrame with extracted data

    Raises:
        FileNotFoundError: If ODS file doesn't exist
        ValueError: If sheet not found or no data extracted
    """
    if not ods_path.exists():
        raise FileNotFoundError(f"ODS file not found: {ods_path}")

    # Default column mapping for the energy model sheet
    if columns is None:
        columns = {
            'Periode': 0,       # A: Period (month + time slot)
            'Production_kW': 7,  # H: Total production
            'Consommation_kW': 15,  # P: Total consumption
            'Deficit_kW': 16,   # Q: Deficit/gas need
            'Duree_h': 17,      # R: Time slot duration
            'Energie_TWh_ODS': 18,  # S: Energy (TWh)
        }

    # Read ODS file (it's a ZIP containing XML)
    with zipfile.ZipFile(ods_path, 'r') as z:
        content = z.read('content.xml')

    root = ET.fromstring(content)
    body = root.find('.//office:spreadsheet', ODF_NAMESPACES)
    if body is None:
        raise ValueError("No spreadsheet content found in ODS file")

    tables = body.findall('table:table', ODF_NAMESPACES)

    # Find the target sheet
    target_sheet = None
    for table in tables:
        name = table.get('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}name')
        if name and sheet_name in name:
            target_sheet = table
            break

    if target_sheet is None:
        available = [
            t.get('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}name')
            for t in tables
        ]
        raise ValueError(
            f"Sheet '{sheet_name}' not found. Available: {available}"
        )

    # Extract rows
    rows = list(target_sheet.findall('table:table-row', ODF_NAMESPACES))
    start_row, end_row = row_range

    data = []
    max_col_idx = max(columns.values()) + 1

    for row_idx in range(start_row, min(end_row, len(rows))):
        cells = expand_row(rows[row_idx], max_cols=max_col_idx)

        if len(cells) > max(columns.values()) and cells[columns['Periode']]:
            row_data = {}
            for col_name, col_idx in columns.items():
                value = cells[col_idx] if col_idx < len(cells) else None
                row_data[col_name] = value

            # Only include rows with valid numeric production/consumption
            prod = row_data.get('Production_kW')
            conso = row_data.get('Consommation_kW')
            if isinstance(prod, (int, float)) and isinstance(conso, (int, float)):
                # Clean up missing values
                for key in ['Deficit_kW', 'Duree_h', 'Energie_TWh_ODS']:
                    if not isinstance(row_data.get(key), (int, float)):
                        row_data[key] = 0
                data.append(row_data)

    if not data:
        raise ValueError(f"No valid data extracted from sheet '{sheet_name}'")

    df = pd.DataFrame(data)
    return df


def load_energy_model_data(ods_path: Path) -> pd.DataFrame:
    """
    Load the energy model data from the standard ODS file.

    This is a convenience function that loads the "moulinette simplifiée avec PAC"
    sheet with the standard column mapping and adds derived columns.

    Args:
        ods_path: Path to "modélisation générale.ods"

    Returns:
        DataFrame with columns:
        - Periode, Production_kW, Consommation_kW, Deficit_kW, Duree_h, Energie_TWh_ODS
        - Mois (extracted month name)
        - Plage (extracted time slot)
    """
    df = load_ods_sheet(
        ods_path,
        sheet_name='moulinette simplifiée avec PAC',
        row_range=(3, 65)
    )

    # Add derived columns
    df['Mois'] = df['Periode'].apply(extraire_mois)
    df['Plage'] = df['Periode'].apply(extraire_plage)

    return df
