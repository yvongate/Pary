/**
 * PredictionCard - Carte d'affichage d'une prédiction
 */
import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prediction } from '../lib/api';

interface PredictionCardProps {
  prediction: Prediction;
  onClick?: () => void;
}

export default function PredictionCard({ prediction, onClick }: PredictionCardProps) {
  const matchDate = new Date(prediction.match_date);
  const isUpcoming = matchDate > new Date();

  return (
    <div
      className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer border border-gray-200"
      onClick={onClick}
    >
      {/* En-tête du match */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs font-semibold text-gray-500 uppercase">
            {prediction.league_code}
          </span>
          <span className="text-xs text-gray-500">
            {matchDate.toLocaleDateString('fr-FR', {
              day: '2-digit',
              month: 'short',
              hour: '2-digit',
              minute: '2-digit'
            })}
          </span>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-between">
            <div className="flex-1 text-right">
              <p className="font-bold text-lg text-gray-800">{prediction.home_team}</p>
              {prediction.formations && (
                <p className="text-xs text-gray-500">{prediction.formations.home}</p>
              )}
            </div>

            <div className="px-4 py-2">
              <span className="text-2xl font-bold text-gray-400">VS</span>
            </div>

            <div className="flex-1 text-left">
              <p className="font-bold text-lg text-gray-800">{prediction.away_team}</p>
              {prediction.formations && (
                <p className="text-xs text-gray-500">{prediction.formations.away}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Prédictions TIRS */}
      <div className="mb-4 bg-blue-50 rounded-lg p-4">
        <div className="flex items-center mb-2">
          <span className="text-2xl mr-2">🎯</span>
          <h3 className="font-bold text-blue-900">TIRS</h3>
        </div>

        <div className="space-y-2 text-sm">
          {/* Par équipe */}
          {prediction.shots.home_team_message && (
            <div className="text-gray-700 font-medium">
              {prediction.shots.home_team_message}
            </div>
          )}
          {prediction.shots.away_team_message && (
            <div className="text-gray-700 font-medium">
              {prediction.shots.away_team_message}
            </div>
          )}

          {/* Total */}
          <div className="pt-2 border-t border-blue-200 space-y-1">
            <div className="flex justify-between">
              <span className="text-gray-700">{prediction.shots.message_min}</span>
              <span className="font-semibold text-green-600">{prediction.shots.min}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">{prediction.shots.message_max}</span>
              <span className="font-semibold text-red-600">{prediction.shots.max}</span>
            </div>
          </div>

          <div className="mt-2 pt-2 border-t border-blue-200">
            <span className="text-xs text-gray-600">
              Confiance: <span className="font-semibold text-blue-700">
                {(prediction.shots.confidence * 100).toFixed(0)}%
              </span>
            </span>
          </div>
        </div>

      </div>

      {/* Prédictions CORNERS */}
      <div className="bg-green-50 rounded-lg p-4 mb-4">
        <div className="flex items-center mb-2">
          <span className="text-2xl mr-2">⚽</span>
          <h3 className="font-bold text-green-900">CORNERS</h3>
        </div>

        <div className="space-y-2 text-sm">
          {/* Par équipe */}
          {prediction.corners.home_team_message && (
            <div className="text-gray-700 font-medium">
              {prediction.corners.home_team_message}
            </div>
          )}
          {prediction.corners.away_team_message && (
            <div className="text-gray-700 font-medium">
              {prediction.corners.away_team_message}
            </div>
          )}

          {/* Total */}
          <div className="pt-2 border-t border-green-200 space-y-1">
            <div className="flex justify-between">
              <span className="text-gray-700">{prediction.corners.message_min}</span>
              <span className="font-semibold text-green-600">{prediction.corners.min}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700">{prediction.corners.message_max}</span>
              <span className="font-semibold text-red-600">{prediction.corners.max}</span>
            </div>
          </div>

          <div className="mt-2 pt-2 border-t border-green-200">
            <span className="text-xs text-gray-600">
              Confiance: <span className="font-semibold text-green-700">
                {(prediction.corners.confidence * 100).toFixed(0)}%
              </span>
            </span>
          </div>
        </div>

      </div>

      {/* Analyse IA Deep Reasoning (affichée UNE SEULE fois) */}
      {prediction.ai_reasoning && (
        <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-purple-500">
          <div className="flex items-center mb-2">
            <span className="text-xl mr-2">🤖</span>
            <h3 className="font-bold text-purple-900">ANALYSE IA</h3>
          </div>
          <div className="prose prose-sm max-w-none text-gray-700">
            <ReactMarkdown>{prediction.ai_reasoning}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
