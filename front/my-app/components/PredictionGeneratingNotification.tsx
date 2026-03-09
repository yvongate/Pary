/**
 * PredictionGeneratingNotification - Notification de génération en cours
 */
'use client';

import React from 'react';
import { useRouter } from 'next/navigation';

interface PredictionGeneratingNotificationProps {
  isOpen: boolean;
  onClose: () => void;
  homeTeam: string;
  awayTeam: string;
}

export default function PredictionGeneratingNotification({
  isOpen,
  onClose,
  homeTeam,
  awayTeam
}: PredictionGeneratingNotificationProps) {
  const router = useRouter();

  if (!isOpen) return null;

  const handleViewPredictions = () => {
    onClose();
    router.push('/predictions');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-500 to-green-600 text-white p-6 rounded-t-lg">
          <div className="flex items-center justify-center">
            <div className="bg-white rounded-full p-3">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-center mt-4">✅ Prédiction en cours</h2>
        </div>

        {/* Contenu */}
        <div className="p-6">
          <div className="text-center mb-6">
            <p className="text-lg font-semibold text-gray-800 mb-2">
              {homeTeam} vs {awayTeam}
            </p>
            <p className="text-sm text-gray-600">
              La prédiction sera disponible sur la page{' '}
              <span className="font-semibold text-blue-600">/predictions</span>{' '}
              dans environ <span className="font-semibold">30-60 secondes</span>.
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-800">
              💡 <strong>Astuce :</strong> Vous pouvez fermer cette fenêtre. La génération continue en arrière-plan.
            </p>
          </div>

          {/* Boutons */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 font-medium"
            >
              Fermer
            </button>
            <button
              onClick={handleViewPredictions}
              className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-semibold"
            >
              Voir /predictions
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
