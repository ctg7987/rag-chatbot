import React from "react";
type Props = { role: "user" | "assistant"; content: string };
export default function Message({ role, content }: Props) {
  return (
    <div>
      <div className="text-xs text-gray-500">{role}</div>
      <div className="whitespace-pre-wrap">{content}</div>
    </div>
  );
}
