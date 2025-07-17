function printEvent(button) {
  const eventGroup = button.nextElementSibling;
  const eventTitle = eventGroup.querySelector("h3").textContent;

  // Create a printable HTML structure
  const printableHTML = `
        <html>
        <head>
            <title>Printed Event - ${eventTitle}</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    font-size: 9px;
                }
                h1 {
                    font-size: 14px;
                    color: #000;
                    margin-bottom: 20px;
                    text-align: center;
                }
                h3 {
                    font-size: 12px;
                    margin: 15px 0 10px 0;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 9px;
                    page-break-inside: avoid;
                }
                th, td {
                    border: 1px solid #000;
                    padding: 4px 6px;
                    text-align: left;
                }
                th {
                    background-color: #f9f9f9;
                    font-weight: bold;
                }
                .event-group {
                    page-break-inside: avoid;
                }
                @media print {
                    @page {
                        size: auto;
                        margin: 10mm 5mm 10mm 5mm;
                    }
                }
            </style>
        </head>
        <body>
            <h1>Indore District Swimming Association</h1>
            <h3>${eventTitle}</h3>
            ${eventGroup.querySelector("table").outerHTML}
        </body>
        </html>
    `;

  // Open and print
  const printWindow = window.open("", "_blank", "height=600,width=800");
  printWindow.document.open();
  printWindow.document.write(printableHTML);
  printWindow.document.close();

  // Add delay and print
  setTimeout(() => {
    printWindow.print();
    printWindow.close();
  }, 500);
}
