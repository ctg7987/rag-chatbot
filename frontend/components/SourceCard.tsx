import React from "react";

export type Source = { filename: string; page_start: number; page_end: number; chunk_id: string };
type Props = { 
  source: Source;
  darkMode?: boolean;
};

export default function SourceCard({ source, darkMode = false }: Props) {
  const { filename, page_start, page_end } = source;
  
  const cardClass = darkMode
    ? "bg-gray-700 text-gray-200 border border-gray-600"
    : "bg-purple-100 text-purple-800 border border-purple-300";
  
  return (
    <span className={`${cardClass} rounded-lg px-3 py-2 text-sm font-medium shadow-sm cursor-pointer hover:opacity-80 transition-opacity`}>
      📄 {filename} (p{page_start}-{page_end})
    </span>
  );
}
