import * as XLSX from "xlsx";

export interface TeamCostRow {
  team: string;
  code: string | null;
  cost: number;
}

/**
 * Exports a Team/LOB Code/Cost breakdown as a real .xlsx file, triggering
 * a browser download. Used by both Mobitel and Dialog Data Bucket bill
 * summary pages — same table shape in both, so one shared implementation.
 */
export function exportTeamCostToExcel(rows: TeamCostRow[], grandTotal: number, filename: string) {
  const data: (string | number)[][] = [
    ["Team", "LOB Code", "Cost"],
    ...rows.map((r) => [r.team, r.code ?? "", Number(r.cost.toFixed(2))]),
    ["Grand Total", "", Number(grandTotal.toFixed(2))],
  ];

  const worksheet = XLSX.utils.aoa_to_sheet(data);
  worksheet["!cols"] = [{ wch: 28 }, { wch: 12 }, { wch: 14 }];

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Team Cost");

  XLSX.writeFile(workbook, filename);
}