import React from "react";

type Document = {
  doc_id: string;
  filename: string;
  file_size: number;
  file_type: string;
  chunks_count: number;
  status: string;
  uploaded_at: string;
};

type Props = {
  documents: Document[];
  onDeleteDocument: (docId: string) => void;
  onClose: () => void;
  darkMode: boolean;
};

export default function DocumentList({ documents, onDeleteDocument, onClose, darkMode }: Props) {
  const bgClass = darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-purple-200";
  const textClass = darkMode ? "text-gray-100" : "text-purple-800";
  const hoverClass = darkMode ? "hover:bg-gray-700" : "hover:bg-purple-50";

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return darkMode ? 'text-green-400' : 'text-green-600';
      case 'processing': return darkMode ? 'text-yellow-400' : 'text-yellow-600';
      case 'failed': return darkMode ? 'text-red-400' : 'text-red-600';
      default: return darkMode ? 'text-gray-400' : 'text-gray-600';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center" onClick={onClose}>
      <div 
        className={`${bgClass} rounded-2xl shadow-2xl p-6 max-w-3xl w-full max-h-[80vh] overflow-y-auto border-2`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-6">
          <h2 className={`text-2xl font-bold ${textClass}`}>Document Library</h2>
          <button 
            onClick={onClose}
            className={`text-2xl ${textClass} hover:opacity-70`}
          >
            ×
          </button>
        </div>

        {documents.length === 0 ? (
          <div className={`text-center py-8 ${darkMode ? 'text-gray-400' : 'text-purple-600'}`}>
            No documents uploaded yet. Upload some documents to get started!
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.doc_id}
                className={`p-4 rounded-lg border-2 border-transparent ${hoverClass} transition-all`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">
                        {doc.file_type === '.pdf' ? '📄' : 
                         doc.file_type === '.txt' ? '📝' : 
                         doc.file_type === '.md' ? '📋' : '📎'}
                      </span>
                      <h3 className={`font-semibold ${textClass}`}>
                        {doc.filename}
                      </h3>
                    </div>
                    <div className={`text-sm space-y-1 ${darkMode ? 'text-gray-400' : 'text-purple-600'}`}>
                      <p>Size: {formatFileSize(doc.file_size)}</p>
                      <p>Chunks: {doc.chunks_count}</p>
                      <p>Uploaded: {new Date(doc.uploaded_at).toLocaleString()}</p>
                      <p className={getStatusColor(doc.status)}>
                        Status: {doc.status}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      if (confirm(`Delete ${doc.filename}?`)) {
                        onDeleteDocument(doc.doc_id);
                      }
                    }}
                    className={`ml-4 px-3 py-1 rounded ${darkMode ? 'bg-red-900 hover:bg-red-800' : 'bg-red-100 hover:bg-red-200'} text-red-600 text-sm transition-colors`}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

