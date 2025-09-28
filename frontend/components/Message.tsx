import React from "react";
type Props = { role: "user" | "assistant"; content: string };
export default function Message({ role, content }: Props) {
  return (
    <div className={`p-4 rounded-xl mb-4 ${
      role === "user" 
        ? "bg-purple-600 text-white ml-8" 
        : "bg-white text-purple-800 mr-8 border-2 border-purple-200"
    }`}>
      <div className="text-sm font-semibold mb-2 opacity-80">
        {role === "user" ? "You" : "Assistant"}
      </div>
      <div className="whitespace-pre-wrap text-lg leading-relaxed">{content}</div>
    </div>
  );
}
