import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

/**
 * Export the P&ID view to a PDF. This renders the element with the given id
 * using html2canvas and embeds the result into a jsPDF document sized for A3.
 *
 * @param filename - Name of the downloaded PDF file
 * @param elementId - DOM element id that contains the SVG and overlays
 * @param version - Version string to stamp on the document
 */
export async function exportPid(
  filename: string,
  elementId = 'pid-container',
  version = ''
): Promise<void> {
  const element = document.getElementById(elementId);
  if (!element) return;

  const canvas = await html2canvas(element, { scale: 2 });
  const imgData = canvas.toDataURL('image/png');

  const orientation = canvas.width > canvas.height ? 'landscape' : 'portrait';
  const pdf = new jsPDF({ orientation, unit: 'px', format: 'a3' });
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();

  pdf.addImage(imgData, 'PNG', 0, 0, pageWidth, pageHeight);
  if (version) {
    pdf.setFontSize(10);
    pdf.text(version, 10, pageHeight - 10);
  }
  pdf.save(filename);
}
