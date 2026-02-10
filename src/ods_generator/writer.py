"""ODS writer with cross-sheet formula support.

Uses odfpy to create OpenDocument Spreadsheet files where every numeric
cell in the synthesis sheet is a formula referencing source data sheets.
Pre-computed values are set alongside formulas so numbers display immediately.
"""

from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableRow, TableCell
from odf.text import P

from .formatting import create_styles


class ODSWriter:
    """ODS spreadsheet writer with formula and cross-sheet reference support."""

    def __init__(self):
        self.doc = OpenDocumentSpreadsheet()
        self.styles = create_styles(self.doc)
        self.sheets = {}

    def add_data_sheet(self, name: str, headers: list, rows: list, title: str = None) -> Table:
        """Add a data sheet with static values.

        Args:
            name: Sheet name
            headers: List of column header strings
            rows: List of row tuples/lists (each matching headers length)
            title: Optional title row above headers

        Returns:
            The created Table object
        """
        table = Table(name=name)

        # Optional title row
        if title:
            tr = TableRow()
            tc = TableCell(stylename=self.styles.get('title', None))
            tc.setAttrNS(
                'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
                'number-columns-spanned', str(len(headers))
            )
            tc.addElement(P(text=title))
            tr.addElement(tc)
            table.addElement(tr)

        # Header row
        tr = TableRow()
        for h in headers:
            tc = TableCell(stylename=self.styles.get('header', None))
            tc.addElement(P(text=str(h)))
            tr.addElement(tc)
        table.addElement(tr)

        # Data rows
        for row in rows:
            tr = TableRow()
            for val in row:
                tc = self._make_value_cell(val)
                tr.addElement(tc)
            table.addElement(tr)

        self.doc.spreadsheet.addElement(table)
        self.sheets[name] = table
        return table

    def add_formula_sheet(self, name: str, headers: list, title: str = None) -> Table:
        """Create an empty sheet ready for formula rows.

        Args:
            name: Sheet name
            headers: Column headers
            title: Optional title

        Returns:
            The created Table object (add rows with add_formula_row)
        """
        table = Table(name=name)

        if title:
            tr = TableRow()
            tc = TableCell(stylename=self.styles.get('title', None))
            tc.setAttrNS(
                'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
                'number-columns-spanned', str(len(headers))
            )
            tc.addElement(P(text=title))
            tr.addElement(tc)
            table.addElement(tr)

        tr = TableRow()
        for h in headers:
            tc = TableCell(stylename=self.styles.get('header', None))
            tc.addElement(P(text=str(h)))
            tr.addElement(tc)
        table.addElement(tr)

        self.doc.spreadsheet.addElement(table)
        self.sheets[name] = table
        return table

    def add_formula_row(self, table: Table, cells: list):
        """Add a row with formula and/or value cells.

        Args:
            table: Target Table object
            cells: List of dicts, each with:
                - 'value': The pre-computed value (number or string)
                - 'formula': Optional ODF formula string (e.g., "of:=[sheet.C5]*1000")
                - 'style': Optional style name override
        """
        tr = TableRow()
        for cell in cells:
            value = cell.get('value')
            formula = cell.get('formula')
            style_name = cell.get('style')

            if formula:
                style = self.styles.get(style_name or 'formula', None)
            elif isinstance(value, (int, float)):
                style = self.styles.get(style_name or 'number', None)
            else:
                style = self.styles.get(style_name or 'text', None)

            tc = self._write_cell(value, formula, style)
            tr.addElement(tc)
        table.addElement(tr)

    def _write_cell(self, value, formula=None, style=None):
        """Create a TableCell with optional formula and pre-computed value.

        For formula cells, both the formula attribute and the pre-computed
        value are set, so numbers display without needing recalculation.

        ODF formula syntax:
        - Cross-sheet: of:=[sheet_name.C5]
        - In-sheet: of:=[.B5]+[.C5]
        - Functions: of:=MAX(0,[.N5]-[.H5])
        """
        attrs = {}
        if style:
            attrs['stylename'] = style

        if formula:
            attrs['formula'] = formula

        if isinstance(value, (int, float)):
            attrs['valuetype'] = 'float'
            attrs['value'] = str(value)
            tc = TableCell(**attrs)
            tc.addElement(P(text=f"{value:.2f}" if isinstance(value, float) else str(value)))
        elif value is not None:
            attrs['valuetype'] = 'string'
            tc = TableCell(**attrs)
            tc.addElement(P(text=str(value)))
        else:
            tc = TableCell(**attrs)

        return tc

    def _make_value_cell(self, value, style_name=None):
        """Create a simple value cell (no formula)."""
        if isinstance(value, (int, float)):
            style = self.styles.get(style_name or 'number', None)
            tc = TableCell(
                valuetype='float',
                value=str(value),
                stylename=style,
            )
            tc.addElement(P(text=f"{value:.2f}" if isinstance(value, float) else str(value)))
        else:
            style = self.styles.get(style_name or 'text', None)
            tc = TableCell(valuetype='string', stylename=style)
            tc.addElement(P(text=str(value) if value is not None else ""))
        return tc

    def save(self, path: str):
        """Save the ODS document.

        Args:
            path: Output file path (e.g., "output/modele_transition.ods")
        """
        from pathlib import Path as P
        P(path).parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(path)
