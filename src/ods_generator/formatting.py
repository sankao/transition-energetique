"""ODS formatting styles for the energy model spreadsheet."""

from odf.style import Style, TextProperties, TableCellProperties, ParagraphProperties
from odf.number import NumberStyle, Number, Text


def create_styles(doc):
    """Create and register all styles in the ODS document.

    Returns dict of style name -> Style object.
    """
    styles = {}

    # Header style: bold, centered, blue background
    header = Style(name="header", family="table-cell")
    header.addElement(TextProperties(fontweight="bold", color="#FFFFFF"))
    header.addElement(TableCellProperties(backgroundcolor="#4472C4", padding="0.05in"))
    header.addElement(ParagraphProperties(textalign="center"))
    doc.automaticstyles.addElement(header)
    styles['header'] = header

    # Number style: right-aligned, 2 decimals
    number = Style(name="number", family="table-cell")
    number.addElement(ParagraphProperties(textalign="end"))
    doc.automaticstyles.addElement(number)
    styles['number'] = number

    # Formula style: light blue background to indicate computed cells
    formula = Style(name="formula", family="table-cell")
    formula.addElement(TableCellProperties(backgroundcolor="#DAEEF3"))
    formula.addElement(ParagraphProperties(textalign="end"))
    doc.automaticstyles.addElement(formula)
    styles['formula'] = formula

    # Text style: left-aligned
    text = Style(name="text", family="table-cell")
    text.addElement(ParagraphProperties(textalign="start"))
    doc.automaticstyles.addElement(text)
    styles['text'] = text

    # Energy style: right-aligned for GW/TWh values
    energy = Style(name="energy", family="table-cell")
    energy.addElement(ParagraphProperties(textalign="end"))
    doc.automaticstyles.addElement(energy)
    styles['energy'] = energy

    # Title style: bold, larger
    title = Style(name="title", family="table-cell")
    title.addElement(TextProperties(fontweight="bold", fontsize="14pt"))
    title.addElement(TableCellProperties(backgroundcolor="#002060", padding="0.08in"))
    title.addElement(ParagraphProperties(textalign="center"))
    doc.automaticstyles.addElement(title)
    styles['title'] = title

    # Total row style
    total = Style(name="total", family="table-cell")
    total.addElement(TextProperties(fontweight="bold"))
    total.addElement(TableCellProperties(backgroundcolor="#D9E2F3"))
    total.addElement(ParagraphProperties(textalign="end"))
    doc.automaticstyles.addElement(total)
    styles['total'] = total

    # Category row style: bold, green-grey background (parameter grouping)
    category = Style(name="category", family="table-cell")
    category.addElement(TextProperties(fontweight="bold", color="#1F4E3D"))
    category.addElement(TableCellProperties(backgroundcolor="#E2EFDA", padding="0.05in"))
    category.addElement(ParagraphProperties(textalign="start"))
    doc.automaticstyles.addElement(category)
    styles['category'] = category

    return styles
