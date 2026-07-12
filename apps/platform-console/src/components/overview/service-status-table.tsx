"use client";

import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import type { PlatformServiceHealth } from "@/contracts/types/platform-health";
import { Badge } from "@/components/ui/badge";
import { mapServiceStatus } from "@/lib/status/map-service-status";

const columnHelper = createColumnHelper<PlatformServiceHealth>();

const columns = [
  columnHelper.accessor("name", {
    header: "Service",
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor("status", {
    header: "Status",
    cell: (info) => {
      const presentation = mapServiceStatus(info.getValue());
      return <Badge tone={presentation.tone}>{presentation.label}</Badge>;
    },
  }),
  columnHelper.accessor("version", {
    header: "Version",
    cell: (info) => (
      <span className="font-[family-name:var(--font-mono)] text-xs">
        {info.getValue() ?? "n/a"}
      </span>
    ),
  }),
  columnHelper.accessor("message", {
    header: "Message",
    cell: (info) => (
      <span className="text-[color:var(--muted-fg)]">{info.getValue()}</span>
    ),
  }),
];

export function ServiceStatusTable({
  services,
}: {
  services: PlatformServiceHealth[];
}) {
  // TD-UI-001: useReactTable trips react-hooks/incompatible-library under React
  // Compiler. Accepted low-severity debt; revisit when Compiler support stabilizes.
  const table = useReactTable({
    data: services,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div
      className="overflow-x-auto rounded-sm border border-[color:var(--border)] bg-[color:var(--surface)]"
      data-testid="overview-status-table"
    >
      <table className="min-w-full border-collapse text-left text-sm">
        <thead className="bg-[color:var(--surface-muted)] text-xs tracking-[0.08em] text-[color:var(--muted-fg)] uppercase">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id} className="px-3 py-2 font-medium">
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext(),
                      )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              className="border-t border-[color:var(--border)]"
              data-status={row.original.status}
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-3 py-2 align-top">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
