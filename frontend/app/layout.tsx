import "./globals.css";
import React from "react";
export const metadata = {
  title: "RAG Chatbot",
  description: "RAG Chatbot UI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
