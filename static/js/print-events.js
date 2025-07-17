function printEvent(button) {
  const eventGroup = button.nextElementSibling;
  const header = document.querySelector("header").cloneNode(true);
  const printableContent = document.createElement("div");

  printableContent.appendChild(header);
  printableContent.appendChild(eventGroup.cloneNode(true));

  // Create a new window for printing
  const printWindow = window.open("", "_blank");
  printWindow.document.write("<html><head><title>Print Event</title>");
  printWindow.document.write(
    '<link rel="stylesheet" href="/static/css/styles.css">',
  );
  printWindow.document.write(
    '<link rel="stylesheet" href="/static/css/results.css">',
  );
  printWindow.document.write("</head><body>");
  printWindow.document.write(printableContent.innerHTML);
  printWindow.document.write("</body></html>");
  printWindow.document.close();
  printWindow.focus();

  // Wait for CSS to load then print
  setTimeout(() => {
    printWindow.print();
    printWindow.close();
  }, 250);
}
