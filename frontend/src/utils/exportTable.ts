import * as XLSX from "xlsx";

/**
 * Exports any headers+rows table as a real .xlsx file, triggering a
 * browser download. Generic so it works for any table shape — Team Cost
 * breakdowns, itemized bill details, per-employee summaries, etc.
 */
export function exportTableToExcel(headers: string[], rows: (string | number)[][], filename: string, sheetName = "Sheet1") {
  const data: (string | number)[][] = [headers, ...rows];

  const worksheet = XLSX.utils.aoa_to_sheet(data);
  worksheet["!cols"] = headers.map(() => ({ wch: 22 }));

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);

  XLSX.writeFile(workbook, filename);
}