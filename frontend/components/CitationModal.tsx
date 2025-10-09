import React from "react";
import { Source } from "./SourceCard";

type Props = {
  citation: Source;
  onClose: () => void;
};

export default function CitationModal({ citation, onClose }: Props) {
  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div 
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-start mb-6">
          <h2 className="text-2xl font-bold text-purple-800 dark:text-purple-300">
            Source Details
          </h2>
          <button 
            onClick={onClose}
            className="text-2xl text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
          >
            ×
          </button>
        </div>

        <div className="space-y-4">
          <div className="bg-purple-50 dark:bg-gray-700 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">📄</span>
              <h3 className="text-lg font-semibold text-purple-800 dark:text-purple-300">
                {citation.filename}
              </h3>
            </div>
            <div className="text-sm text-purple-600 dark:text-purple-400 space-y-1">
              <p><strong>Pages:</strong> {citation.page_start} - {citation.page_end}</p>
              <p><strong>Chunk ID:</strong> {citation.chunk_id}</p>
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
            <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">
              About Citations
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              This citation indicates that the information came from the specified document and page range. 
              The chunk ID helps identify the exact section of the document that was used to generate the response.
            </p>
          </div>

          <button
            onClick={onClose}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-xl transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

