import React from "react";

type Props = { 
  role: "user" | "assistant"; 
  content: string;
  darkMode?: boolean;
};

export default function Message({ role, content, darkMode = false }: Props) {
  const userClass = darkMode
    ? "bg-purple-700 text-white ml-8"
    : "bg-purple-600 text-white ml-8";
  
  const assistantClass = darkMode
    ? "bg-gray-700 text-gray-100 mr-8 border-2 border-gray-600"
    : "bg-white text-purple-800 mr-8 border-2 border-purple-200";

  return (
    <div className={`p-4 rounded-xl mb-4 ${
      role === "user" ? userClass : assistantClass
    }`}>
      <div className="text-sm font-semibold mb-2 opacity-80">
        {role === "user" ? "You" : "Assistant"}
      </div>
      <div className="whitespace-pre-wrap text-lg leading-relaxed">{content}</div>
    </div>
  );
}
