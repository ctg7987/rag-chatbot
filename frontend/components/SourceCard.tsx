import React from "react";
export type Source = { filename: string; page_start: number; page_end: number; chunk_id: string };
type Props = { source: Source };
export default function SourceCard({ source }: Props) {
  const { filename, page_start, page_end } = source;
  return (
    <span className="border rounded px-2 py-1 text-xs bg-gray-50">
      {filename} p{page_start}-{page_end}
    </span>
  );
}
