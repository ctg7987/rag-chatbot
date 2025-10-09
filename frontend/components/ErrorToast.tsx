import React, { useEffect } from "react";

type Props = {
  message: string;
  onClose: () => void;
  duration?: number;
};

export default function ErrorToast({ message, onClose, duration = 5000 }: Props) {
  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in">
      <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded-lg shadow-lg max-w-md">
        <div className="flex justify-between items-start">
          <div className="flex items-start">
            <span className="text-xl mr-2">⚠️</span>
            <p className="font-medium">{message}</p>
          </div>
          <button 
            onClick={onClose}
            className="ml-4 text-red-700 hover:text-red-900 font-bold"
          >
            ×
          </button>
        </div>
      </div>
    </div>
  );
}

