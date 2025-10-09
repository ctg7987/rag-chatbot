import React from "react";

type Session = {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

type Props = {
  sessions: Session[];
  currentSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onClose: () => void;
  darkMode: boolean;
};

export default function SessionList({ 
  sessions, 
  currentSessionId, 
  onSelectSession, 
  onDeleteSession, 
  onClose,
  darkMode 
}: Props) {
  const bgClass = darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-purple-200";
  const textClass = darkMode ? "text-gray-100" : "text-purple-800";
  const hoverClass = darkMode ? "hover:bg-gray-700" : "hover:bg-purple-50";
  const activeClass = darkMode ? "bg-gray-700 border-purple-500" : "bg-purple-100 border-purple-500";

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center" onClick={onClose}>
      <div 
        className={`${bgClass} rounded-2xl shadow-2xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto border-2`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-6">
          <h2 className={`text-2xl font-bold ${textClass}`}>Conversation History</h2>
          <button 
            onClick={onClose}
            className={`text-2xl ${textClass} hover:opacity-70`}
          >
            ×
          </button>
        </div>

        {sessions.length === 0 ? (
          <div className={`text-center py-8 ${darkMode ? 'text-gray-400' : 'text-purple-600'}`}>
            No conversations yet. Start chatting to create your first session!
          </div>
        ) : (
          <div className="space-y-2">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  currentSessionId === session.session_id 
                    ? activeClass 
                    : `border-transparent ${hoverClass}`
                }`}
              >
                <div className="flex justify-between items-start">
                  <div 
                    className="flex-1"
                    onClick={() => onSelectSession(session.session_id)}
                  >
                    <h3 className={`font-semibold ${textClass} mb-1`}>
                      {session.title}
                    </h3>
                    <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-purple-500'}`}>
                      {new Date(session.updated_at).toLocaleString()}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm('Delete this conversation?')) {
                        onDeleteSession(session.session_id);
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

