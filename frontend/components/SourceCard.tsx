import React from "react";
export type Source = { filename: string; page_start: number; page_end: number; chunk_id: string };
type Props = { source: Source };
export default function SourceCard({ source }: Props) {
  const { filename, page_start, page_end } = source;
  return (
    <span className="bg-purple-100 text-purple-800 border border-purple-300 rounded-lg px-3 py-2 text-sm font-medium shadow-sm">
      📄 {filename} (p{page_start}-{page_end})
    </span>
  );
}
