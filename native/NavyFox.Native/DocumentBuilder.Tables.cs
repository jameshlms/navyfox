using DocumentFormat.OpenXml.Wordprocessing;

namespace NavyFox.Native;

internal static partial class DocumentBuilder
{
    // Build an empty table with the given dimensions and default borders.
    // Returns the new Table and populates cells[,].
    private static Table BuildTable(int rows, int cols, out TableCell[,] cells)
    {
        var table = new Table();

        table.AppendChild(new TableProperties(
            new TableBorders(
                new TopBorder    { Val = BorderValues.Single, Size = 4 },
                new BottomBorder { Val = BorderValues.Single, Size = 4 },
                new LeftBorder   { Val = BorderValues.Single, Size = 4 },
                new RightBorder  { Val = BorderValues.Single, Size = 4 },
                new InsideHorizontalBorder { Val = BorderValues.Single, Size = 4 },
                new InsideVerticalBorder   { Val = BorderValues.Single, Size = 4 })));

        var grid = new TableGrid();
        for (var c = 0; c < cols; c++)
            grid.AppendChild(new GridColumn());
        table.AppendChild(grid);

        cells = new TableCell[rows, cols];
        for (var r = 0; r < rows; r++)
        {
            var row = new TableRow();
            for (var c = 0; c < cols; c++)
            {
                var cell = new TableCell(
                    new Paragraph(new Run(new Text(string.Empty))));
                cells[r, c] = cell;
                row.AppendChild(cell);
            }
            table.AppendChild(row);
        }

        return table;
    }
}
